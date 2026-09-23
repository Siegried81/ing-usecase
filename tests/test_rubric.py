"""Tests for the rubric bridge."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.rubric import (  # noqa: E402
    make_sheet,
    merge_scores,
    read_sheets,
    rubric_features,
    sheet_guide,
)


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


@pytest.fixture(scope="module")
def df(fd):
    data = build_fixture(fd)
    data["capture_quality"] = "ok"
    data.loc[data["bank"] == "ing", "capture_quality"] = "unusable"
    return data


# A rater's sheet gets hand-edited in Excel between sessions, and
# Excel's CSV export defaults to ";" under a French/Belgian locale - one real
# sheet has already flipped between "," and ";" more than once. read_sheets()
# must parse either without anyone needing to remember which.
def test_read_sheets_accepts_either_comma_or_semicolon(tmp_path):
    comma = tmp_path / "comma.csv"
    comma.write_text("rater,page_id,formality_score\nsiegried,ing_01,3\n", encoding="utf-8")
    semicolon = tmp_path / "semicolon.csv"
    semicolon.write_text("rater;page_id;formality_score\nsiegried;ing_01;3\n", encoding="utf-8")

    frames = read_sheets([comma, semicolon])
    for frame in frames:
        assert list(frame.columns) == ["rater", "page_id", "formality_score"]
        assert frame.loc[0, "page_id"] == "ing_01"


def test_sheet_has_a_column_for_every_rubric_feature(df, fd):
    sheet = make_sheet(df, fd, rater="stephane")
    for feature in rubric_features(fd):
        assert feature.name in sheet.columns


def test_sheet_starts_empty(df, fd):
    """A blank cell is honest. A pre-filled one invites rubber-stamping."""
    sheet = make_sheet(df, fd, rater="stephane")
    for feature in rubric_features(fd):
        assert sheet[feature.name].isna().all()


def test_sheet_carries_the_screenshot_so_a_rater_can_see_the_page(df, fd):
    assert "screenshot_path" in make_sheet(df, fd).columns


def test_unusable_captures_are_not_sent_for_scoring(df, fd):
    """Scoring the tone of a maintenance page wastes an afternoon."""
    sheet = make_sheet(df, fd, rater="x")
    assert "ing" not in set(sheet["bank"])
    assert "ing" in set(make_sheet(df, fd, rater="x", skip_unusable=False)["bank"])


def test_guide_documents_every_rubric_feature(fd):
    guide = sheet_guide(fd)
    for feature in rubric_features(fd):
        assert f"`{feature.name}`" in guide


def test_guide_lists_allowed_values_so_the_sheet_matches_the_validator(fd):
    guide = sheet_guide(fd)
    layout = fd["layout_archetype"]
    for value in layout.values:
        assert f"`{value}`" in guide


# --- merging -----------------------------------------------------------------
def _scored(df, fd, rater: str, formality: int, layout: str) -> pd.DataFrame:
    sheet = make_sheet(df, fd, rater=rater)
    sheet["formality_score"] = formality
    sheet["layout_archetype"] = layout
    return sheet


def test_unscored_pages_stay_empty_rather_than_being_invented(df, fd):
    """The excluded ING rows were never scored; they must not acquire a value."""
    merged = merge_scores(df, [_scored(df, fd, "a", 3, "card_grid")], fd)
    assert merged[merged["bank"] == "ing"]["formality_score"].isna().all()


def test_merging_nothing_changes_nothing(df, fd):
    pd.testing.assert_frame_equal(merge_scores(df, [], fd), df)


# --- one judged sheet --------------------------------------------
# The project runs on a single rater, so the merge no longer reconciles
# anything. These pin the behaviour that replaced averaging and majority vote.
def test_a_single_sheet_is_taken_at_face_value(df, fd):
    """No averaging, no rounding: the number the person wrote is the number
    that reaches the dataset."""
    merged = merge_scores(df, [_scored(df, fd, "siegried", 2, "card_grid")], fd)
    scored = merged[merged["bank"] != "ing"]
    assert (scored["formality_score"].dropna() == 2).all()
    assert (scored["layout_archetype"].dropna() == "card_grid").all()


def test_a_second_row_for_one_page_is_ignored_not_blended(df, fd):
    """With the agreement layer gone, averaging two values would bury a
    disagreement instead of reporting it. The first value wins and the second
    is dropped, which is at least inspectable."""
    first = _scored(df, fd, "siegried", 2, "card_grid")
    second = _scored(df, fd, "siegried", 4, "long_form")
    merged = merge_scores(df, [pd.concat([first, second], ignore_index=True)], fd)
    scored = merged[merged["bank"] != "ing"]["formality_score"].dropna()
    assert set(scored.unique()) <= {2}


def test_an_integer_scale_stays_an_integer(df, fd):
    """The dictionary declares these as integers; a float would fail to load."""
    merged = merge_scores(df, [_scored(df, fd, "siegried", 3, "card_grid")], fd)
    values = merged["formality_score"].dropna()
    assert all(float(v).is_integer() for v in values)


def test_the_guide_states_the_single_judge_scope(fd):
    """A rater must not be told to score independently of a second rater who
    does not exist, and the deliverable must not imply a measure it lacks."""
    guide = sheet_guide(fd)
    assert "One named person scores every page" in guide
    assert "single-judge bias" in guide
    for gone in ("Cohen", "kappa", "disagreement is measured"):
        assert gone not in guide
