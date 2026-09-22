"""Tests for the search-interest benchmark lessons (steph 22/09).

The thing worth pinning here is the boundary: search interest chooses WHICH
brands to look at, the measured features say WHAT they do, and the module must
never let one stand in for the other.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.benchmarks import (  # noqa: E402
    COMMON_MIN_SD,
    LESSON_MIN_GAP_SD,
    build_benchmark_lessons,
)
from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402

BANKS = ["ing", "kbc", "crelan", "revolut", "belfius", "argenta"]


@pytest.fixture()
def fd():
    return load_dictionary()


@pytest.fixture()
def df(fd):
    return build_fixture(fd, banks=BANKS, pages_per_bank=2)


def _trajectory(*entries, challenger=None):
    """A trajectory carrying only what this module reads from it."""
    return {
        "benchmark": {
            "subject": "ING",
            "benchmarks": list(entries),
            "challenger": challenger,
        }
    }


def _entry(bank, key, roles, share=10.0, slope=1.0, direction="up"):
    return {
        "bank": bank, "key": key, "roles": roles, "lastSharePct": share,
        "relativeSlopePctPerYear": slope, "direction": direction,
    }


KBC = _entry("KBC", "kbc", ["attention"])
CRELAN = _entry("Crelan", "crelan", ["momentum"])
REVOLUT = _entry("Revolut", "revolut", ["challenger"])


def test_no_trajectory_means_no_section(df, fd):
    """Trends absent is normal - the section disappears, nothing else breaks."""
    assert build_benchmark_lessons(df, fd, None) is None


def test_only_the_banks_trends_selected_are_profiled(df, fd):
    result = build_benchmark_lessons(df, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT))
    assert [b["key"] for b in result["banks"]] == ["kbc", "crelan", "revolut"]
    assert [b["role"] for b in result["banks"]] == ["attention", "momentum", "challenger"]


def test_the_focus_bank_is_never_one_of_its_own_benchmarks(df, fd):
    """ING is what the benchmarks are FOR; it cannot also be one of them."""
    ing_entry = _entry("ING", "ing", ["attention"])
    result = build_benchmark_lessons(df, fd, _trajectory(ing_entry, CRELAN, challenger=REVOLUT))
    assert all(b["key"] != "ing" for b in result["banks"])


def test_a_bank_trends_did_not_select_is_absent(df, fd):
    result = build_benchmark_lessons(df, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT))
    assert all(b["key"] != "belfius" for b in result["banks"])


def test_every_lesson_clears_the_gap_threshold(df, fd):
    """A feature where a benchmark and ING do the same thing teaches nothing."""
    result = build_benchmark_lessons(df, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT))
    for bank in result["banks"]:
        for lesson in bank["lessons"]:
            assert abs(lesson["gapSd"]) >= LESSON_MIN_GAP_SD
            assert lesson["gapSd"] == pytest.approx(lesson["z"] - lesson["focusZ"], abs=0.02)
            assert lesson["direction"] == ("above" if lesson["gapSd"] > 0 else "below")


def test_shared_ground_needs_all_benchmarks_on_one_side_and_the_focus_on_the_other(df, fd):
    result = build_benchmark_lessons(df, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT))
    keys = [b["key"] for b in result["banks"]]
    lookup = {b["key"]: {l["feature"]: l for l in b["lessons"]} for b in result["banks"]}
    for item in result["common"]:
        assert abs(item["meanZ"]) >= COMMON_MIN_SD
        # The focus bank leans the other way, which is what makes it a lesson.
        assert (item["meanZ"] > 0) != (item["focusZ"] > 0)
        # A shared fact is never repeated as one bank's own lesson.
        for key in keys:
            assert item["feature"] not in lookup[key]


def test_a_disagreement_really_straddles_the_average(df, fd):
    result = build_benchmark_lessons(df, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT))
    for item in result["divergent"]:
        values = [v["z"] for v in item["values"]]
        assert max(values) > 0 and min(values) < 0
        assert item["spreadSd"] == pytest.approx(max(values) - min(values), abs=0.02)


def test_twin_features_of_one_dimension_are_reported_once(df, fd):
    """has_animation and animated_asset_count describe one choice; listing both
    reads as two findings when there is one."""
    result = build_benchmark_lessons(df, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT))
    dimensions = [fd[i["feature"]].dimension for i in result["common"] if i["feature"] in fd]
    assert len(dimensions) == len(set(dimensions))
    for bank in result["banks"]:
        dims = [fd[l["feature"]].dimension for l in bank["lessons"] if l["feature"] in fd]
        assert len(dims) == len(set(dims))


def test_the_caveat_refuses_the_causal_reading(df, fd):
    """The whole section invites 'they are searched for because of this'. The
    payload has to say, in the payload, that it shows no such thing."""
    result = build_benchmark_lessons(df, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT))
    assert "selected on search attention" in result["caveat"]
    assert "not a demonstration" in result["caveat"]


def test_figures_follow_the_data_not_the_copy(df, fd):
    """Change what a bank does and its lessons change with it."""
    def crelan(result):
        return {l["feature"]: l["gapSd"] for b in result["banks"] if b["key"] == "crelan"
                for l in b["lessons"]}

    base = crelan(build_benchmark_lessons(df, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT)))
    moved_feature = next(iter(base))

    tilted = df.copy()
    tilted.loc[tilted["bank"] == "crelan", moved_feature] = (
        df[moved_feature].max() * 10 + 100
    )
    moved = crelan(build_benchmark_lessons(tilted, fd, _trajectory(KBC, CRELAN, challenger=REVOLUT)))

    assert base != moved
    assert base[moved_feature] != moved.get(moved_feature)


def test_trend_figures_are_carried_through_from_the_trajectory(df, fd):
    """The card states share and momentum; both come from Trends, unaltered."""
    entry = _entry("KBC", "kbc", ["attention"], share=21.3, slope=-2.8, direction="down")
    result = build_benchmark_lessons(df, fd, _trajectory(entry, CRELAN, challenger=REVOLUT))
    card = next(b for b in result["banks"] if b["key"] == "kbc")
    assert card["lastSharePct"] == 21.3
    assert card["relativeSlopePctPerYear"] == -2.8
    assert card["trendDirection"] == "down"


def test_fewer_than_two_benchmarks_yields_nothing(df, fd):
    """One brand is not a pattern; the section does not appear."""
    assert build_benchmark_lessons(df, fd, _trajectory(KBC)) is None
