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
    context_or_none,
    interest_context,
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
