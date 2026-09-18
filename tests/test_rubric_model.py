"""Tests for model rubric scoring (steph 16/09). No test calls a model."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.rubric import rubric_features  # noqa: E402
from comparator.rubric_model import (  # noqa: E402
    TEXT_SCORABLE,
    VISION_ONLY,
    build_prompt,
)


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


def test_every_rubric_feature_is_either_scorable_or_explicitly_vision_only(fd):
    """No feature may fall between the two lists and be silently forgotten."""
    covered = set(TEXT_SCORABLE) | set(VISION_ONLY)
    assert {f.name for f in rubric_features(fd)} == covered


def test_the_two_lists_do_not_overlap():
    assert not set(TEXT_SCORABLE) & set(VISION_ONLY)


def test_visual_features_are_not_scored_from_text(fd):
    """The pinned model has no vision, and the extractor only ever sends text.
    Scoring a layout from words would be guessing from the wrong evidence."""
    prompt = build_prompt(fd)
    for name in VISION_ONLY:
        assert f'"{name}"' not in prompt


def test_the_prompt_is_built_from_the_dictionary(fd):
    """So the rubric the model is given and the rubric a human reads cannot drift."""
    prompt = build_prompt(fd)
    for name in TEXT_SCORABLE:
        assert f'"{name}"' in prompt
    for level_text in fd["formality_score"].rubric.values():
        assert " ".join(str(level_text).split())[:30] in prompt


def test_the_split_matches_what_the_dictionary_says_each_feature_is_judged_from(fd):
    """steph 18/09, the regression this module actually had.

    TEXT_SCORABLE was hand-written and 8 of its 9 entries were declared in the
    dictionary as `source: screenshot`. The model answered anyway - confidently,
    from evidence that cannot settle the question - and against Siegried's
    scoring those eight came back at chance (value_prop_clarity ranked the pages
    almost exactly opposite, Spearman -0.77). The one text-sourced feature,
    formality_score, reached kappa 0.42.

    So the split is derived, and this asserts it stays derived.
    """
    for name in TEXT_SCORABLE:
        assert fd[name].source == "html_text", (
            f"{name} is declared as judged from {fd[name].source}, so the model must not "
            "score it from text"
        )
    for name in VISION_ONLY:
        assert fd[name].source != "html_text"


def test_a_screenshot_sourced_feature_never_reaches_the_prompt(fd):
    prompt = build_prompt(fd)
    for feature in rubric_features(fd):
        if feature.source != "html_text":
            assert f'"{feature.name}"' not in prompt


def test_allowed_values_are_listed_for_any_categorical_that_is_text_sourced(fd):
    prompt = build_prompt(fd)
    for name in TEXT_SCORABLE:
        feature = fd[name]
        if feature.values:
            for value in feature.values:
                assert f'"{value}"' in prompt


def test_the_prompt_demands_the_same_standard_for_every_bank(fd):
    assert "SAME standard to every bank" in build_prompt(fd)
