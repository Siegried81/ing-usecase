"""Tests for the bridge to Dan's Google Trends benchmark (steph 16/09).

The thing most worth testing here is what the module REFUSES to do: it must
stay context and never become an outcome variable, and it must vanish quietly
when the exports are not present.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.trends import (  # noqa: E402
    BANK_MAP,
    PRODUCT_MAP,
    TrendsUnavailable,
    anomalies_frame,
    build_trends_dashboard,
    context_or_none,
    detect_anomalies,
    interest_context,
    load_series,
    load_trends,
)


def _export(tmp_path: Path) -> Path:
    """A miniature version of Dan's export format."""
    rows = []
    for bank, product in (("ING", "compte_epargne"), ("KBC", "compte_a_vue")):
        for week in range(120):
            rows.append({
                "product_id": product, "product_label": product, "term": f"{bank} x",
                "bank": bank, "language": "fr",
                "date": (pd.Timestamp("2023-01-01", tz="UTC") + pd.Timedelta(weeks=week)).date(),
                # recent half is clearly higher, so direction is testable
                "value": 10 if week < 60 else 30,
            })
    path = tmp_path / "export"
    path.mkdir()
    pd.DataFrame(rows).to_csv(path / "all_trends_data.csv", index=False)
    return path


@pytest.fixture()
def campaigns() -> pd.DataFrame:
    return pd.DataFrame([
        {"bank": "ing", "product_family": "savings_account"},
        {"bank": "kbc", "product_family": "current_account_pack"},
        {"bank": "revolut", "product_family": "current_account_pack"},
        {"bank": "belfius", "product_family": "other"},
    ])


# --- absence is normal, not an error -----------------------------------------
def test_missing_exports_are_not_an_error(tmp_path, campaigns):
    """The kbc-ing-benchmark branch may simply not be merged."""
    assert context_or_none(campaigns, tmp_path / "nope") is None


def test_load_trends_explains_itself_when_absent(tmp_path):
    with pytest.raises(TrendsUnavailable, match="may not be merged"):
        load_trends(tmp_path)


def test_empty_trends_yields_no_context(campaigns):
    ctx = interest_context(campaigns, pd.DataFrame())
    assert not ctx.available
    assert "No search-interest context" in ctx.render()


# --- the join ----------------------------------------------------------------
def test_only_mapped_bank_product_pairs_are_joined(tmp_path, campaigns):
    ctx = interest_context(campaigns, load_trends(_export(tmp_path)))
    assert ctx.available
    pairs = set(zip(ctx.table["bank"], ctx.table["product_family"]))
    assert pairs == {("ing", "savings_account"), ("kbc", "current_account_pack")}


def test_banks_with_no_trends_data_are_named_not_silently_dropped(tmp_path, campaigns):
    ctx = interest_context(campaigns, load_trends(_export(tmp_path)))
    assert "revolut" in ctx.uncovered_banks and "belfius" in ctx.uncovered_banks
    assert "revolut" in ctx.render()


def test_direction_against_baseline_is_reported(tmp_path, campaigns):
    ctx = interest_context(campaigns, load_trends(_export(tmp_path)), months=12)
    assert (ctx.table["vs_baseline"] == "higher").all()


def test_product_mapping_is_partial_on_purpose():
    """A guessed mapping would join a savings page to credit-card searches."""
    assert "carte_credit" not in PRODUCT_MAP
    assert set(PRODUCT_MAP.values()) <= {
        "current_account_pack", "savings_account", "mortgage", "investment"}


def test_cbc_is_kept_separate_from_kbc():
    """Same group, distinct brands and distinct searches - merging would invent
    a number neither brand has."""
    assert BANK_MAP["CBC"] == "cbc" and BANK_MAP["KBC"] == "kbc"


# --- the guardrail that matters ----------------------------------------------
def test_context_never_returns_a_per_page_outcome_column(tmp_path, campaigns):
    """If this ever produced a per-page number, somebody would regress it onto
    page features and call it performance. It is aggregated by bank+product."""
    ctx = interest_context(campaigns, load_trends(_export(tmp_path)))
    assert "page_id" not in ctx.table.columns
    assert "url" not in ctx.table.columns


def test_render_states_it_is_not_performance_data(tmp_path, campaigns):
    text = interest_context(campaigns, load_trends(_export(tmp_path))).render()
    assert "not what a campaign achieved" in text


# --- the full Trends tab: anomaly detection ----------------------------------
def _one_month_series(values: list[int]) -> pd.DataFrame:
    """All points in one calendar month, so the seasonal profile equals the mean.

    That removes the seasonal term from the arithmetic and makes the test assert
    the z/ratio rule itself rather than a particular month's shape.
    """
    return pd.DataFrame({
        "date": pd.date_range("2024-03-01", periods=len(values), freq="D"),
        "value": values,
    })


def test_detect_isolated_spike_and_sustained_trend():
    values = [10] * 20
    values[5] = 100          # a single week
    values[10], values[11] = 90, 95   # two consecutive weeks
    result = detect_anomalies(_one_month_series(values))
    by_date = {r["date"]: r["type"] for r in result}
    assert by_date["2024-03-06"] == "isolated_spike"
    assert by_date["2024-03-11"] == "sustained_trend"
    assert by_date["2024-03-12"] == "sustained_trend"
    assert len(result) == 3


def test_detect_ignores_a_flat_series():
    """Zero variance means no anomaly is possible, not that nothing is flagged."""
    assert detect_anomalies(_one_month_series([10] * 30)) == []


def test_anomalies_frame_keys_by_product_term_and_bank():
    series = pd.DataFrame({
        "product_id": ["compte_a_vue"] * 20,
        "term": ["ING zichtrekening"] * 20,
        "bank": ["ING"] * 20,
        "date": pd.date_range("2024-03-01", periods=20, freq="D"),
        "value": [10] * 20,
    })
    series.loc[5, "value"] = 100
    frame = anomalies_frame(series)
    assert len(frame) == 1
    assert frame.loc[0, "product_id"] == "compte_a_vue"
    assert frame.loc[0, "term"] == "ING zichtrekening"
    assert frame.loc[0, "bank"] == "ING"


# --- the full Trends tab: the dashboard payload ------------------------------
def _campaign_exports(export_dir: Path) -> None:
    pd.DataFrame([
        {"id": 1, "bank": "ING", "name": "Level up", "language": "FR+NL",
         "start_date": "2026-09-05", "end_date": None, "date_confidence": "exact",
         "campaign_type": "brand", "target_fiches": "compte_a_vue;compte_epargne",
         "status": "scorable", "not_scorable_reason": None, "anomaly_count": 2,
         "fiches_touched": 2, "seasonal_confound_count": 1, "raw_score": 4.0,
         "breadth_multiplier": 1.5, "final_score": 6.0},
        {"id": 2, "bank": "KBC", "name": "Kate", "language": "NL",
         "start_date": "2025-10", "end_date": None, "date_confidence": "approximate",
         "campaign_type": "product", "target_fiches": "app_mobile",
         "status": "scorable", "not_scorable_reason": None, "anomaly_count": 0,
         "fiches_touched": 0, "seasonal_confound_count": 0, "raw_score": 0.0,
         "breadth_multiplier": 1.0, "final_score": 0.0},
    ]).to_csv(export_dir / "campaign_scorecards.csv", index=False)
    pd.DataFrame([
        {"campaign_id": 1, "campaign_name": "Level up", "campaign_bank": "ING",
         "product_id": "compte_a_vue", "term": "ING zichtrekening", "anomaly_bank": "ING",
         "date": "2026-09-06", "anomaly_type": "sustained_trend", "deviation_score": 2.05,
         "delay_days": 1, "possible_seasonal_confound": True,
         "overlapping_campaign_ids": None, "contribution": 1.23},
    ]).to_csv(export_dir / "campaign_matches.csv", index=False)


def test_dashboard_is_none_when_the_export_is_absent(tmp_path, campaigns):
    assert build_trends_dashboard(campaigns, tmp_path / "nope") is None


def test_dashboard_carries_series_anomalies_and_campaigns(tmp_path, campaigns):
    _export(tmp_path)
    _campaign_exports(tmp_path / "export")

    dashboard = build_trends_dashboard(campaigns, tmp_path / "export")
    assert dashboard is not None and dashboard["available"]

    names = {b["name"] for b in dashboard["banks"]}
    assert {"ING", "KBC"} <= names

    # The guardrail travels WITH the payload, not in a separate file.
    assert "not what any campaign achieved" in dashboard["guardrail"]

    # Coverage names the banks Dan has no search sheet for.
    assert "revolut" in [u.lower() for u in dashboard["coverage"]["uncovered"]]

    campaigns_out = dashboard["campaigns"]
    assert campaigns_out["catalogued"] == 2
    assert campaigns_out["scorable"] == 2
    ing = next(s for s in campaigns_out["summary"] if s["bank"] == "ING")
    kbc = next(s for s in campaigns_out["summary"] if s["bank"] == "KBC")
    assert ing["totalScore"] == 6.0 and ing["successRate"] == 1.0
    assert kbc["successRate"] == 0.0
    assert campaigns_out["matches"][0]["campaignId"] == 1


def test_dashboard_attaches_anomalies_to_the_right_term(tmp_path, campaigns):
    """A spike in one term's series must not appear on any other term."""
    export = tmp_path / "export"
    export.mkdir()
    dates = pd.date_range("2024-03-01", periods=20, freq="D")
    rows = []
    for term in ("ING zichtrekening", "compte a vue ING"):
        for i, date in enumerate(dates):
            rows.append({
                "product_id": "compte_a_vue", "product_label": "Compte a vue",
                "term": term, "bank": "ING", "language": "fr",
                "date": date.date(),
                "value": 100 if (term == "ING zichtrekening" and i == 5) else 10,
            })
    pd.DataFrame(rows).to_csv(export / "all_trends_data.csv", index=False)

    dashboard = build_trends_dashboard(campaigns, export)
    terms = {t["label"]: t for b in dashboard["banks"] for p in b["products"] for t in p["terms"]}
    assert len(terms["ING zichtrekening"]["anomalies"]) == 1
    assert terms["ING zichtrekening"]["anomalies"][0]["type"] == "isolated_spike"
    assert terms["compte a vue ING"]["anomalies"] == []
