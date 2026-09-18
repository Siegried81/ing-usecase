"""Bridge to Dan's Google Trends benchmark - search interest as CONTEXT.

steph 16/09, new module. kbc-ing-benchmark/ measures weekly Google search
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
  * Coverage is ING, KBC and CBC only. Belfius, Revolut, N26, Argenta, Crelan
    and bunq have no trends data at all, so any comparison across the full bank
    set is missing most of its rows.

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
DEFAULT_EXPORT_DIR = REPO_ROOT / "kbc-ing-benchmark" / "export"

# Their bank labels -> ours. All nine banks have a Trends sheet now (the
# original KBC/ING/CBC baseline plus Dan's six-bank extension); CBC is KBC
# Group's francophone brand and stays a separate search entity.
BANK_MAP = {
    "ING": "ing", "KBC": "kbc", "CBC": "cbc",
    "BNPPF": "bnp_paribas_fortis", "ARGENTA": "argenta", "CRELAN": "crelan",
    "REVOLUT": "revolut", "N26": "n26", "BUNQ": "bunq",
}

# Display names for the codes Dan stores, so the UI never shows "BNPPF".
BANK_DISPLAY = {
    "ING": "ING", "KBC": "KBC", "CBC": "CBC", "BNPPF": "BNP Paribas Fortis",
    "ARGENTA": "Argenta", "CRELAN": "Crelan", "REVOLUT": "Revolut",
    "N26": "N26", "BUNQ": "bunq",
}

# pytrends returns the Knowledge Graph topic mid as the column name; a reader
# needs the brand. Mirror of Dan's config.TERM_DISPLAY_LABELS.
TERM_DISPLAY = {
    "/g/1z3t2x3c8": "CBC Banque & Assurance",
    "/m/07sc3dj": "BNP Paribas Fortis",
    "/m/03lmky": "Argenta",
    "/g/11c1p5t9vb": "N26",
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
PRODUCT_MAP = {
    "compte_a_vue": "current_account_pack",
    "compte_epargne": "savings_account",
    "pret_hypothecaire": "mortgage",
    "investissement_courtage": "investment",
}


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
            return ("No search-interest context: the Google Trends exports are not present, "
                    "or no captured bank/product pair is covered by them.")
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
            f"no *_trends_data.csv under {export_dir}. The kbc-ing-benchmark branch may not be "
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
            f"{export_dir} is not present. Dan's kbc-ing-benchmark export may not be "
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

    return {
        "available": True,
        "source": "Dan's kbc-ing-benchmark Google Trends benchmark (Belgium, 5-year weekly)",
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
