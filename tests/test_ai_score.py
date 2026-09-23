"""Tests for the AI Score axes (New module).

Every formula is a plain mean of already-collected features, so these tests
check the arithmetic directly against small, hand-built rows - and, just as
important, that a bank with no data for an axis gets None rather than a
fabricated 0 (comparator/profiles.py's mean() follows the same rule).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import ai_score  # noqa: E402
from comparator.schema import format_list  # noqa: E402


def test_score_digital_is_the_mean_of_its_three_signals():
    rows = pd.DataFrame({
        "primary_cta_type": ["self_service_online", "self_service_online"],
        "fast_digital_onboarding_claim": [True, True],
        "mobile_first_design_signal": [True, True],
    })
    assert ai_score.score_digital(rows) == 10.0


def test_score_cross_sell_is_the_share_of_bundled_pages():
    rows = pd.DataFrame({"is_bundled_offer": [True, False]})
    assert ai_score.score_cross_sell(rows) == 5.0


def test_score_innovation_averages_animation_and_render_3d():
    rows = pd.DataFrame({
        "has_animation": [True, False],
        "dominant_image_type": ["render_3d", "photo"],
    })
    assert ai_score.score_innovation(rows) == 5.0


def test_score_simplicity_maps_the_modal_readability_band():
    rows = pd.DataFrame({"readability_band": ["easy", "easy", "medium"]})
    assert ai_score.score_simplicity(rows) == 7.5


def test_score_personalisation_counts_distinct_personas_out_of_the_taxonomy():
    rows = pd.DataFrame({"target_personas": [format_list(["family", "student"]), format_list(["family"])]})
    assert ai_score.score_personalisation(rows) == 2.5  # 2 distinct / 8 * 10


# --- None, never a fabricated 0 --------------------------------------------

def test_score_is_none_when_every_underlying_column_is_missing():
    rows = pd.DataFrame({"bank": ["ing", "ing"]})
    assert ai_score.score_digital(rows) is None
    assert ai_score.score_trust(rows) is None
    assert ai_score.score_cross_sell(rows) is None
    assert ai_score.score_personalisation(rows) is None
    assert ai_score.score_innovation(rows) is None
    assert ai_score.score_simplicity(rows) is None


def test_score_is_none_when_the_column_exists_but_is_entirely_null():
    rows = pd.DataFrame({"is_bundled_offer": pd.array([None, None], dtype="boolean")})
    assert ai_score.score_cross_sell(rows) is None


# Pins the fix for a real bug caught while writing this test - a
# categorical column with a null value used to compare as "condition false"
# (pandas: NaN == "x" is False, not NaN) instead of being excluded.
def test_a_missing_categorical_value_is_excluded_not_counted_as_false():
    rows = pd.DataFrame({"primary_cta_type": ["self_service_online", None]})
    # Only the non-null row counts; the null row must not drag this to 5.0.
    assert ai_score.score_digital(rows) == 10.0


def test_score_bank_and_score_all_cover_every_axis():
    df = pd.DataFrame({
        "bank": ["ing", "ing", "kbc"],
        "is_bundled_offer": [True, True, False],
    })
    bank_scores = ai_score.score_bank(df, "ing")
    assert set(bank_scores) == set(ai_score.AXES)

    all_scores = ai_score.score_all(df)
    assert set(all_scores) == {"ing", "kbc"}
    assert all(set(axes) == set(ai_score.AXES) for axes in all_scores.values())
