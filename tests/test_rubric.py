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


# -----------------------------------------------------------------------------
# sieg 16/09: Cohen's kappa - each case below is hand-computed in the
# function's own docstring reasoning, not just "some plausible number".
def _pair_sheet(rater: str, page_ids: list[str], feature: str, values: list) -> pd.DataFrame:
    return pd.DataFrame({"page_id": page_ids, "rater": rater, feature: values})


def test_kappa_is_one_for_perfect_agreement():
    from comparator.rubric import kappa_agreement

    pages = ["p1", "p2", "p3", "p4", "p5"]
    a = _pair_sheet("a", pages, "formality_score", [1, 2, 3, 4, 5])
    b = _pair_sheet("b", pages, "formality_score", [1, 2, 3, 4, 5])
    report = kappa_agreement([a, b])
    row = report.table.set_index("feature").loc["formality_score"]
    assert row["kappa"] == 1.0


def test_kappa_is_zero_at_chance_level():
    """Hand-computed: A/A, A/B, B/A, B/B with matched 50/50 marginals gives
    exactly 0 - observed disagreement equals what the marginals predict."""
    from comparator.rubric import kappa_agreement

    pages = ["p1", "p2", "p3", "p4"]
    a = _pair_sheet("a", pages, "layout_archetype", ["hero_stacked", "hero_stacked", "long_form", "long_form"])
    b = _pair_sheet("b", pages, "layout_archetype", ["hero_stacked", "long_form", "hero_stacked", "long_form"])
    report = kappa_agreement([a, b])
    row = report.table.set_index("feature").loc["layout_archetype"]
    assert row["kappa"] == 0.0


def test_kappa_is_negative_for_systematic_opposite_disagreement():
    """Hand-computed: raters always pick the OTHER category - worse than
    chance, kappa = -1 exactly, given matched 50/50 marginals."""
    from comparator.rubric import kappa_agreement

    pages = ["p1", "p2", "p3", "p4"]
    a = _pair_sheet("a", pages, "layout_archetype", ["hero_stacked", "hero_stacked", "long_form", "long_form"])
    b = _pair_sheet("b", pages, "layout_archetype", ["long_form", "long_form", "hero_stacked", "hero_stacked"])
    report = kappa_agreement([a, b])
    row = report.table.set_index("feature").loc["layout_archetype"]
    assert row["kappa"] == -1.0


def test_kappa_needs_at_least_two_raters():
    from comparator.rubric import kappa_agreement

    report = kappa_agreement([_pair_sheet("a", ["p1", "p2"], "formality_score", [1, 2])])
    assert report.table.empty
    assert "Not enough" in report.render()


def test_kappa_covers_every_rater_pair_not_just_the_first_two():
    """The model is just a third rater - same function, no special case."""
    from comparator.rubric import kappa_agreement

    pages = ["p1", "p2", "p3", "p4"]
    a = _pair_sheet("siegried", pages, "layout_archetype", ["hero_stacked", "hero_stacked", "long_form", "long_form"])
    b = _pair_sheet("stephane", pages, "layout_archetype", ["hero_stacked", "hero_stacked", "long_form", "long_form"])
    c = _pair_sheet("model", pages, "layout_archetype", ["hero_stacked", "long_form", "hero_stacked", "long_form"])
    report = kappa_agreement([a, b, c])
    pairs = {frozenset(p.split(" vs ")) for p in report.table["raters"]}
    assert pairs == {
        frozenset({"siegried", "stephane"}),
        frozenset({"siegried", "model"}),
        frozenset({"stephane", "model"}),
    }


def test_kappa_flags_weak_pairs_in_render():
    from comparator.rubric import kappa_agreement

    pages = ["p1", "p2", "p3", "p4"]
    a = _pair_sheet("a", pages, "layout_archetype", ["hero_stacked", "hero_stacked", "long_form", "long_form"])
    b = _pair_sheet("b", pages, "layout_archetype", ["long_form", "long_form", "hero_stacked", "hero_stacked"])
    assert "Below 0.4" in kappa_agreement([a, b]).render()


def test_kappa_is_undefined_not_fabricated_when_every_rater_agrees_on_one_value():
    """Zero variance means kappa's denominator is 0 - reporting 1.0 here
    would be a fabricated "perfect agreement" from a case that proves nothing."""
    from comparator.rubric import kappa_agreement

    pages = ["p1", "p2", "p3"]
    a = _pair_sheet("a", pages, "formality_score", [3, 3, 3])
    b = _pair_sheet("b", pages, "formality_score", [3, 3, 3])
    report = kappa_agreement([a, b])
    assert report.table.empty


def test_day5_table_reports_chance_corrected_agreement_too(df, fd):
    """steph 16/09: raw % agreement can look fine while being close to chance -
    Sieg's own note on kappa. The deck table must not carry only the flattering
    half of the story."""
    from comparator.rubric import disagreement_table

    text = disagreement_table([_scored(df, fd, "a", 3, "card_grid"),
                               _scored(df, fd, "b", 4, "long_form")], fd)
    assert "Inter-rater agreement" in text
    # Either the kappa table, or kappa's own explanation of why it cannot be
    # computed - both are the chance-corrected half being reported rather than
    # quietly omitted. (These fixture raters are constant, so kappa is undefined.)
    assert "Cohen's kappa" in text or "compute kappa" in text


def test_day5_table_shows_the_kappa_table_when_it_can_be_computed(df, fd):
    from comparator.rubric import disagreement_table, make_sheet

    def varied(rater, scores):
        sheet = make_sheet(df, fd, rater=rater)
        sheet["formality_score"] = scores[: len(sheet)]
        return sheet

    n = len(make_sheet(df, fd, rater="a"))
    text = disagreement_table([varied("a", [1, 5] * n), varied("b", [1, 4] * n)], fd)
    assert "Cohen's kappa" in text
