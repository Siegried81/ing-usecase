"""Tests for the semantic schema-freeze check (Plan risk P-04)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.dictionary import Feature, FeatureDictionary, load_dictionary  # noqa: E402
from comparator.freeze import DEFAULT_FROZEN, check, compare  # noqa: E402


def _feature(name: str, **overrides) -> Feature:
    base = dict(
        name=name, dimension="tone_messaging", definition="d", type="integer",
        extraction="automatic", source="html_text", comparability="cross_language",
        tier="core", required=True, nullable=False,
    )
    base.update(overrides)
    return Feature(**base)


def _dictionary(features: list[Feature]) -> FeatureDictionary:
    fd = load_dictionary()
    return FeatureDictionary(
        meta=fd.meta, dimensions=fd.dimensions, extraction_methods=fd.extraction_methods,
        comparability=fd.comparability, tiers=fd.tiers,
        features=[_feature("page_id", type="string", primary_key=True, dimension="provenance"), *features],
    )


def test_the_repo_currently_honours_the_freeze():
    assert check().ok, check().render()


def test_frozen_snapshot_is_itself_a_valid_dictionary():
    assert len(load_dictionary(DEFAULT_FROZEN)) > 0


def test_no_change_is_a_pass():
    fd = _dictionary([_feature("word_count")])
    assert compare(fd, fd).ok


def test_adding_a_feature_is_allowed():
    """The rule permits additions - this is what byte-equality gets wrong."""
    frozen = _dictionary([_feature("word_count")])
    current = _dictionary([_feature("word_count"), _feature("new_thing", tier="extended", required=False)])
    report = compare(frozen, current)
    assert report.ok
    assert any("new_thing" in a for a in report.additions)


def test_removing_a_feature_is_breaking():
    frozen = _dictionary([_feature("word_count"), _feature("doomed")])
    current = _dictionary([_feature("word_count")])
    report = compare(frozen, current)
    assert not report.ok
    assert any("doomed" in b for b in report.breaking)


def test_renaming_a_feature_is_breaking():
    """The case byte-equality cannot catch: update both files and it passes."""
    frozen = _dictionary([_feature("word_count")])
    current = _dictionary([_feature("wordcount")])
    report = compare(frozen, current)
    assert not report.ok
    assert any("word_count" in b and "removed or renamed" in b for b in report.breaking)


def test_changing_a_type_is_breaking():
    frozen = _dictionary([_feature("word_count", type="integer")])
    current = _dictionary([_feature("word_count", type="string")])
    assert not compare(frozen, current).ok


def test_removing_an_allowed_value_is_breaking():
    frozen = _dictionary([_feature("tone", type="categorical", values=["a", "b"])])
    current = _dictionary([_feature("tone", type="categorical", values=["a"])])
    report = compare(frozen, current)
    assert not report.ok
    assert any("allowed value(s) removed" in b for b in report.breaking)


def test_adding_an_allowed_value_is_fine():
    frozen = _dictionary([_feature("tone", type="categorical", values=["a"])])
    current = _dictionary([_feature("tone", type="categorical", values=["a", "b"])])
    report = compare(frozen, current)
    assert report.ok
    assert any("allowed value(s) added" in b for b in report.benign)


def test_narrowing_a_range_is_breaking():
    frozen = _dictionary([_feature("ratio", type="float", range=[0, 1])])
    current = _dictionary([_feature("ratio", type="float", range=[0, 0.5])])
    assert not compare(frozen, current).ok


# New test - freeze.py used to only check narrowing of an
# EXISTING range, so adding a range to a feature that had none before slipped
# through unchecked even though it is itself a narrowing (values already
# recorded outside the new range become invalid).
def test_adding_a_range_where_none_existed_is_breaking():
    frozen = _dictionary([_feature("count", type="integer")])
    current = _dictionary([_feature("count", type="integer", range=[0, 100])])
    report = compare(frozen, current)
    assert not report.ok
    assert any("range added" in b for b in report.breaking)


def test_demoting_a_core_feature_is_breaking():
    frozen = _dictionary([_feature("word_count", tier="core")])
    current = _dictionary([_feature("word_count", tier="extended", required=False)])
    assert not compare(frozen, current).ok


def test_promoting_to_core_is_allowed():
    frozen = _dictionary([_feature("word_count", tier="extended", required=False)])
    current = _dictionary([_feature("word_count", tier="core")])
    assert compare(frozen, current).ok


def test_tightening_nullability_is_breaking():
    frozen = _dictionary([_feature("word_count", nullable=True)])
    current = _dictionary([_feature("word_count", nullable=False)])
    assert not compare(frozen, current).ok


def test_report_raises_with_the_offending_feature_named():
    frozen = _dictionary([_feature("word_count"), _feature("doomed")])
    current = _dictionary([_feature("word_count")])
    with pytest.raises(ValueError, match="doomed"):
        compare(frozen, current).raise_if_failed()
