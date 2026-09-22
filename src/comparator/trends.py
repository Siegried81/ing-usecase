"""Bridge to Dan's Google Trends benchmark - search interest as CONTEXT.

steph 16/09, new module. trends-benchmark/ measures weekly Google search
interest per bank per product in Belgium. This module joins that to the
campaign dataset so a bank profile can carry the market attention around its
product, and degrades to nothing when the exports are absent.

WHAT THIS IS NOT, and the reason this docstring leads with it.

Every deliverable in this project says we have no performance data (PRD 5.2,
plan risk P-08, D-09). Search interest is NOT performance data and joining it
here does not change that sentence. Three reasons, all of which have to survive
into the deck:

  * It measures what people searched for, not what any campaign achieved. Dan's
    own handoff doc is explicit that the pipeline "ne collecte aucune donnée
    publicitaire".
  * The pages we captured are today's pages. A movement in 2023 was driven by a
    campaign we never saw. Joining a 2026 page to a 2023 movement and calling it
    an effect would be the single most embarrassing error available to us.
  * Coverage was ING, KBC and CBC only for most of this project's life. Dan's
    second wave (21/09) resolved a search term for every remaining bank, so all
    14 now share one scale - but six of them sit below the measurable floor (see
    MEASURABLE_PEAK_FLOOR), which is a different kind of thin than "missing".

So: context for the narrative, never a dependent variable, and never a claim
that a page caused a number. `interest_context()` returns descriptive levels,
and nothing in this module correlates a page feature with a search value.

CBC is KBC Group's French-speaking brand (Dan's doc, section 1). Distinct
searches, same group - kept separate here, because merging them would invent a
number neither brand has.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from comparator.banks import category_for

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPORT_DIR = REPO_ROOT / "trends-benchmark" / "export"

# Their bank labels -> ours. All 14 banks have a Trends sheet now (the original
# KBC/ING/CBC baseline, Dan's six-bank extension, then the 21/09 second wave);
# CBC is KBC Group's francophone brand and stays a separate search entity.
BANK_MAP = {
    "ING": "ing", "KBC": "kbc", "CBC": "cbc",
    "BNPPF": "bnp_paribas_fortis", "ARGENTA": "argenta", "CRELAN": "crelan",
    "REVOLUT": "revolut", "N26": "n26", "BUNQ": "bunq",
    # steph 21/09, second wave: the five banks the comparator captured but the
    # benchmark had no search term for. Dan resolved them, so the Trends tab's
    # "no coverage" list is now empty and all 14 banks share one scale.
    "BELFIUS": "belfius", "BEOBANK": "beobank", "VDK": "vdk",
    "HELLOBANK": "hellobank", "KEYTRADE": "keytrade",
}

# Display names for the codes Dan stores, so the UI never shows "BNPPF".
BANK_DISPLAY = {
    "ING": "ING", "KBC": "KBC", "CBC": "CBC", "BNPPF": "BNP Paribas Fortis",
    "ARGENTA": "Argenta", "CRELAN": "Crelan", "REVOLUT": "Revolut",
    "N26": "N26", "BUNQ": "bunq",
    "BELFIUS": "Belfius", "BEOBANK": "Beobank", "VDK": "VDK Bank",
    "HELLOBANK": "Hello bank!", "KEYTRADE": "Keytrade Bank",
}

# pytrends returns the Knowledge Graph topic mid as the column name; a reader
# needs the brand. Mirror of Dan's config.TERM_DISPLAY_LABELS.
TERM_DISPLAY = {
    "/g/1z3t2x3c8": "CBC Banque & Assurance",
    "/m/07sc3dj": "BNP Paribas Fortis",
    "/m/03lmky": "Argenta",
    "/g/11c1p5t9vb": "N26",
    "/g/121yyfq9": "VDK Bank",
}

# Structural market events. DISPLAY ONLY: they annotate the weekly series and
# take no part in any computation. Mirror of Dan's config.KNOWN_EVENTS.
KNOWN_EVENTS = [
    {"bank": "BNPPF", "date": "2024-01-22",
     "label": "Integration of bpost banque (about 1 million clients migrated)"},
    {"bank": "N26", "date": "2024-03-14",
     "label": "Savings account launched in Belgium"},
    {"bank": "CRELAN", "date": "2024-06-10",
     "label": "Merger with AXA Bank Belgium, IT migration of about 840,000 clients"},
    {"bank": "BUNQ", "date": "2024-12-17", "label": "bunq Stocks available in Belgium"},
    {"bank": "REVOLUT", "date": "2025-05-01",
     "label": "Belgian accounts (IBAN BE) for new clients, migration through 2025"},
    {"bank": "REVOLUT", "date": "2025-08-21",
     "label": "Daily-interest savings account launched (press coverage date)"},
    {"bank": "BUNQ", "date": "2026-07-24",
     "label": "Belgian IBANs and Wero launched (press coverage date)"},
]

# Their product_id -> our product_family. Deliberately partial: a mapping that
# guessed would join a savings page to credit-card searches.
#
# steph 21/09, SCOPE CHANGE UPSTREAM. Dan's pipeline was narrowed to brand
# notoriety only: the 29 product sheets were dropped because most smaller banks'
# product terms flattened to near-zero once normalised in the same request as
# ING (33 of 43 candidate sheets rejected for coverage). Only brand-level sheets
# remain, so every key below now maps nothing.
#
# The mapping is KEPT, empty of matches, rather than deleted, because it is the
# record of a question this project can no longer answer: "is search interest in
# this bank's savings product up?" needs a savings sheet, and there is none.
# Share of search replaces it with a DIFFERENT question - "what portion of brand
# attention does each bank hold?" - not a better version of the same one.
PRODUCT_MAP = {
    "compte_a_vue": "current_account_pack",
    "compte_epargne": "savings_account",
    "pret_hypothecaire": "mortgage",
    "investissement_courtage": "investment",
}

# The brand sheets that replaced them, and the chaining anchors. Mirror of Dan's
# config.SHARE_OF_SEARCH_* - ING and KBC appear unchanged in EVERY sheet, which
# is what lets 14 banks share one scale despite pytrends' 5-term-per-request
# limit. Adding a sheet here means adding it to Dan's config first: the anchors
# have to be in it, literally, or the scale factor has nothing to key on.
BRAND_SHEETS = (
    "marque_generique",
    "marque_generique_traditionnelles",
    "marque_generique_traditionnelles_2",
    "marque_generique_digitales",
    "marque_generique_neobanques",
)
SHARE_REFERENCE_SHEET = "marque_generique"
SHARE_ANCHOR_BANKS = ("ING", "KBC")

# A brand whose raw 0-100 series never clears this is not really measured: it
# shares its request with a term that peaks at 100, so its own values are
# quantised into a handful of integers and its share is a rounding artefact as
# much as a fact. Reported alongside the number, never used to drop a bank.
MEASURABLE_PEAK_FLOOR = 10

# The four banks Belgian market commentary calls the big four. A market
# convention, NOT a result derived from this data - which is why the roll-up
# below checks it against the computed ranking instead of assuming they match.
BIG_FOUR_KEYS = ("kbc", "belfius", "ing", "bnp_paribas_fortis")

# Presentation convention, not a significance test. Two adjacent ranks closer
# than this are shown as level: chaining across requests and Google's integer
# 0-100 scale cannot order a gap that small. A systematic one-unit difference
# on a weekly series moves a share by more than this.
TIE_THRESHOLD_PTS = 0.5

SEGMENT_IDS = ("big_four", "other_incumbents", "challengers")
SEGMENT_LABELS = {
    "big_four": "big four",
    "other_incumbents": "other incumbents",
    "challengers": "challengers",
}

# The only facts on the Trends tab that are not computed from the payload.
# Everything else in the UI copy is derived at build time, so this registry is
# the single place a non-computed claim may enter - each one carrying its
# source and dates, which the UI always renders next to the claim.
EXTERNAL_REFERENCES = [
    {
        "id": "revolut_be_customers",
        "claim": (
            "Revolut reported more than 1 million private customers in Belgium, "
            "adding around 25,000 per month."
        ),
        "value": "more than 1 million private customers",
        "source": "Belga News Agency",
        "url": "https://www.belganewsagency.eu/revolut-passes-1-million-customers-in-belgium",
        "published": "2026-03-11",
        "retrieved": "2026-09-21",
        "appliesToBank": "Revolut",
    },
    {
        "id": "big_four_deposits",
        "claim": (
            "KBC, BNP Paribas Fortis, Belfius and ING Belgium account for the vast "
            "majority of retail deposits in Belgium."
        ),
        "value": None,
        "source": "Banks.eu",
        "url": "https://banks.eu/banks/belgium",
        "published": "2026-04-30",
        "retrieved": "2026-09-21",
        "appliesToBank": None,
    },
]


class TrendsUnavailable(RuntimeError):
    """The exports are not present. Not an error - the branch may not be merged."""


@dataclass
class TrendsContext:
    """Search-interest context for the banks and products we actually captured."""

    table: pd.DataFrame
    covered_banks: list[str]
    uncovered_banks: list[str]
    window_start: pd.Timestamp | None = None
    window_end: pd.Timestamp | None = None

    @property
    def available(self) -> bool:
        return not self.table.empty

    def render(self) -> str:
        if not self.available:
            # steph 21/09: this used to say "the exports are not present", which
            # is now the wrong diagnosis in the common case. They ARE present -
            # Dan's pipeline was narrowed to brand notoriety, so there is no
            # longer a per-product sheet to join a savings or mortgage page to.
            # Naming the real cause matters: "no data" invites someone to go
            # looking for a file, "no product sheets exist any more" tells them
            # the question itself changed.
            return (
                "No per-product search-interest context. Dan's Trends pipeline was narrowed to "
                "brand notoriety (brand sheets only, no product sheets), because most smaller "
                "banks' product terms flattened to near-zero once normalised against ING in the "
                "same request. Per-product interest is therefore unanswerable, not merely "
                "uncollected. Brand-level share of search replaces it with a different question - "
                "how attention splits across banks - and is reported in the Trends tab."
            )
        lines = [
            "Search interest (Google Trends, Belgium) for the captured bank/product pairs.",
            "CONTEXT ONLY - this is what people searched for, not what a campaign achieved.",
            "",
            self.table.to_string(index=False),
        ]
        if self.uncovered_banks:
            lines += ["", f"No trends data at all for: {', '.join(self.uncovered_banks)}."]
        return "\n".join(lines)


def load_trends(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> pd.DataFrame:
    """Read every *_trends_data.csv Dan's pipeline exports."""
    export_dir = Path(export_dir)
    files = sorted(export_dir.glob("*_trends_data.csv")) if export_dir.is_dir() else []
    if not files:
        raise TrendsUnavailable(
            f"no *_trends_data.csv under {export_dir}. The trends-benchmark branch may not be "
            "merged yet - search-interest context is skipped, nothing else is affected."
        )
    frames = [pd.read_csv(f) for f in files]
    trends = pd.concat(frames, ignore_index=True)
    trends["date"] = pd.to_datetime(trends["date"], errors="coerce", utc=True)
    trends["value"] = pd.to_numeric(trends["value"], errors="coerce")
    trends["bank_key"] = trends["bank"].map(BANK_MAP)
    trends["product_family"] = trends["product_id"].map(PRODUCT_MAP)
    return trends.dropna(subset=["date", "value"])


def interest_context(
    df: pd.DataFrame,
    trends: pd.DataFrame | None = None,
    *,
    months: int = 12,
) -> TrendsContext:
    """Summarise search interest for each (bank, product_family) we captured.

    Reports the recent level against the longer-run baseline, which is the only
    question this data can answer honestly: was attention to this product
    unusually high lately, or ordinary?
    """
    captured = df[["bank", "product_family"]].drop_duplicates()
    captured_banks = sorted(captured["bank"].dropna().unique())

    if trends is None or trends.empty:
        return TrendsContext(pd.DataFrame(), [], captured_banks)

    joinable = trends.dropna(subset=["bank_key", "product_family"])
    latest = joinable["date"].max()
    cutoff = latest - pd.DateOffset(months=months)

    rows = []
    covered: list[str] = []
    for bank, family in captured.itertuples(index=False):
        subset = joinable[(joinable["bank_key"] == bank) & (joinable["product_family"] == family)]
        if subset.empty:
            continue
        covered.append(bank)
        recent = subset[subset["date"] >= cutoff]["value"]
        baseline = subset[subset["date"] < cutoff]["value"]
        if recent.empty:
            continue
        recent_mean = float(recent.mean())
        baseline_mean = float(baseline.mean()) if not baseline.empty else float("nan")
        if baseline_mean and not pd.isna(baseline_mean):
            change = (recent_mean - baseline_mean) / baseline_mean * 100
            direction = "higher" if change > 10 else "lower" if change < -10 else "about the same"
        else:
            change, direction = float("nan"), "no baseline"
        rows.append({
            "bank": bank,
            "product_family": family,
            f"last_{months}m_mean": round(recent_mean, 1),
            "baseline_mean": round(baseline_mean, 1) if not pd.isna(baseline_mean) else None,
            "change_pct": round(change, 1) if not pd.isna(change) else None,
            "vs_baseline": direction,
            "weeks": int(len(subset)),
        })

    return TrendsContext(
        table=pd.DataFrame(rows),
        covered_banks=sorted(set(covered)),
        uncovered_banks=sorted(set(captured_banks) - set(covered)),
        window_start=cutoff if rows else None,
        window_end=latest if rows else None,
    )


def context_or_none(df: pd.DataFrame, export_dir: str | Path = DEFAULT_EXPORT_DIR) -> TrendsContext | None:
    """Best-effort: returns None when the exports are absent, never raises."""
    try:
        return interest_context(df, load_trends(export_dir))
    except TrendsUnavailable:
        return None


# -----------------------------------------------------------------------------
# The full Trends tab - brand search series.
# -----------------------------------------------------------------------------
# steph 18/09. The module above answers one narrow question ("is interest in
# this bank/product unusually high lately?") and feeds search_interest_context.md.
# Dan's export carries more: a five-year weekly series per term. That is a tab of
# its own, and the guardrails in this file's docstring apply to all of it:
# context, never an outcome, never regressed onto a page feature.
#
# dan 21/09: the campaign catalogue that used to live here is GONE. It matched
# real ad campaigns to detected spikes and scored them, which reads as "this
# campaign caused this spike" no matter how many caveats surround it - and this
# project has no performance data to support that reading (PRD 5.2, plan risk
# P-08). The tab now answers one question only: how much do people search for
# each bank. Dan's own pipeline still holds the catalogue if it is ever wanted
# back; nothing was deleted upstream.


def display_term(term: str) -> str:
    """Human label for a pytrends column, which may be a Knowledge Graph mid."""
    return TERM_DISPLAY.get(term, term)


def _iso(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _number(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_series(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> pd.DataFrame:
    """Every weekly point in Dan's export, in long format.

    Prefers the combined `all_trends_data.csv`; falls back to concatenating the
    per-bank `*_trends_data.csv` files when the combined export is absent, so
    either hand-off shape works. Raises TrendsUnavailable when neither exists.
    """
    export_dir = Path(export_dir)
    if not export_dir.is_dir():
        raise TrendsUnavailable(
            f"{export_dir} is not present. Dan's trends-benchmark export may not be "
            "merged or checked out - the Trends tab is skipped, nothing else is affected."
        )
    combined = export_dir / "all_trends_data.csv"
    if combined.is_file():
        frame = pd.read_csv(combined)
    else:
        files = sorted(p for p in export_dir.glob("*_trends_data.csv") if p.name != combined.name)
        if not files:
            raise TrendsUnavailable(
                f"no all_trends_data.csv or *_trends_data.csv under {export_dir}."
            )
        frame = pd.concat([pd.read_csv(p) for p in files], ignore_index=True)

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return (
        frame.dropna(subset=["date", "value"])
        .sort_values("date")
        .reset_index(drop=True)
    )


# -----------------------------------------------------------------------------
# Share of search - every bank on one scale (steph 21/09)
# -----------------------------------------------------------------------------
# Google Trends returns at most 5 terms per request and its 0-100 values are
# only comparable WITHIN one request, because each request is rescaled to its
# own peak. More banks than that therefore need several requests, chained
# through anchors (ING and KBC, byte-identical in every sheet) whose ratio
# between requests gives the factor that puts everything on one scale.
#
# That chaining is Dan's pipeline step (analysis/share_of_search.py), stored in
# his brand_share_of_search table and exported as a CSV. We READ it. Re-deriving
# it here would create a second definition of every number on screen, which is
# the one thing this repo's report layer refuses to do.
#
# What IS computed here is the roll-up his export does not carry: the aggregate
# share per bank. It must be volume-weighted - sum the rescaled values over the
# whole window, then divide - and never a mean of weekly shares, which would give
# a near-zero-volume week the same weight as a peak week.


@dataclass
class ShareOfSearch:
    """Each bank's share of the brand-search panel."""

    ranking: list[dict]
    window_start: str | None
    window_end: str | None
    weeks: int
    reference_sheet: str
    anchors: list[str]
    scale_factors: dict[str, float]
    low_confidence: list[str]
    insights: dict = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return bool(self.ranking)

    def render(self) -> str:
        if not self.available:
            return "No share-of-search data: brand_share_of_search.csv is absent."
        # steph 21/09: the request count is read from the data, not written in.
        # It said "three" until Dan's second wave made it five, which is exactly
        # the drift this report layer is built to prevent.
        lines = [
            f"Share of search, {self.window_start} to {self.window_end} "
            f"({self.weeks} weeks, Belgium, brand-level search).",
            f"{len(self.ranking)} banks chained across {len(self.scale_factors)} Google Trends "
            f"requests via the {' + '.join(self.anchors)} anchors; "
            f"{self.reference_sheet} is the reference scale.",
            "",
        ]
        for row in self.ranking:
            flag = "  (low confidence)" if row["lowConfidence"] else ""
            lines.append(f"  {row['rank']}. {row['bank']:<20} {row['sharePct']:5.1f}%{flag}")
        if self.low_confidence:
            lines += [
                "",
                "Low confidence: " + ", ".join(self.low_confidence) + ". Their raw series never "
                f"clears {MEASURABLE_PEAK_FLOOR}/100 because they share a request with a term that "
                "peaks at 100, so the share is quantisation as much as measurement.",
            ]
        return "\n".join(lines)


def restrict_to_common_window(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep only the weeks where every bank in the panel has a point.

    Dan's sheets were collected in two waves a week apart, so the first and last
    weeks of the union carry a partial panel. A share is a share OF something:
    computed on a partial panel it is arithmetically fine and substantively
    wrong - the final week alone put one bank above 78% because only five of
    fourteen banks were in its denominator.
    """
    if frame.empty:
        return frame
    per_date = frame.groupby("date")["bank"].nunique()
    complete = per_date[per_date == per_date.max()].index
    return frame[frame["date"].isin(complete)]


def load_share_of_search(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> pd.DataFrame:
    """Dan's pre-chained weekly table, on the common window. Raises when absent."""
    path = Path(export_dir) / "brand_share_of_search.csv"
    if not path.is_file():
        raise TrendsUnavailable(
            f"no brand_share_of_search.csv under {export_dir}. Run Dan's "
            "analysis/share_of_search.py and re-export - share of search is skipped."
        )
    frame = pd.read_csv(path)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in ("raw_value", "scale_factor", "rescaled_value", "share_pct"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["date", "rescaled_value"]).sort_values("date")
    return restrict_to_common_window(frame)


def share_of_search(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> ShareOfSearch | None:
    """Rank every bank by share of brand search. None when the export is absent."""
    try:
        frame = load_share_of_search(export_dir)
    except TrendsUnavailable:
        return None
    if frame.empty:
        return None

    # Volume-weighted, not a mean of weekly shares. See the note above.
    totals = frame.groupby("bank")["rescaled_value"].sum()
    grand_total = float(totals.sum())
    if grand_total <= 0:
        return None

    peaks = frame.groupby("bank")["raw_value"].max()
    weak = sorted(
        BANK_DISPLAY.get(code, code)
        for code, peak in peaks.items()
        if peak < MEASURABLE_PEAK_FLOOR
    )

    ranking = []
    for rank, (code, total) in enumerate(totals.sort_values(ascending=False).items(), start=1):
        peak = int(peaks.get(code, 0))
        ranking.append({
            "rank": rank,
            "bank": BANK_DISPLAY.get(code, code),
            "key": BANK_MAP.get(code, str(code).lower()),
            "segment": category_for(BANK_MAP.get(code, "")) or "traditional",
            "sharePct": round(float(total) / grand_total * 100, 2),
            "rawPeak": peak,
            "lowConfidence": peak < MEASURABLE_PEAK_FLOOR,
            "sourceSheet": str(frame[frame["bank"] == code]["source_fiche"].iloc[0]),
        })

    factors = (
        frame.groupby("source_fiche")["scale_factor"].first().round(4).to_dict()
    )
    share = ShareOfSearch(
        ranking=ranking,
        window_start=frame["date"].min().strftime("%Y-%m-%d"),
        window_end=frame["date"].max().strftime("%Y-%m-%d"),
        weeks=int(frame["date"].nunique()),
        reference_sheet=SHARE_REFERENCE_SHEET,
        anchors=list(SHARE_ANCHOR_BANKS),
        scale_factors={str(k): float(v) for k, v in factors.items()},
        low_confidence=weak,
    )
    share.insights = share_insights(share)
    return share


# -----------------------------------------------------------------------------
# Reading the ranking - segments, concentration, ties, per-bank sentences
# -----------------------------------------------------------------------------
# The ranking answers "who is first". Everything below answers "what shape is
# this", and all of it is derived from the ranking the pipeline already
# produced - no second definition of any number, and nothing the UI has to
# restate as a literal. Change the data and every sentence changes with it.


def _segment_of(key: str) -> str:
    """big four (market convention) first, then this repo's incumbent split."""
    if key in BIG_FOUR_KEYS:
        return "big_four"
    return "challengers" if category_for(key) == "challenger" else "other_incumbents"


def _tie_groups(ranking: list[dict]) -> list[list[dict]]:
    """Runs of consecutive ranks whose every adjacent gap is under the threshold.

    A chain can hold more than two banks: A-B and B-C both under the threshold
    makes one group of three, even where A-C is wider. That is the honest
    reading of "too close to order" applied transitively.
    """
    if not ranking:
        return []
    groups: list[list[dict]] = []
    current = [ranking[0]]
    for previous, row in zip(ranking, ranking[1:]):
        if previous["sharePct"] - row["sharePct"] < TIE_THRESHOLD_PTS:
            current.append(row)
        else:
            if len(current) > 1:
                groups.append(current)
            current = [row]
    if len(current) > 1:
        groups.append(current)
    return groups


def _segment_rollup(ranking: list[dict]) -> dict:
    groups = []
    for segment_id in SEGMENT_IDS:
        members = [r for r in ranking if _segment_of(r["key"]) == segment_id]
        groups.append({
            "id": segment_id,
            "label": SEGMENT_LABELS[segment_id],
            "sharePct": round(sum(r["sharePct"] for r in members), 2),
            "count": len(members),
            "members": [
                {"bank": r["bank"], "key": r["key"], "sharePct": r["sharePct"]}
                for r in members
            ],
        })

    top_four = ranking[:4]
    big_four_are_top_four = (
        len(ranking) >= 4 and {r["key"] for r in top_four} == set(BIG_FOUR_KEYS)
    )
    return {
        "groups": groups,
        "bigFourAreTopFour": big_four_are_top_four,
        "topFour": [
            {"bank": r["bank"], "key": r["key"], "rank": r["rank"], "sharePct": r["sharePct"]}
            for r in top_four
        ],
    }


def _concentration(ranking: list[dict]) -> dict:
    """HHI on the 0-10,000 scale, and the equally sized brand count it implies."""
    hhi = sum(r["sharePct"] ** 2 for r in ranking)
    return {
        "hhi": round(hhi, 1),
        "equivalentBrands": round(10_000 / hhi, 1) if hhi else None,
    }


def _bank_readings(ranking: list[dict], segments: dict) -> list[dict]:
    segment_share = {g["id"]: g["sharePct"] for g in segments["groups"]}
    tie_of: dict[str, list[dict]] = {}
    for group in _tie_groups(ranking):
        for row in group:
            tie_of[row["key"]] = group

    readings = []
    for index, row in enumerate(ranking):
        above = ranking[index - 1] if index else None
        group = tie_of.get(row["key"])
        segment_id = _segment_of(row["key"])
        own_segment = segment_share.get(segment_id) or 0.0
        readings.append({
            "rank": row["rank"],
            "bank": row["bank"],
            "key": row["key"],
            "sharePct": row["sharePct"],
            "gapToAbovePts": None if above is None else round(above["sharePct"] - row["sharePct"], 2),
            "bankAbove": None if above is None else above["bank"],
            # Spread across the whole tie group, so a three-bank chain reports
            # how far apart its ends are rather than one adjacent step.
            "tieWith": [] if not group else [m["bank"] for m in group if m["key"] != row["key"]],
            "tieSpreadPts": None if not group else round(
                group[0]["sharePct"] - group[-1]["sharePct"], 2
            ),
            "segment": segment_id,
            "segmentLabel": SEGMENT_LABELS[segment_id],
            "pctOfSegment": round(row["sharePct"] / own_segment * 100, 1) if own_segment else None,
            "lowConfidence": row["lowConfidence"],
        })
    return readings


def _challenger_focus(ranking: list[dict], segments: dict, low_confidence: list[str]) -> dict | None:
    """The largest challenger, and how far the incumbents sit above it."""
    challengers = [r for r in ranking if _segment_of(r["key"]) == "challengers"]
    if not challengers:
        return None
    leader = challengers[0]
    challenger_total = next(
        g["sharePct"] for g in segments["groups"] if g["id"] == "challengers"
    )
    reference = next(
        (ref for ref in EXTERNAL_REFERENCES if ref["appliesToBank"] == leader["bank"]), None
    )
    return {
        "bank": leader["bank"],
        "key": leader["key"],
        "rank": leader["rank"],
        "sharePct": leader["sharePct"],
        "pctOfChallengerAttention": (
            round(leader["sharePct"] / challenger_total * 100, 1) if challenger_total else None
        ),
        "incumbentsAbove": sum(
            1 for r in ranking
            if r["rank"] < leader["rank"] and _segment_of(r["key"]) != "challengers"
        ),
        "lowConfidenceBanks": list(low_confidence),
        "reference": reference,
    }


def share_insights(share: ShareOfSearch) -> dict:
    """Everything the Trends tab needs to read the ranking out loud."""
    ranking = share.ranking
    segments = _segment_rollup(ranking)
    return {
        "window": {
            "firstDate": share.window_start,
            "lastDate": share.window_end,
            "weeks": share.weeks,
            "banks": len(ranking),
            "fiches": len(share.scale_factors),
        },
        "segments": segments,
        "concentration": _concentration(ranking),
        "ties": {
            "thresholdPts": TIE_THRESHOLD_PTS,
            "groups": [[r["bank"] for r in g] for g in _tie_groups(ranking)],
        },
        "banks": _bank_readings(ranking, segments),
        "challengerFocus": _challenger_focus(ranking, segments, share.low_confidence),
        "measurablePeakFloor": MEASURABLE_PEAK_FLOOR,
        "references": EXTERNAL_REFERENCES,
    }


def _share_headline(share: ShareOfSearch) -> dict:
    """The 'who is first and why' sentence, computed from the real aggregates.

    Never a fixed string: a hardcoded conclusion silently becomes false after the
    next collection run, which is the failure this whole report layer avoids.
    """
    ranking = share.ranking
    leader = ranking[0]
    focus = next((r for r in ranking if r["key"] == "ing"), None)
    traditional = [r for r in ranking if r["segment"] == "traditional"]
    challenger = [r for r in ranking if r["segment"] == "challenger"]
    trad_share = round(sum(r["sharePct"] for r in traditional), 1)
    chal_share = round(sum(r["sharePct"] for r in challenger), 1)

    if focus is None:
        sentence = f"{leader['bank']} holds the largest share of brand search, at {leader['sharePct']}%."
    elif focus["rank"] == 1:
        runner_up = ranking[1]
        sentence = (
            f"ING holds the largest share of brand search at {focus['sharePct']}%, "
            f"ahead of {runner_up['bank']} at {runner_up['sharePct']}%."
        )
    else:
        gap = round(leader["sharePct"] - focus["sharePct"], 1)
        sentence = (
            f"{leader['bank']} leads brand search with {leader['sharePct']}%; ING is "
            f"{_ordinal(focus['rank'])} at {focus['sharePct']}%, {gap} points behind."
        )

    return {
        "sentence": sentence,
        "leader": leader["bank"],
        "leaderShare": leader["sharePct"],
        "focusRank": None if focus is None else focus["rank"],
        "focusShare": None if focus is None else focus["sharePct"],
        "traditionalShare": trad_share,
        "challengerShare": chal_share,
        "segmentSentence": (
            f"The {len(traditional)} incumbents together hold {trad_share}% of brand search; "
            f"the {len(challenger)} challengers hold {chal_share}%."
        ),
    }


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def share_timeseries(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> list[dict]:
    """Weekly share per bank, for the detail chart under the ranking."""
    try:
        frame = load_share_of_search(export_dir)
    except TrendsUnavailable:
        return []
    series = []
    for code, group in frame.groupby("bank"):
        rows = group.sort_values("date")
        series.append({
            "bank": BANK_DISPLAY.get(code, code),
            "key": BANK_MAP.get(code, str(code).lower()),
            "points": [
                [d.strftime("%Y-%m-%d"), round(float(s) * 100, 2)]
                for d, s in zip(rows["date"], rows["share_pct"])
            ],
        })
    return sorted(series, key=lambda s: s["bank"])


def _display_for_key(key: str) -> str:
    for code, canonical in BANK_MAP.items():
        if canonical == key:
            return BANK_DISPLAY.get(code, key)
    return key.replace("_", " ").title()


# -----------------------------------------------------------------------------
# How attention moved - trajectory, rank stability, benchmark scope
# -----------------------------------------------------------------------------
# The aggregated ranking above answers "who holds attention". This answers
# "which way is it moving", on the same volume-weighted basis, so the two can
# never disagree. Movement is described, never explained: this data shows that
# attention moved, not why.

# One period is one year of weekly points. Blocks are anchored on the LAST week
# and counted backwards, so the most recent period is always complete and any
# short remainder falls at the start, where it is dropped rather than compared
# against full years.
PERIOD_WEEKS = 52

# Presentation convention, not a significance test: a relative slope inside
# this band reads as "flat". Expressed as a percentage of the bank's own mean
# share so a small brand and a large one are judged on the same scale.
MOMENTUM_FLAT_BAND_PCT = 2.0

# Google Trends changed how it collects data on this date. The first period
# straddles it, so every trajectory is recomputed without that period and the
# two directions are compared - a trend that only survives with it is flagged.
METHOD_CHANGE_DATE = "2022-01-01"

# The bank this tab benchmarks FOR. Never a benchmark candidate itself.
BENCHMARK_SUBJECT = "ING"


def _period_blocks(dates: list[pd.Timestamp]) -> tuple[list[dict], int]:
    """52-week blocks anchored on the last week, counted backwards."""
    ordered = sorted(set(dates))
    full = len(ordered) // PERIOD_WEEKS
    dropped = len(ordered) - full * PERIOD_WEEKS
    blocks = []
    for index in range(full):
        start = dropped + index * PERIOD_WEEKS
        chunk = ordered[start:start + PERIOD_WEEKS]
        blocks.append({
            "index": index,
            "label": f"{chunk[0].strftime('%b %Y')}–{chunk[-1].strftime('%b %Y')}",
            "start": chunk[0].strftime("%Y-%m-%d"),
            "end": chunk[-1].strftime("%Y-%m-%d"),
            "dates": chunk,
        })
    return blocks, dropped


def _shares_per_period(frame: pd.DataFrame, blocks: list[dict], column: str) -> dict[str, list[float]]:
    """Volume-weighted share per period: sum the values, then divide.

    Never a mean of weekly shares - a near-zero-volume week would otherwise
    weigh as much as a peak week, the same trap the aggregate avoids.
    """
    names = sorted(frame[column].dropna().unique())
    series: dict[str, list[float]] = {name: [] for name in names}
    for block in blocks:
        window = frame[frame["date"].isin(block["dates"])]
        total = float(window["rescaled_value"].sum())
        sums = window.groupby(column)["rescaled_value"].sum()
        for name in names:
            value = float(sums.get(name, 0.0))
            series[name].append(round(value / total * 100, 2) if total else 0.0)
    return series


def _ols_slope(values: list[float]) -> float | None:
    """Points per period, i.e. per year. None below two periods."""
    if len(values) < 2:
        return None
    return float(np.polyfit(range(len(values)), values, 1)[0])


def _direction(relative_slope: float | None) -> str | None:
    if relative_slope is None:
        return None
    if relative_slope > MOMENTUM_FLAT_BAND_PCT:
        return "up"
    if relative_slope < -MOMENTUM_FLAT_BAND_PCT:
        return "down"
    return "flat"


def _relative_slope(values: list[float]) -> float | None:
    slope = _ols_slope(values)
    if slope is None:
        return None
    mean = sum(values) / len(values)
    return round(slope / mean * 100, 1) if mean else None


def _trajectory(shares: list[float]) -> dict:
    """Level change, momentum, and whether the momentum survives the 2022 cut."""
    relative = _relative_slope(shares)
    without_first = _relative_slope(shares[1:]) if len(shares) > 2 else None
    direction = _direction(relative)
    slope = _ols_slope(shares)
    return {
        "periodShares": shares,
        "meanSharePct": round(sum(shares) / len(shares), 2),
        "deltaPts": round(shares[-1] - shares[0], 2),
        "slopePtsPerYear": None if slope is None else round(slope, 3),
        "relativeSlopePctPerYear": relative,
        "relativeSlopeExFirstPeriod": without_first,
        "direction": direction,
        "robust": without_first is not None and direction == _direction(without_first),
    }


def _ranked_with_ties(shares: dict[str, float]) -> dict[str, int]:
    """Tie-group rank: every member of a tie group carries the group's top rank,
    so a reshuffle inside a group is invisible to rank comparisons.
    """
    ordered = sorted(shares.items(), key=lambda kv: kv[1], reverse=True)
    ranks: dict[str, int] = {}
    group_rank = 1
    for index, (bank, share) in enumerate(ordered):
        if index and ordered[index - 1][1] - share >= TIE_THRESHOLD_PTS:
            group_rank = index + 1
        ranks[bank] = group_rank
    return ranks


def _rank_stability(measurable: list[str], shares: dict[str, list[float]], blocks: list[dict]) -> dict:
    per_period = [
        _ranked_with_ties({bank: shares[bank][i] for bank in measurable})
        for i in range(len(blocks))
    ]

    banks = []
    for bank in measurable:
        ranks = [p[bank] for p in per_period]
        banks.append({
            "bank": bank,
            "ranks": ranks,
            "bestRank": min(ranks),
            "worstRank": max(ranks),
            "changes": sum(1 for a, b in zip(ranks, ranks[1:]) if a != b),
        })

    first, last = per_period[0], per_period[-1]
    overtakes, kept, total = [], 0, 0
    for i, a in enumerate(measurable):
        for b in measurable[i + 1:]:
            total += 1
            before, after = first[a] - first[b], last[a] - last[b]
            if before * after > 0 or before == after == 0:
                kept += 1
            # A pair tied in either period was never ordered, so it cannot
            # have been overtaken.
            elif before != 0 and after != 0:
                ahead, behind = (a, b) if after < 0 else (b, a)
                overtakes.append({"bank": ahead, "passed": behind})

    return {
        "banks": sorted(banks, key=lambda r: r["ranks"][-1]),
        "overtakes": overtakes,
        "pairsKept": kept,
        "pairsTotal": total,
    }


def _bank_key(bank: str) -> str:
    """Display name back to the comparator's bank key."""
    return next((k for code, k in BANK_MAP.items() if BANK_DISPLAY.get(code) == bank), "")


def _benchmark_entry(bank: str, roles: list[str], shares: dict, trajectories: dict, ing_last: float) -> dict:
    trajectory = trajectories[bank]
    last = shares[bank][-1]
    return {
        "bank": bank,
        "key": _bank_key(bank),
        "roles": roles,
        "lastSharePct": last,
        "deltaPts": trajectory["deltaPts"],
        "relativeSlopePctPerYear": trajectory["relativeSlopePctPerYear"],
        "direction": trajectory["direction"],
        "robust": trajectory["robust"],
        "gapToSubjectPts": round(last - ing_last, 2),
    }


def _benchmark_scope(
    measurable: list[str], shares: dict[str, list[float]], trajectories: dict, low_confidence: list[str]
) -> dict:
    subject_shares = shares.get(BENCHMARK_SUBJECT)
    if subject_shares is None:
        return {}
    ing_last = subject_shares[-1]

    key_of = _bank_key

    traditional = [
        b for b in measurable
        if b != BENCHMARK_SUBJECT and category_for(key_of(b)) == "traditional"
    ]
    challengers = [b for b in measurable if category_for(key_of(b)) == "challenger"]

    benchmarks = []
    if traditional:
        attention = max(traditional, key=lambda b: shares[b][-1])
        rising = [b for b in traditional if trajectories[b]["direction"] == "up"]
        momentum = (
            max(rising, key=lambda b: trajectories[b]["relativeSlopePctPerYear"])
            if rising else None
        )
        if momentum == attention:
            benchmarks.append(
                _benchmark_entry(attention, ["attention", "momentum"], shares, trajectories, ing_last)
            )
        else:
            benchmarks.append(
                _benchmark_entry(attention, ["attention"], shares, trajectories, ing_last)
            )
            if momentum:
                benchmarks.append(
                    _benchmark_entry(momentum, ["momentum"], shares, trajectories, ing_last)
                )

    challenger_benchmark = None
    if challengers:
        rising = [b for b in challengers if trajectories[b]["direction"] == "up"]
        pick = (
            max(rising, key=lambda b: trajectories[b]["relativeSlopePctPerYear"])
            if rising else max(challengers, key=lambda b: shares[b][-1])
        )
        challenger_benchmark = _benchmark_entry(pick, ["challenger"], shares, trajectories, ing_last)
        challenger_benchmark["onlyMeasurable"] = len(challengers) == 1

    excluded = [
        b for b in low_confidence if category_for(key_of(b)) == "challenger"
    ]
    subject = trajectories[BENCHMARK_SUBJECT]
    return {
        "subject": BENCHMARK_SUBJECT,
        "traditionalCandidates": len(traditional),
        "challengerCandidates": len(challengers),
        "benchmarks": benchmarks,
        "challenger": challenger_benchmark,
        "excludedChallengers": excluded,
        "subjectContext": {
            "bank": BENCHMARK_SUBJECT,
            "lastSharePct": ing_last,
            "deltaPts": subject["deltaPts"],
            "relativeSlopePctPerYear": subject["relativeSlopePctPerYear"],
            "direction": subject["direction"],
            "robust": subject["robust"],
        },
    }


def attention_trajectory(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> dict | None:
    """How each bank's and each segment's share moved, period by period.

    Low-volume brands are computed but never exposed for display: their weekly
    values move in whole steps of a few units, so a trajectory drawn through
    them would be a picture of rounding.
    """
    share = share_of_search(export_dir)
    if share is None or not share.ranking:
        return None
    frame = load_share_of_search(export_dir)

    blocks, dropped_weeks = _period_blocks(list(frame["date"].unique()))
    if len(blocks) < 2:
        return None

    frame = frame.assign(
        display=frame["bank"].map(lambda code: BANK_DISPLAY.get(code, code)),
        segment=frame["bank"].map(
            lambda code: _segment_of(BANK_MAP.get(code, str(code).lower()))
        ),
    )

    bank_shares = _shares_per_period(frame, blocks, "display")
    segment_shares = _shares_per_period(frame, blocks, "segment")
    trajectories = {bank: _trajectory(values) for bank, values in bank_shares.items()}

    low_confidence = list(share.low_confidence)
    aggregate_of = {row["bank"]: row["sharePct"] for row in share.ranking}
    measurable = [
        row["bank"] for row in share.ranking if row["bank"] not in low_confidence
    ]

    banks_payload = []
    for row in share.ranking:
        bank = row["bank"]
        flagged = bank in low_confidence
        entry = {
            "bank": bank,
            "key": row["key"],
            "aggregatedSharePct": aggregate_of[bank],
            "lowConfidence": flagged,
        }
        # A flagged brand carries no per-period figure into the payload at all,
        # so no view can render one by accident.
        entry.update(
            {"periodShares": None, "deltaPts": None, "relativeSlopePctPerYear": None,
             "direction": None, "robust": None}
            if flagged else
            {k: trajectories[bank][k] for k in
             ("periodShares", "deltaPts", "relativeSlopePctPerYear", "direction", "robust")}
        )
        banks_payload.append(entry)
    banks_payload.sort(
        key=lambda e: (e["periodShares"][-1] if e["periodShares"] else -1), reverse=True
    )

    movers = [
        e for e in banks_payload
        if e["deltaPts"] is not None and category_for(e["key"]) == "traditional"
    ]
    return {
        "periods": [
            {k: b[k] for k in ("index", "label", "start", "end")} for b in blocks
        ],
        "droppedWeeks": dropped_weeks,
        "weeksPerPeriod": PERIOD_WEEKS,
        "flatBandPct": MOMENTUM_FLAT_BAND_PCT,
        "methodChangeDate": METHOD_CHANGE_DATE,
        "segments": [
            {
                "id": segment_id,
                "label": SEGMENT_LABELS[segment_id],
                **_trajectory(segment_shares[segment_id]),
            }
            for segment_id in SEGMENT_IDS if segment_id in segment_shares
        ],
        "banks": banks_payload,
        "biggestRise": max(movers, key=lambda e: e["deltaPts"]) if movers else None,
        "biggestFall": min(movers, key=lambda e: e["deltaPts"]) if movers else None,
        "rankStability": _rank_stability(measurable, bank_shares, blocks),
        "benchmark": _benchmark_scope(measurable, bank_shares, trajectories, low_confidence),
        "lowConfidenceBanks": low_confidence,
    }


def build_trends_dashboard(
    captured: pd.DataFrame | None = None,
    export_dir: str | Path | None = None,
) -> dict | None:
    """Everything the Trends tab renders, or None when Dan's export is absent.

    All heavy lifting (joins, thresholds, roll-ups) happens here in the library;
    the UI renders the numbers it is handed. The guardrail sentence travels with
    the payload so it cannot be dropped on the way to the screen.
    """
    export_dir = export_dir or DEFAULT_EXPORT_DIR
    try:
        series = load_series(export_dir)
    except TrendsUnavailable:
        return None
    if series.empty:
        return None

    banks: list[dict] = []
    present_codes = [c for c in BANK_DISPLAY if c in set(series["bank"])]
    # Preserve Dan's sheet order (the row order of the export) rather than sorting.
    for code in present_codes:
        subset = series[series["bank"] == code]
        key = BANK_MAP.get(code, code.lower())
        products = []
        for product_id in list(dict.fromkeys(subset["product_id"])):
            sheet = subset[subset["product_id"] == product_id]
            terms = []
            for term in list(dict.fromkeys(sheet["term"])):
                term_rows = sheet[sheet["term"] == term].sort_values("date")
                points = [
                    [d.strftime("%Y-%m-%d"), int(v)]
                    for d, v in zip(term_rows["date"], term_rows["value"])
                ]
                terms.append({
                    "term": term,
                    "label": display_term(term),
                    "language": str(term_rows["language"].iloc[0]),
                    "points": points,
                })
            products.append({
                "id": product_id,
                "label": str(sheet["product_label"].iloc[0]),
                "terms": terms,
            })
        banks.append({
            "key": key,
            "name": BANK_DISPLAY[code],
            "segment": category_for(key) or "traditional",
            "products": products,
        })

    captured_keys = (
        sorted(set(captured["bank"].dropna()))
        if captured is not None and "bank" in captured.columns
        else []
    )
    present_keys = {b["key"] for b in banks}
    covered = [k for k in captured_keys if k in present_keys]
    uncovered = [k for k in captured_keys if k not in present_keys]

    share = share_of_search(export_dir)
    trajectory = attention_trajectory(export_dir)

    return {
        "available": True,
        "trajectory": trajectory,
        "shareOfSearch": None if share is None else {
            "ranking": share.ranking,
            "series": share_timeseries(export_dir),
            "window": {"start": share.window_start, "end": share.window_end},
            "weeks": share.weeks,
            "headline": _share_headline(share),
            "method": {
                "why": (
                    "Google Trends allows 5 terms per request and its 0-100 values are only "
                    f"comparable inside one request. {len(share.ranking)} banks need "
                    f"{len(share.scale_factors)} requests, so {' and '.join(share.anchors)} appear "
                    "unchanged in every one of them and the ratio of their means gives the factor "
                    "that puts every bank on one scale."
                ),
                "referenceSheet": share.reference_sheet,
                "anchors": share.anchors,
                "scaleFactors": share.scale_factors,
                "aggregation": (
                    "Aggregate share sums each bank's rescaled value over the whole window and "
                    "divides by the panel total, so a near-zero-volume week does not carry the "
                    "same weight as a peak week."
                ),
            },
            "lowConfidence": share.low_confidence,
            "insights": share.insights,
            "caveat": (
                "A share is a share of ATTENTION, not of customers, revenue or market. It says "
                "which brand people looked up, nothing about why or with what result."
            ),
        },
        "source": "Dan's trends-benchmark Google Trends benchmark (Belgium, 5-year weekly)",
        "window": {
            "start": series["date"].min().strftime("%Y-%m-%d"),
            "end": series["date"].max().strftime("%Y-%m-%d"),
        },
        "coverage": {
            "covered": [_display_for_key(k) for k in covered],
            "uncovered": [_display_for_key(k) for k in uncovered],
        },
        "banks": banks,
        "events": [
            {"bank": BANK_DISPLAY.get(e["bank"], e["bank"]), "key": BANK_MAP.get(e["bank"], e["bank"].lower()),
             "date": e["date"], "label": e["label"]}
            for e in KNOWN_EVENTS
        ],
        "guardrail": (
            "Google Trends measures what people searched for, not what any campaign "
            "achieved. It is context, never an outcome: nothing here links a page or a "
            "campaign to a click, a conversion or a sale, and no search value is ever "
            "regressed onto a page feature."
        ),
    }
