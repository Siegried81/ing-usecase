"""Tests for the rubric bridge (steph 16/09)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.rubric import (  # noqa: E402
    agreement,
    make_sheet,
    merge_scores,
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


def test_numeric_scores_are_averaged_across_raters(df, fd):
    merged = merge_scores(df, [_scored(df, fd, "a", 2, "card_grid"),
                               _scored(df, fd, "b", 4, "card_grid")], fd)
    scored = merged[merged["bank"] != "ing"]["formality_score"].dropna()
    assert (scored == 3.0).all()


def test_categorical_scores_take_the_majority(df, fd):
    merged = merge_scores(df, [_scored(df, fd, "a", 3, "card_grid"),
                               _scored(df, fd, "b", 3, "card_grid"),
                               _scored(df, fd, "c", 3, "long_form")], fd)
    scored = merged[merged["bank"] != "ing"]["layout_archetype"].dropna()
    assert (scored == "card_grid").all()


def test_unscored_pages_stay_empty_rather_than_being_invented(df, fd):
    """The excluded ING rows were never scored; they must not acquire a value."""
    merged = merge_scores(df, [_scored(df, fd, "a", 3, "card_grid")], fd)
    assert merged[merged["bank"] == "ing"]["formality_score"].isna().all()


def test_merging_nothing_changes_nothing(df, fd):
    pd.testing.assert_frame_equal(merge_scores(df, [], fd), df)


# --- agreement (NFR-05) ------------------------------------------------------
def test_identical_raters_agree_completely(df, fd):
    report = agreement([_scored(df, fd, "a", 3, "card_grid"),
                        _scored(df, fd, "b", 3, "card_grid")], fd)
    assert (report.table["agreement"] == 1.0).all()


def test_disagreement_is_measured_not_hidden(df, fd):
    report = agreement([_scored(df, fd, "a", 1, "card_grid"),
                        _scored(df, fd, "b", 5, "long_form")], fd)
    row = report.table.set_index("feature")
    assert row.loc["formality_score", "agreement"] == 0.0
    assert row.loc["layout_archetype", "agreement"] == 0.0


def test_numeric_agreement_tolerates_one_step(df, fd):
    """A 3 vs a 4 on a 1-5 scale is agreement for practical purposes."""
    report = agreement([_scored(df, fd, "a", 3, "card_grid"),
                        _scored(df, fd, "b", 4, "card_grid")], fd)
    assert report.table.set_index("feature").loc["formality_score", "agreement"] == 1.0


def test_one_rater_cannot_produce_an_agreement_number(df, fd):
    report = agreement([_scored(df, fd, "a", 3, "card_grid")], fd)
    assert report.table.empty
    assert "cannot be measured" in report.render()


def test_weak_agreement_is_called_out(df, fd):
    report = agreement([_scored(df, fd, "a", 1, "card_grid"),
                        _scored(df, fd, "b", 5, "long_form")], fd)
    assert "Weak agreement" in report.render()
