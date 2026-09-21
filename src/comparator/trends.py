"""Bridge to Dan's Google Trends benchmark - search interest as CONTEXT.

steph 16/09, new module. trends-benchmark/ measures weekly Google search
interest per bank per product in Belgium and flags anomalous spikes. This module
joins that to the campaign dataset so a bank profile can carry the market
attention around its product, and degrades to nothing when the exports are
absent.

WHAT THIS IS NOT, and the reason this docstring leads with it.

Every deliverable in this project says we have no performance data (PRD 5.2,
plan risk P-08, D-09). Search interest is NOT performance data and joining it
here does not change that sentence. Three reasons, all of which have to survive
into the deck:

  * It measures what people searched for, not what any campaign achieved. Dan's
    own handoff doc is explicit that the pipeline "ne collecte aucune donnée
    publicitaire" and that spikes are dates to verify by hand.
  * The pages we captured are today's pages. A search spike in 2023 was caused
    by a campaign we never saw. Joining a 2026 page to a 2023 spike and calling
    it an effect would be the single most embarrassing error available to us.
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

from dataclasses import dataclass
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

# Anomaly-detection thresholds - Dan's, ported verbatim, not re-tuned here. A
# week is flagged only when it clears BOTH its own 5-year baseline (z-score)
# and its normal seasonal level for that calendar month.
Z_SCORE_THRESHOLD = 1.5
SEASONAL_RATIO_THRESHOLD = 1.3
ANOMALY_TYPES = {
    "isolated_spike": "Isolated spike",
    "sustained_trend": "Sustained trend",
}

# Structural market events. DISPLAY ONLY: anomaly detection never reads these,
# so a break is still detected on its own merits and merely annotated after.
# Mirror of Dan's config.KNOWN_EVENTS.
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
                "brand notoriety (three brand sheets, no product sheets), because most smaller "
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
# The full Trends tab - series, anomalies and campaign scorecards.
# -----------------------------------------------------------------------------
# steph 18/09. The module above answers one narrow question ("is interest in
# this bank/product unusually high lately?") and feeds search_interest_context.md.
# Dan's export carries far more: a five-year weekly series per term, the spikes
# he detects, and the catalogue of real campaigns matched to those spikes. That
# is a tab of its own, and the guardrails in this file's docstring apply to all
# of it: context, never an outcome, never regressed onto a page feature.


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


def detect_anomalies(series: pd.DataFrame) -> list[dict]:
    """Dan's rule, ported: flag a week, then group consecutive flags.

    A point must clear BOTH thresholds: z >= 1.5 against the term's own history
    and value / seasonal-month-mean >= 1.3. A run of consecutive flagged weeks
    is an `isolated_spike` (length 1) or a `sustained_trend` (length >= 2). A
    flat or all-zero series has no anomaly, by construction.

    Kept identical to `analysis/anomaly_detection.py` so this tab and Dan's
    Streamlit app cannot report different spikes for the same series.
    """
    series = series.sort_values("date").reset_index(drop=True)
    values = series["value"]
    if values.empty:
        return []

    overall_mean = float(values.mean())
    overall_std = float(values.std(ddof=0))
    if overall_std == 0 or overall_mean == 0:
        return []

    months = series["date"].dt.month
    seasonal_mean = values.groupby(months).transform("mean")
    z_scores = (values - overall_mean) / overall_std
    seasonal_ratio = values / seasonal_mean.replace(0, np.nan)
    is_candidate = (
        (z_scores >= Z_SCORE_THRESHOLD) & (seasonal_ratio >= SEASONAL_RATIO_THRESHOLD)
    ).fillna(False)

    results: list[dict] = []
    run_start: int | None = None
    for i in range(len(series) + 1):
        flagged = bool(is_candidate.iloc[i]) if i < len(series) else False
        if flagged and run_start is None:
            run_start = i
        elif not flagged and run_start is not None:
            run_indices = list(range(run_start, i))
            kind = "isolated_spike" if len(run_indices) == 1 else "sustained_trend"
            for idx in run_indices:
                results.append({
                    "date": series.loc[idx, "date"].strftime("%Y-%m-%d"),
                    "value": int(series.loc[idx, "value"]),
                    "type": kind,
                    "label": ANOMALY_TYPES.get(kind, kind),
                    "score": round(float(z_scores.iloc[idx]), 3),
                })
            run_start = None
    return results


def anomalies_frame(series: pd.DataFrame) -> pd.DataFrame:
    """One row per detected anomaly, keyed by (product_id, term, bank)."""
    rows: list[dict] = []
    for (product_id, term, bank), group in series.groupby(
        ["product_id", "term", "bank"], observed=True
    ):
        for anomaly in detect_anomalies(group[["date", "value"]]):
            rows.append({"product_id": product_id, "term": term, "bank": bank, **anomaly})
    return pd.DataFrame(
        rows, columns=["product_id", "term", "bank", "date", "value", "type", "label", "score"]
    )


# -----------------------------------------------------------------------------
# Share of search - nine banks on one scale (steph 21/09)
# -----------------------------------------------------------------------------
# Google Trends returns at most 5 terms per request and its 0-100 values are
# only comparable WITHIN one request, because each request is rescaled to its
# own peak. Nine banks therefore need three requests, chained through anchors
# (ING and KBC, byte-identical in all three) whose ratio between requests gives
# the factor that puts everything on one scale.
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
    """Each bank's share of the nine-bank brand-search panel."""

    ranking: list[dict]
    window_start: str | None
    window_end: str | None
    weeks: int
    reference_sheet: str
    anchors: list[str]
    scale_factors: dict[str, float]
    low_confidence: list[str]

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


def load_share_of_search(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> pd.DataFrame:
    """Dan's pre-chained weekly table. Raises TrendsUnavailable when absent."""
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
    return frame.dropna(subset=["date", "rescaled_value"]).sort_values("date")


def share_of_search(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> ShareOfSearch | None:
    """Rank the nine banks by share of brand search. None when the export is absent."""
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
    return ShareOfSearch(
        ranking=ranking,
        window_start=frame["date"].min().strftime("%Y-%m-%d"),
        window_end=frame["date"].max().strftime("%Y-%m-%d"),
        weeks=int(frame["date"].nunique()),
        reference_sheet=SHARE_REFERENCE_SHEET,
        anchors=list(SHARE_ANCHOR_BANKS),
        scale_factors={str(k): float(v) for k, v in factors.items()},
        low_confidence=weak,
    )


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


def load_campaign_scorecards(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> pd.DataFrame:
    path = Path(export_dir) / "campaign_scorecards.csv"
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


def load_campaign_matches(export_dir: str | Path = DEFAULT_EXPORT_DIR) -> pd.DataFrame:
    path = Path(export_dir) / "campaign_matches.csv"
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


def _scorecard_rows(frame: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in frame.iterrows():
        bank_code = str(r.get("bank", ""))
        targets = [t for t in str(r.get("target_fiches") or "").split(";") if t]
        rows.append({
            "id": int(r["id"]),
            "bank": BANK_DISPLAY.get(bank_code, bank_code),
            "key": BANK_MAP.get(bank_code, bank_code.lower()),
            "name": r.get("name"),
            "language": r.get("language"),
            "startDate": _iso(r.get("start_date")),
            "endDate": _iso(r.get("end_date")),
            "confidence": r.get("date_confidence"),
            "type": r.get("campaign_type"),
            "targetFiches": targets,
            "status": r.get("status"),
            "reason": _iso(r.get("not_scorable_reason")),
            "anomalyCount": int(_number(r.get("anomaly_count")) or 0),
            "fichesTouched": int(_number(r.get("fiches_touched")) or 0),
            "seasonalConfounds": int(_number(r.get("seasonal_confound_count")) or 0),
            "rawScore": round(_number(r.get("raw_score")) or 0.0, 3),
            "finalScore": round(_number(r.get("final_score")) or 0.0, 3),
        })
    return rows


def _match_rows(frame: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in frame.iterrows():
        confound = r.get("possible_seasonal_confound")
        rows.append({
            "campaignId": int(r["campaign_id"]),
            "campaignName": r.get("campaign_name"),
            "campaignBank": BANK_DISPLAY.get(str(r.get("campaign_bank")), r.get("campaign_bank")),
            "productId": r.get("product_id"),
            "term": display_term(str(r.get("term"))),
            "date": _iso(r.get("date")),
            "type": r.get("anomaly_type"),
            "label": ANOMALY_TYPES.get(str(r.get("anomaly_type")), r.get("anomaly_type")),
            "score": _number(r.get("deviation_score")),
            "delayDays": None if _number(r.get("delay_days")) is None else int(_number(r.get("delay_days"))),
            "seasonalConfound": bool(confound) if not (isinstance(confound, float) and pd.isna(confound)) else False,
            "contribution": _number(r.get("contribution")),
        })
    return rows


def _campaign_rollup(scorecards: list[dict]) -> tuple[list[dict], list[dict]]:
    """Per-bank campaign summary and type mix, computed here so the UI does no arithmetic."""
    order: list[str] = []
    for card in scorecards:
        if card["bank"] not in order:
            order.append(card["bank"])

    summary, by_type = [], []
    for bank in order:
        rows = [c for c in scorecards if c["bank"] == bank]
        scorable = [c for c in rows if c["status"] == "scorable"]
        total = sum(c["finalScore"] for c in scorable)
        hits = sum(1 for c in scorable if c["finalScore"] > 0)
        summary.append({
            "bank": bank,
            "catalogued": len(rows),
            "scorable": len(scorable),
            "totalScore": round(total, 3),
            "averageScore": round(total / len(scorable), 3) if scorable else 0.0,
            "successRate": round(hits / len(scorable), 3) if scorable else 0.0,
        })
        mix = {"brand": 0, "product": 0, "sponsoring": 0, "csr": 0, "other": 0}
        for c in rows:
            key = str(c["type"] or "other")
            mix[key] = mix.get(key, 0) + 1
        by_type.append({"bank": bank, **mix})
    return summary, by_type


def _display_for_key(key: str) -> str:
    for code, canonical in BANK_MAP.items():
        if canonical == key:
            return BANK_DISPLAY.get(code, key)
    return key.replace("_", " ").title()


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

    anomalies = anomalies_frame(series)
    anomaly_index: dict[tuple[str, str], list[dict]] = {}
    for row in anomalies.to_dict("records"):
        anomaly_index.setdefault((row["product_id"], row["term"]), []).append({
            "date": row["date"],
            "value": int(row["value"]),
            "type": row["type"],
            "label": row["label"],
            "score": float(row["score"]),
        })

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
                    "anomalies": anomaly_index.get((product_id, term), []),
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

    scorecards = _scorecard_rows(load_campaign_scorecards(export_dir))
    matches = _match_rows(load_campaign_matches(export_dir))
    summary, by_type = _campaign_rollup(scorecards)
    share = share_of_search(export_dir)

    return {
        "available": True,
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
        "campaigns": {
            "catalogued": len(scorecards),
            "scorable": sum(1 for c in scorecards if c["status"] == "scorable"),
            "scorecards": sorted(scorecards, key=lambda c: c["finalScore"], reverse=True),
            "matches": matches,
            "summary": summary,
            "byType": by_type,
        },
        "guardrail": (
            "Google Trends measures what people searched for, not what any campaign "
            "achieved. It is context, never an outcome: nothing here links a page or a "
            "campaign to a click, a conversion or a sale, and no search value is ever "
            "regressed onto a page feature."
        ),
    }
