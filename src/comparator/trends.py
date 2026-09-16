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

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPORT_DIR = REPO_ROOT / "kbc-ing-benchmark" / "export"

# Their bank labels -> ours. Only these three exist in the trends data.
BANK_MAP = {"ING": "ing", "KBC": "kbc", "CBC": "cbc"}

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
