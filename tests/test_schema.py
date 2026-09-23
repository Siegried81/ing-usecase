"""Tests for the dictionary and the dataset contract.

The dataset schema is what three people build against in parallel. These tests
exist so a breaking change to it fails here rather than on day 6.

    python3 -m pytest tests/ -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.dictionary import REPO_ROOT, load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.schema import coerce_types, format_list, parse_list, validate  # noqa: E402


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


@pytest.fixture(scope="module")
def df(fd):
    return build_fixture(fd)


# --- the dictionary itself ---------------------------------------------------
def test_dictionary_loads_and_is_consistent(fd):
    assert len(fd) > 0
    assert fd.primary_key == "page_id"


def test_every_feature_has_a_definition(fd):
    missing = [f.name for f in fd.features if not f.definition.strip()]
    assert not missing, f"features without a definition: {missing}"


def test_categorical_features_declare_their_values(fd):
    missing = [f.name for f in fd.select(kind="categorical") if not f.values]
    assert not missing


def test_required_features_are_core(fd):
    assert all(f.tier == "core" for f in fd.features if f.required)


# Config/feature_dictionary.yaml is the single source of truth
# (CLAUDE.md) - this guards it against silent drift. Any change must also
# update the frozen copy on purpose, in the same PR, so nobody's edit to a
# type/tier/comparability slips in unreviewed.
def test_dictionary_matches_frozen_snapshot():
    current = (REPO_ROOT / "config" / "feature_dictionary.yaml").read_text()
    frozen = (REPO_ROOT / "config" / "feature_dictionary.frozen.yaml").read_text()
    assert current == frozen, (
        "config/feature_dictionary.yaml differs from config/feature_dictionary.frozen.yaml. "
        "If the change is intentional, update the frozen copy too."
    )


def test_judgement_based_features_are_identifiable(fd):
    """Rubric and model-assisted values carry a trust caveat, so the code must be
    able to tell them apart from deterministic ones."""
    judged = fd.select(extraction="rubric") + fd.select(extraction="model_assisted")
    assert judged
    assert all(f.is_judgement_based for f in judged)


# --- list round-tripping -----------------------------------------------------
@pytest.mark.parametrize("values", [[], ["text"], ["text", "icons", "imagery"]])
def test_list_columns_round_trip(values):
    assert parse_list(format_list(values)) == values


def test_parse_list_handles_missing(fd):
    assert parse_list(None) == []
    assert parse_list(float("nan")) == []
    assert parse_list("") == []


# --- the fixture satisfies the contract --------------------------------------
def test_fixture_passes_validation(df, fd):
    report = validate(df, fd, tier="core")
    assert report.ok, report.render()


def test_fixture_covers_both_categories(df):
    assert set(df["bank_category"]) == {"traditional", "challenger"}


def test_fixture_is_labelled_synthetic(df):
    assert (df["data_source"] == "synthetic_fixture").all()


def test_fixture_is_deterministic(fd):
    a = build_fixture(fd, seed=7)
    b = build_fixture(fd, seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_fixture_readability_formula_matches_language(fd):
    # A fixture must report the formula for its own language - claiming Dutch
    # scoring on a fr or en fixture would misstate how it was scored.
    expected = {"nl": "flesch_douma_nl", "fr": "kandel_moles_fr", "en": "flesch_reading_ease_en"}
    for lang, formula in expected.items():
        df = build_fixture(fd, language=lang, pages_per_bank=1)
        assert set(df["readability_formula"]) == {formula}, lang


# --- the validator actually catches things -----------------------------------
def test_missing_required_column_is_an_error(df, fd):
    report = validate(df.drop(columns=["word_count"]), fd, tier="core")
    assert not report.ok
    assert any("missing required columns" in e for e in report.errors)


def test_unknown_column_is_an_error(df, fd):
    broken = df.copy()
    broken["vibe_score"] = 1
    report = validate(broken, fd, tier="core")
    assert any("absent from the feature dictionary" in e for e in report.errors)


def test_out_of_range_value_is_an_error(df, fd):
    broken = df.copy()
    broken.loc[0, "second_person_ratio"] = 1.4  # declared range is [0, 1]
    report = validate(broken, fd, tier="core")
    assert any("above the maximum" in e for e in report.errors)


def test_bad_categorical_value_is_an_error(df, fd):
    broken = df.copy()
    broken.loc[0, "bank_category"] = "cooperative"
    report = validate(broken, fd, tier="core")
    assert any("outside the allowed set" in e for e in report.errors)


def test_duplicate_primary_key_is_an_error(df, fd):
    broken = pd.concat([df, df.head(1)], ignore_index=True)
    report = validate(broken, fd, tier="core")
    assert any("duplicate page_id" in e for e in report.errors)


def test_robots_disallowed_row_is_a_compliance_error(df, fd):
    """LC-01: a row collected from a disallowed path must never pass validation."""
    broken = df.copy()
    broken.loc[0, "robots_allowed"] = False
    report = validate(broken, fd, tier="core")
    assert any(e.startswith("COMPLIANCE") for e in report.errors)


def test_synthetic_rows_raise_a_warning(df, fd):
    report = validate(df, fd, tier="core")
    assert any("synthetic fixture" in w for w in report.warnings)


def test_coercion_survives_a_csv_round_trip(df, fd, tmp_path):
    path = tmp_path / "roundtrip.csv"
    df.to_csv(path, index=False)
    back = coerce_types(pd.read_csv(path), fd)
    assert validate(back, fd, tier="core").ok
    assert back["has_animation"].dtype == "boolean"
    assert back["word_count"].dtype == "Int64"


def test_timestamps_of_different_iso_precision_parse(fd):
    """The live path writes microseconds, the manual-capture
    importer did not, and a column mixing the two coerced the odd ones to NaT -
    captured_at then failed validation as missing on rows that had one."""
    df = pd.DataFrame({
        "captured_at": ["2026-09-16T13:42:21.253554+00:00", "2026-09-16T12:42:30+00:00"],
    })
    out = coerce_types(df, fd)
    assert out["captured_at"].notna().all()
