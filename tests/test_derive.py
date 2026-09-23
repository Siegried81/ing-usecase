"""Tests for derived-feature recomputation."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.derive import recompute_derived  # noqa: E402
from comparator.dictionary import load_dictionary  # noqa: E402


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


def test_aida_coverage_counts_the_stages(fd):
    df = pd.DataFrame([{"aida_attention": True, "aida_interest": True,
                        "aida_desire": False, "aida_action": True}])
    assert recompute_derived(df, fd)["aida_coverage_score"].iat[0] == 3


def test_aida_coverage_survives_a_csv_round_trip(fd, tmp_path):
    """Booleans come back as the strings 'True'/'False' - a naive sum would count both."""
    df = pd.DataFrame([{"aida_attention": True, "aida_interest": False,
                        "aida_desire": False, "aida_action": False}])
    path = tmp_path / "r.csv"
    df.to_csv(path, index=False)
    assert recompute_derived(pd.read_csv(path), fd)["aida_coverage_score"].iat[0] == 1


def test_partial_aida_scores_nothing_rather_than_something(fd):
    """'2 of the 4 we bothered to score' is not a coverage score."""
    df = pd.DataFrame([{"aida_attention": True, "aida_interest": True,
                        "aida_desire": None, "aida_action": True}])
    assert pd.isna(recompute_derived(df, fd)["aida_coverage_score"].iat[0])


def test_persuasion_levers_are_counted_uniquely(fd):
    df = pd.DataFrame([{"persuasion_levers": "authority|liking|authority"}])
    assert recompute_derived(df, fd)["persuasion_lever_count"].iat[0] == 2


def test_no_levers_is_zero_not_missing(fd):
    df = pd.DataFrame([{"persuasion_levers": ""}])
    assert recompute_derived(df, fd)["persuasion_lever_count"].iat[0] == 0


def test_missing_levers_stays_missing(fd):
    df = pd.DataFrame([{"persuasion_levers": None}])
    assert pd.isna(recompute_derived(df, fd)["persuasion_lever_count"].iat[0])


def test_bands_follow_their_source(fd):
    df = pd.DataFrame([{"word_count": 90}, {"word_count": 900}])
    out = recompute_derived(df, fd)["word_count_band"].tolist()
    assert out == ["very_short", "long"]


# Audit finding (LOW): readability_band used to be filled by its
# own special-cased block with a locally-duplicated edge list - now it is just
# another BAND_RULES entry, same loop as word_count_band and friends.
def test_readability_band_follows_its_source(fd):
    df = pd.DataFrame([{"readability_score": 95}, {"readability_score": 10}])
    out = recompute_derived(df, fd)["readability_band"].tolist()
    assert out == ["very_easy", "very_hard"]


def test_has_animation_follows_the_asset_count(fd):
    df = pd.DataFrame([{"animated_asset_count": 0}, {"animated_asset_count": 3}])
    assert recompute_derived(df, fd)["has_animation"].tolist() == [False, True]


def test_a_stale_derived_value_is_corrected_not_preserved(fd):
    """The whole point: the source changed, so the derived value must follow."""
    df = pd.DataFrame([{"word_count": 900, "word_count_band": "very_short"}])
    assert recompute_derived(df, fd)["word_count_band"].iat[0] == "long"


def test_missing_sources_leave_the_derived_feature_alone(fd):
    df = pd.DataFrame([{"bank": "ing"}])
    out = recompute_derived(df, fd)
    assert "aida_coverage_score" not in out.columns or pd.isna(out["aida_coverage_score"]).all()
