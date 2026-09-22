"""Tests for the bridge to Dan's Google Trends benchmark (steph 16/09).

The thing most worth testing here is what the module REFUSES to do: it must
stay context and never become an outcome variable, and it must vanish quietly
when the exports are not present.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.trends import (  # noqa: E402
    BANK_MAP,
    BENCHMARK_SUBJECT,
    BIG_FOUR_KEYS,
    EXTERNAL_REFERENCES,
    MOMENTUM_FLAT_BAND_PCT,
    PERIOD_WEEKS,
    PRODUCT_MAP,
    TIE_THRESHOLD_PTS,
    TrendsUnavailable,
    attention_trajectory,
    build_trends_dashboard,
    context_or_none,
    interest_context,
    load_series,
    load_trends,
    share_of_search,
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
    """The trends-benchmark branch may simply not be merged."""
    assert context_or_none(campaigns, tmp_path / "nope") is None


def test_load_trends_explains_itself_when_absent(tmp_path):
    with pytest.raises(TrendsUnavailable, match="may not be merged"):
        load_trends(tmp_path)


def test_empty_trends_yields_no_context(campaigns):
    ctx = interest_context(campaigns, pd.DataFrame())
    assert not ctx.available
    assert "No per-product search-interest context" in ctx.render()


def test_absent_product_context_names_the_scope_change_not_a_missing_file(campaigns):
    """steph 21/09: the old message blamed a missing export, which sends a reader
    hunting for a file that is in fact present. The pipeline narrowed to brand
    notoriety, so per-product interest is unanswerable rather than uncollected -
    and the message has to say which, or the next person re-opens a dead end."""
    rendered = interest_context(campaigns, pd.DataFrame()).render()
    assert "brand notoriety" in rendered
    assert "unanswerable, not merely uncollected" in rendered


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


# --- the full Trends tab: the dashboard payload ------------------------------
def test_dashboard_is_none_when_the_export_is_absent(tmp_path, campaigns):
    assert build_trends_dashboard(campaigns, tmp_path / "nope") is None


def test_dashboard_carries_the_series(tmp_path, campaigns):
    _export(tmp_path)

    dashboard = build_trends_dashboard(campaigns, tmp_path / "export")
    assert dashboard is not None and dashboard["available"]

    names = {b["name"] for b in dashboard["banks"]}
    assert {"ING", "KBC"} <= names

    # The guardrail travels WITH the payload, not in a separate file.
    assert "not what any campaign achieved" in dashboard["guardrail"]

    # Coverage names the banks Dan has no search sheet for.
    assert "revolut" in [u.lower() for u in dashboard["coverage"]["uncovered"]]


def test_dashboard_no_longer_carries_a_campaign_catalogue(tmp_path, campaigns):
    """dan 21/09: the catalogue matched real ad campaigns to detected spikes and
    scored them. However it was captioned, a reader takes "this campaign scored 6
    on these spikes" as cause and effect - and this project has no performance
    data that could support that (PRD 5.2, plan risk P-08). The tab answers one
    question now: how much each bank is searched for. Pinned as a test so the
    block cannot drift back in with the next export refresh."""
    _export(tmp_path)
    dashboard = build_trends_dashboard(campaigns, tmp_path / "export")
    assert "campaigns" not in dashboard


# -----------------------------------------------------------------------------
# Share of search - steph 21/09
# -----------------------------------------------------------------------------


def _share_export(tmp_path: Path, rows: list[dict]) -> Path:
    export = tmp_path / "export"
    export.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(export / "brand_share_of_search.csv", index=False)
    return export


def _share_row(bank, date, value, *, sheet="marque_generique", factor=1.0):
    return {
        "bank": bank, "date": date, "source_fiche": sheet, "raw_value": value,
        "scale_factor": factor, "rescaled_value": value * factor,
        "share_pct": 0.0,  # recomputed downstream; never read for the aggregate
    }


def test_share_of_search_is_none_when_the_export_is_absent(tmp_path):
    assert share_of_search(tmp_path / "nope") is None


def test_aggregate_share_is_volume_weighted_not_a_mean_of_weekly_shares():
    """Playbook trap 4. A near-zero-volume week must not weigh as much as a peak
    week. Here A dominates the only high-volume week; a mean of weekly shares
    would put A and B level, summing first keeps A ahead."""
    rows = [
        _share_row("ING", "2026-01-04", 100), _share_row("KBC", "2026-01-04", 0),
        _share_row("ING", "2026-01-11", 0), _share_row("KBC", "2026-01-11", 1),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        result = share_of_search(_share_export(Path(tmp), rows))
    shares = {r["bank"]: r["sharePct"] for r in result.ranking}
    # Volume-weighted: 100 / 101 vs 1 / 101. A mean of weekly shares gives 50/50.
    assert shares["ING"] > 98.0
    assert shares["KBC"] < 2.0


def test_a_brand_crushed_by_its_request_peer_is_flagged_low_confidence():
    """Playbook trap 2. bunq peaking at 1/100 in a sheet where KBC peaks at 100
    is a quantisation artefact, not a measured near-zero. Report it, never drop it."""
    rows = [
        _share_row("KBC", "2026-01-04", 100),
        _share_row("BUNQ", "2026-01-04", 1, sheet="marque_generique_neobanques"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        result = share_of_search(_share_export(Path(tmp), rows))
    bunq = next(r for r in result.ranking if r["bank"] == "bunq")
    assert bunq["lowConfidence"] is True
    assert "bunq" in result.low_confidence
    assert next(r for r in result.ranking if r["bank"] == "KBC")["lowConfidence"] is False


def test_headline_is_computed_from_the_aggregates_not_hardcoded():
    """The conclusion sentence must follow the data, so a later run cannot leave
    a stale claim on screen."""
    rows = [
        _share_row("ING", "2026-01-04", 90), _share_row("KBC", "2026-01-04", 10),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        export = _share_export(Path(tmp), rows)
        dashboard_rows = pd.DataFrame([{
            "product_id": "marque_generique", "product_label": "Marque",
            "term": "ING", "bank": "ING", "language": "en",
            "date": "2026-01-04", "value": 90,
        }])
        dashboard_rows.to_csv(export / "brand_trends_data.csv", index=False)
        dashboard = build_trends_dashboard(None, export)
    headline = dashboard["shareOfSearch"]["headline"]
    assert headline["leader"] == "ING"
    assert "ING holds the largest share" in headline["sentence"]


def test_share_payload_carries_the_chaining_method_with_it():
    """A reader must be able to see WHY nine banks are on one scale without
    leaving the page - the anchors and the factors travel with the numbers."""
    rows = [_share_row("ING", "2026-01-04", 50), _share_row("KBC", "2026-01-04", 50)]
    with tempfile.TemporaryDirectory() as tmp:
        result = share_of_search(_share_export(Path(tmp), rows))
    assert result.anchors == ["ING", "KBC"]
    assert result.reference_sheet == "marque_generique"
    assert result.scale_factors["marque_generique"] == 1.0


def test_request_count_in_the_narrative_follows_the_data():
    """steph 21/09: this sentence said "three requests" in prose while the data
    had grown to five sheets. Anything countable must be counted, or the next
    wave of banks silently makes the method description false."""
    rows = [
        _share_row("ING", "2026-01-04", 50),
        _share_row("KBC", "2026-01-04", 50),
        _share_row("BELFIUS", "2026-01-04", 40, sheet="marque_generique_traditionnelles_2",
                   factor=1.1),
        _share_row("VDK", "2026-01-04", 7, sheet="marque_generique_traditionnelles_2",
                   factor=1.1),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        result = share_of_search(_share_export(Path(tmp), rows))
    rendered = result.render()
    assert "4 banks chained across 2 Google Trends requests" in rendered
    assert "three" not in rendered.lower()


# -----------------------------------------------------------------------------
# Reading the ranking - segments, concentration, ties, challenger focus
# -----------------------------------------------------------------------------
# The UI writes no figure of its own, so every sentence it renders is only as
# honest as these roll-ups. Each test below pins a number the copy would
# otherwise be tempted to hard-code.


def _insights(rows: list[dict]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        return share_of_search(_share_export(Path(tmp), rows)).insights


def test_partial_panel_weeks_are_dropped_before_any_share_is_computed():
    """The two collection waves are a week apart, so the union's first and last
    weeks hold a partial panel. A share computed there is arithmetically fine
    and substantively wrong."""
    rows = [
        _share_row("ING", "2026-01-04", 50), _share_row("KBC", "2026-01-04", 50),
        _share_row("ING", "2026-01-11", 50), _share_row("KBC", "2026-01-11", 50),
        _share_row("BELFIUS", "2026-01-11", 40, sheet="marque_generique_traditionnelles_2"),
    ]
    insights = _insights(rows)
    # Only 2026-01-11 has all three banks; the two-bank week must not count.
    assert insights["window"]["weeks"] == 1
    assert insights["window"]["firstDate"] == insights["window"]["lastDate"] == "2026-01-11"
    assert insights["window"]["banks"] == 3


def test_segment_shares_sum_to_the_total_and_follow_bank_category():
    rows = [
        _share_row("KBC", "2026-01-04", 40), _share_row("ING", "2026-01-04", 30),
        _share_row("ARGENTA", "2026-01-04", 20, sheet="marque_generique_traditionnelles"),
        _share_row("REVOLUT", "2026-01-04", 10, sheet="marque_generique_neobanques"),
    ]
    insights = _insights(rows)
    groups = {g["id"]: g for g in insights["segments"]["groups"]}
    assert sum(g["sharePct"] for g in groups.values()) == pytest.approx(100.0, abs=0.01)
    # Membership comes from BIG_FOUR_KEYS then BANK_CATEGORY, never from rank.
    assert {m["key"] for m in groups["big_four"]["members"]} == {"kbc", "ing"}
    assert {m["key"] for m in groups["other_incumbents"]["members"]} == {"argenta"}
    assert {m["key"] for m in groups["challengers"]["members"]} == {"revolut"}


def test_hhi_and_equivalent_brand_count_on_a_hand_computed_fixture():
    """75/25 gives 75^2 + 25^2 = 6250, i.e. 1.6 equally sized brands."""
    rows = [_share_row("ING", "2026-01-04", 75), _share_row("KBC", "2026-01-04", 25)]
    concentration = _insights(rows)["concentration"]
    assert concentration["hhi"] == pytest.approx(6250.0, abs=0.1)
    assert concentration["equivalentBrands"] == pytest.approx(1.6, abs=0.05)


def test_two_banks_closer_than_the_threshold_are_one_tie_group():
    rows = [_share_row("ING", "2026-01-04", 1000), _share_row("KBC", "2026-01-04", 997)]
    insights = _insights(rows)
    assert insights["ties"]["groups"] == [["ING", "KBC"]]
    ing = next(b for b in insights["banks"] if b["key"] == "ing")
    assert ing["tieWith"] == ["KBC"]
    assert ing["tieSpreadPts"] < TIE_THRESHOLD_PTS


def test_a_chain_of_small_gaps_makes_one_tie_group_of_three():
    """A-B and B-C both under the threshold is one group, even where A-C is
    wider: too-close-to-order applied transitively."""
    rows = [
        _share_row("ING", "2026-01-04", 340), _share_row("KBC", "2026-01-04", 336),
        _share_row("BELFIUS", "2026-01-04", 332, sheet="marque_generique_traditionnelles_2"),
    ]
    insights = _insights(rows)
    assert insights["ties"]["groups"] == [["ING", "KBC", "Belfius"]]
    spread = next(b for b in insights["banks"] if b["key"] == "ing")["tieSpreadPts"]
    assert spread > TIE_THRESHOLD_PTS  # the ends are further apart than the steps


def test_a_gap_of_exactly_the_threshold_is_not_a_tie():
    """The convention is strictly-below, so the boundary stays orderable."""
    rows = [_share_row("ING", "2026-01-04", 100.5), _share_row("KBC", "2026-01-04", 99.5)]
    insights = _insights(rows)
    gap = next(b for b in insights["banks"] if b["key"] == "kbc")["gapToAbovePts"]
    assert gap == pytest.approx(TIE_THRESHOLD_PTS, abs=1e-9)
    assert insights["ties"]["groups"] == []


def test_big_four_claim_falls_back_when_an_outsider_reaches_the_top_four():
    """The convention is checked against the ranking, never assumed. Argenta
    above BNPPF must not produce the big-four-capture sentence."""
    rows = [
        _share_row("KBC", "2026-01-04", 40), _share_row("ING", "2026-01-04", 30),
        _share_row("BELFIUS", "2026-01-04", 20, sheet="marque_generique_traditionnelles_2"),
        _share_row("ARGENTA", "2026-01-04", 15, sheet="marque_generique_traditionnelles"),
        _share_row("BNPPF", "2026-01-04", 5, sheet="marque_generique_traditionnelles"),
    ]
    segments = _insights(rows)["segments"]
    assert segments["bigFourAreTopFour"] is False
    assert [t["bank"] for t in segments["topFour"]][3] == "Argenta"
    # The big four roll-up still exists; it just cannot be called the top four.
    big_four = next(g for g in segments["groups"] if g["id"] == "big_four")
    assert {m["key"] for m in big_four["members"]} == set(BIG_FOUR_KEYS)


def test_big_four_claim_holds_when_they_really_are_the_top_four():
    rows = [
        _share_row("KBC", "2026-01-04", 40), _share_row("ING", "2026-01-04", 30),
        _share_row("BELFIUS", "2026-01-04", 20, sheet="marque_generique_traditionnelles_2"),
        _share_row("BNPPF", "2026-01-04", 15, sheet="marque_generique_traditionnelles"),
        _share_row("ARGENTA", "2026-01-04", 5, sheet="marque_generique_traditionnelles"),
    ]
    assert _insights(rows)["segments"]["bigFourAreTopFour"] is True


def test_every_figure_moves_when_the_fixture_shares_move():
    """No sentence may carry a literal: change the data, change the numbers."""
    def fixture(ing, kbc, revolut):
        return [
            _share_row("ING", "2026-01-04", ing), _share_row("KBC", "2026-01-04", kbc),
            _share_row("REVOLUT", "2026-01-04", revolut, sheet="marque_generique_neobanques"),
        ]

    a, b = _insights(fixture(70, 25, 5)), _insights(fixture(50, 30, 20))
    assert a["concentration"]["hhi"] != b["concentration"]["hhi"]
    assert a["concentration"]["equivalentBrands"] != b["concentration"]["equivalentBrands"]
    assert a["banks"][0]["sharePct"] != b["banks"][0]["sharePct"]
    assert a["banks"][1]["gapToAbovePts"] != b["banks"][1]["gapToAbovePts"]
    assert a["segments"]["groups"][0]["sharePct"] != b["segments"]["groups"][0]["sharePct"]


def test_bank_and_query_counts_follow_the_panel():
    """Block 1 states how many banks and how many queries; both are counted."""
    two = _insights([_share_row("ING", "2026-01-04", 50), _share_row("KBC", "2026-01-04", 50)])
    three = _insights([
        _share_row("ING", "2026-01-04", 50), _share_row("KBC", "2026-01-04", 50),
        _share_row("BELFIUS", "2026-01-04", 40, sheet="marque_generique_traditionnelles_2"),
    ])
    assert two["window"]["banks"] == 2 and two["window"]["fiches"] == 1
    assert three["window"]["banks"] == 3 and three["window"]["fiches"] == 2


def test_challenger_focus_is_the_largest_challenger_by_share():
    rows = [
        _share_row("KBC", "2026-01-04", 60),
        _share_row("REVOLUT", "2026-01-04", 30, sheet="marque_generique_neobanques"),
        _share_row("N26", "2026-01-04", 10, sheet="marque_generique_neobanques"),
    ]
    focus = _insights(rows)["challengerFocus"]
    assert focus["bank"] == "Revolut"
    assert focus["rank"] == 2
    assert focus["incumbentsAbove"] == 1
    assert focus["pctOfChallengerAttention"] == pytest.approx(75.0, abs=0.2)
    assert focus["reference"]["id"] == "revolut_be_customers"


def test_the_revolut_reference_is_dropped_when_another_challenger_leads():
    """A reference belongs to a bank, not to a slot in the layout."""
    rows = [
        _share_row("KBC", "2026-01-04", 60),
        _share_row("N26", "2026-01-04", 30, sheet="marque_generique_neobanques"),
        _share_row("REVOLUT", "2026-01-04", 10, sheet="marque_generique_neobanques"),
    ]
    focus = _insights(rows)["challengerFocus"]
    assert focus["bank"] == "N26"
    assert focus["reference"] is None


def test_the_measurement_floor_list_matches_the_low_confidence_flags():
    rows = [
        _share_row("KBC", "2026-01-04", 100),
        _share_row("BUNQ", "2026-01-04", 1, sheet="marque_generique_neobanques"),
        _share_row("REVOLUT", "2026-01-04", 40, sheet="marque_generique_neobanques"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        share = share_of_search(_share_export(Path(tmp), rows))
    focus = share.insights["challengerFocus"]
    assert focus["lowConfidenceBanks"] == share.low_confidence == ["bunq"]
    flagged = {b["bank"] for b in share.insights["banks"] if b["lowConfidence"]}
    assert flagged == set(share.low_confidence)


def test_external_references_travel_with_their_source_and_dates():
    """The only non-computed facts on the tab; they may never appear unsourced."""
    rows = [_share_row("ING", "2026-01-04", 50), _share_row("KBC", "2026-01-04", 50)]
    references = _insights(rows)["references"]
    assert {r["id"] for r in references} == {"revolut_be_customers", "big_four_deposits"}
    for reference in references:
        assert reference["source"] and reference["url"].startswith("https://")
        assert reference["published"] and reference["retrieved"]
    assert references == EXTERNAL_REFERENCES


def test_per_bank_reading_carries_its_share_of_its_own_segment():
    rows = [
        _share_row("KBC", "2026-01-04", 60), _share_row("ING", "2026-01-04", 20),
        _share_row("REVOLUT", "2026-01-04", 20, sheet="marque_generique_neobanques"),
    ]
    banks = {b["key"]: b for b in _insights(rows)["banks"]}
    assert banks["kbc"]["pctOfSegment"] == pytest.approx(75.0, abs=0.2)
    assert banks["ing"]["pctOfSegment"] == pytest.approx(25.0, abs=0.2)
    # A lone challenger holds all of its segment's attention.
    assert banks["revolut"]["pctOfSegment"] == pytest.approx(100.0, abs=0.2)
    assert banks["kbc"]["segmentLabel"] == "big four"
    assert banks["revolut"]["segmentLabel"] == "challengers"


# -----------------------------------------------------------------------------
# How attention moved - periods, trajectories, rank stability, benchmark scope
# -----------------------------------------------------------------------------


def _weekly(bank: str, values: list[float], *, sheet="marque_generique", start="2021-01-04"):
    """One row per week for one bank, so a fixture reads as a time series."""
    first = pd.Timestamp(start)
    return [
        _share_row(bank, (first + pd.Timedelta(weeks=i)).strftime("%Y-%m-%d"), v, sheet=sheet)
        for i, v in enumerate(values)
    ]


def _flat(bank: str, level: float, weeks: int, **kw):
    return _weekly(bank, [level] * weeks, **kw)


def _trajectory_of(rows: list[dict]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        return attention_trajectory(_share_export(Path(tmp), rows))


def test_periods_are_52_week_blocks_anchored_on_the_last_week():
    """Anchored backwards, so the most recent period is always complete and any
    short remainder falls at the start, where it is dropped."""
    weeks = PERIOD_WEEKS * 2 + 5
    rows = _flat("ING", 60, weeks) + _flat("KBC", 40, weeks)
    traj = _trajectory_of(rows)
    assert len(traj["periods"]) == 2
    assert traj["droppedWeeks"] == 5
    assert traj["periods"][-1]["end"] == rows[-1]["date"]


def test_period_shares_are_volume_weighted_not_a_mean_of_weekly_shares():
    """One near-zero-volume week must not weigh as much as a peak week."""
    weeks = PERIOD_WEEKS * 2
    # In the last period ING dominates the high-volume weeks and KBC wins only
    # the flat ones; a mean of weekly shares would put them far closer.
    ing = [50] * PERIOD_WEEKS + [100] * (PERIOD_WEEKS - 1) + [0]
    kbc = [50] * PERIOD_WEEKS + [1] * (PERIOD_WEEKS - 1) + [1]
    traj = _trajectory_of(_weekly("ING", ing) + _weekly("KBC", kbc))
    last_ing = next(b for b in traj["banks"] if b["bank"] == "ING")["periodShares"][-1]
    weekly_mean = sum(
        i / (i + k) * 100 for i, k in zip(ing[PERIOD_WEEKS:], kbc[PERIOD_WEEKS:])
    ) / PERIOD_WEEKS
    assert last_ing == pytest.approx(99.0, abs=0.3)
    assert abs(last_ing - weekly_mean) > 1.0


def test_slope_and_relative_slope_on_a_hand_computed_fixture():
    """Three periods at 40 / 50 / 60% of the panel: +10 pts per year on a mean
    of 50, so +20% per year in relative terms."""
    weeks = PERIOD_WEEKS * 3
    ing = [40] * PERIOD_WEEKS + [50] * PERIOD_WEEKS + [60] * PERIOD_WEEKS
    kbc = [60] * PERIOD_WEEKS + [50] * PERIOD_WEEKS + [40] * PERIOD_WEEKS
    traj = _trajectory_of(_weekly("ING", ing) + _weekly("KBC", kbc))
    entry = next(b for b in traj["banks"] if b["bank"] == "ING")
    assert entry["periodShares"] == [40.0, 50.0, 60.0]
    assert entry["deltaPts"] == pytest.approx(20.0, abs=0.01)
    assert entry["relativeSlopePctPerYear"] == pytest.approx(20.0, abs=0.2)
    assert entry["direction"] == "up"


def test_direction_labels_respect_the_flat_band():
    """A drift smaller than the band is flat, not a trend."""
    weeks = PERIOD_WEEKS * 3
    # ING moves by a fraction of a point per year: well inside the band.
    ing = [50] * PERIOD_WEEKS + [50.2] * PERIOD_WEEKS + [50.4] * PERIOD_WEEKS
    kbc = [50] * PERIOD_WEEKS + [49.8] * PERIOD_WEEKS + [49.6] * PERIOD_WEEKS
    traj = _trajectory_of(_weekly("ING", ing) + _weekly("KBC", kbc))
    entry = next(b for b in traj["banks"] if b["bank"] == "ING")
    assert abs(entry["relativeSlopePctPerYear"]) < MOMENTUM_FLAT_BAND_PCT
    assert entry["direction"] == "flat"


def test_robust_is_false_when_only_the_first_period_drives_the_trend():
    """The first period straddles Google's 2022 collection change, so a trend
    that disappears without it is flagged rather than reported as a finding."""
    weeks = PERIOD_WEEKS * 3
    # A big step between period 1 and 2, then flat: the slope is real overall
    # but vanishes once the first period is dropped.
    ing = [20] * PERIOD_WEEKS + [60] * PERIOD_WEEKS + [60] * PERIOD_WEEKS
    kbc = [80] * PERIOD_WEEKS + [40] * PERIOD_WEEKS + [40] * PERIOD_WEEKS
    traj = _trajectory_of(_weekly("ING", ing) + _weekly("KBC", kbc))
    entry = next(b for b in traj["banks"] if b["bank"] == "ING")
    assert entry["direction"] == "up"
    assert entry["robust"] is False


def test_a_reshuffle_inside_a_tie_group_is_neither_a_rank_change_nor_an_overtake():
    weeks = PERIOD_WEEKS * 2
    # ING and KBC swap by a hair; BELFIUS sits clearly below both throughout.
    ing = [45.1] * PERIOD_WEEKS + [44.9] * PERIOD_WEEKS
    kbc = [44.9] * PERIOD_WEEKS + [45.1] * PERIOD_WEEKS
    bel = [10.0] * weeks
    traj = _trajectory_of(
        _weekly("ING", ing) + _weekly("KBC", kbc)
        + _weekly("BELFIUS", bel, sheet="marque_generique_traditionnelles_2")
    )
    stability = traj["rankStability"]
    assert stability["overtakes"] == []
    assert all(b["changes"] == 0 for b in stability["banks"] if b["bank"] in {"ING", "KBC"})


def test_a_real_overtake_is_reported_with_its_direction():
    weeks = PERIOD_WEEKS * 2
    ing = [60] * PERIOD_WEEKS + [30] * PERIOD_WEEKS
    kbc = [40] * PERIOD_WEEKS + [70] * PERIOD_WEEKS
    traj = _trajectory_of(_weekly("ING", ing) + _weekly("KBC", kbc))
    assert traj["rankStability"]["overtakes"] == [{"bank": "KBC", "passed": "ING"}]


def test_pair_counts_exclude_flagged_banks():
    """n(n-1)/2 over the measurable banks only: a brand nobody can rank does
    not create pairs to preserve."""
    weeks = PERIOD_WEEKS * 2
    rows = (
        _flat("ING", 60, weeks) + _flat("KBC", 30, weeks)
        + _flat("BELFIUS", 15, weeks, sheet="marque_generique_traditionnelles_2")
        + _flat("BUNQ", 1, weeks, sheet="marque_generique_neobanques")
    )
    traj = _trajectory_of(rows)
    assert traj["lowConfidenceBanks"] == ["bunq"]
    # Three measurable banks -> three pairs, bunq contributes none.
    assert traj["rankStability"]["pairsTotal"] == 3
    assert all(b["bank"] != "bunq" for b in traj["rankStability"]["banks"])


def test_a_flagged_bank_exposes_no_period_figure_for_display():
    weeks = PERIOD_WEEKS * 2
    rows = (
        _flat("ING", 60, weeks) + _flat("KBC", 39, weeks)
        + _flat("BUNQ", 1, weeks, sheet="marque_generique_neobanques")
    )
    traj = _trajectory_of(rows)
    bunq = next(b for b in traj["banks"] if b["bank"] == "bunq")
    assert bunq["lowConfidence"] is True
    assert bunq["periodShares"] is None
    assert bunq["deltaPts"] is None and bunq["direction"] is None and bunq["robust"] is None
    # It keeps its aggregated share: the ranking still lists it.
    assert bunq["aggregatedSharePct"] > 0


def test_the_benchmark_subject_is_never_its_own_benchmark():
    weeks = PERIOD_WEEKS * 2
    rows = (
        _flat("ING", 60, weeks) + _flat("KBC", 25, weeks)
        + _flat("BELFIUS", 15, weeks, sheet="marque_generique_traditionnelles_2")
    )
    scope = _trajectory_of(rows)["benchmark"]
    assert scope["subject"] == BENCHMARK_SUBJECT
    assert all(b["bank"] != BENCHMARK_SUBJECT for b in scope["benchmarks"])


def test_a_flagged_bank_is_never_selected_as_a_benchmark():
    weeks = PERIOD_WEEKS * 2
    # VDK is flagged, and would otherwise win momentum outright.
    vdk = [1] * PERIOD_WEEKS + [8] * PERIOD_WEEKS
    rows = (
        _flat("ING", 50, weeks) + _flat("KBC", 45, weeks)
        + _weekly("VDK", vdk, sheet="marque_generique_traditionnelles_2")
    )
    traj = _trajectory_of(rows)
    assert "VDK Bank" in traj["lowConfidenceBanks"]
    assert all(b["bank"] != "VDK Bank" for b in traj["benchmark"]["benchmarks"])


def test_one_card_when_the_same_bank_leads_attention_and_momentum():
    weeks = PERIOD_WEEKS * 2
    kbc = [40] * PERIOD_WEEKS + [70] * PERIOD_WEEKS
    ing = [50] * PERIOD_WEEKS + [20] * PERIOD_WEEKS
    bel = [10] * weeks
    rows = (
        _weekly("ING", ing) + _weekly("KBC", kbc)
        + _weekly("BELFIUS", bel, sheet="marque_generique_traditionnelles_2")
    )
    benchmarks = _trajectory_of(rows)["benchmark"]["benchmarks"]
    assert len(benchmarks) == 1
    assert benchmarks[0]["bank"] == "KBC"
    assert set(benchmarks[0]["roles"]) == {"attention", "momentum"}


def test_momentum_leader_is_null_when_no_traditional_bank_is_rising():
    weeks = PERIOD_WEEKS * 2
    rows = (
        _flat("ING", 50, weeks) + _flat("KBC", 30, weeks)
        + _flat("BELFIUS", 20, weeks, sheet="marque_generique_traditionnelles_2")
    )
    benchmarks = _trajectory_of(rows)["benchmark"]["benchmarks"]
    assert all("momentum" not in b["roles"] for b in benchmarks)


def test_a_single_measurable_challenger_is_marked_as_the_only_one():
    weeks = PERIOD_WEEKS * 2
    rows = (
        _flat("ING", 50, weeks) + _flat("KBC", 28, weeks)
        + _flat("REVOLUT", 21, weeks, sheet="marque_generique_neobanques")
        + _flat("BUNQ", 1, weeks, sheet="marque_generique_neobanques")
    )
    scope = _trajectory_of(rows)["benchmark"]
    assert scope["challenger"]["bank"] == "Revolut"
    assert scope["challenger"]["onlyMeasurable"] is True
    assert scope["excludedChallengers"] == ["bunq"]


def test_the_challenger_benchmark_is_null_when_none_is_measurable():
    weeks = PERIOD_WEEKS * 2
    rows = (
        _flat("ING", 60, weeks) + _flat("KBC", 39, weeks)
        + _flat("BUNQ", 1, weeks, sheet="marque_generique_neobanques")
    )
    scope = _trajectory_of(rows)["benchmark"]
    assert scope["challenger"] is None
    assert scope["challengerCandidates"] == 0


def test_the_asterisked_list_equals_the_flags():
    weeks = PERIOD_WEEKS * 2
    rows = (
        _flat("ING", 60, weeks) + _flat("KBC", 38, weeks)
        + _flat("BUNQ", 1, weeks, sheet="marque_generique_neobanques")
        + _flat("N26", 1, weeks, sheet="marque_generique_neobanques")
    )
    with tempfile.TemporaryDirectory() as tmp:
        export = _share_export(Path(tmp), rows)
        share = share_of_search(export)
        traj = attention_trajectory(export)
    assert traj["lowConfidenceBanks"] == share.low_confidence
    assert set(traj["lowConfidenceBanks"]) == {"bunq", "N26"}


def test_no_anomaly_key_survives_in_the_payload(tmp_path, campaigns):
    _export(tmp_path)
    dashboard = build_trends_dashboard(campaigns, tmp_path / "export")
    serialised = json.dumps(dashboard)
    for banned in ("anomalies", "isolated_spike", "sustained_trend", "deviation_score"):
        assert banned not in serialised


def test_period_labels_and_figures_follow_the_data():
    """No literal may survive a change of fixture: labels and shares both move."""
    weeks = PERIOD_WEEKS * 2
    a = _trajectory_of(_flat("ING", 60, weeks) + _flat("KBC", 40, weeks))
    b = _trajectory_of(
        _flat("ING", 60, weeks, start="2019-01-06")
        + _flat("KBC", 20, weeks, start="2019-01-06")
    )
    assert [p["label"] for p in a["periods"]] != [p["label"] for p in b["periods"]]
    share_a = next(x for x in a["banks"] if x["bank"] == "ING")["periodShares"]
    share_b = next(x for x in b["banks"] if x["bank"] == "ING")["periodShares"]
    assert share_a != share_b
