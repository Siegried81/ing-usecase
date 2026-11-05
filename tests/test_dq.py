"""Tests for the data-quality scorecard (comparator/dq.py).

The scorecard names and scores the DQ dimensions schema.validate() already
checks, and a gate fails the build when a gating one drops. These tests pin the
gating behaviour: which dimensions block, which only warn, and that accuracy is
never invented.

    python3 -m pytest tests/ -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.dq import DQReport, score  # noqa: E402


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


@pytest.fixture(scope="module")
def df(fd):
    return build_fixture(fd)


def _dim(report: DQReport, name: str):
    return next(d for d in report.dimensions if d.name == name)


# --- a clean dataset passes --------------------------------------------------
def test_clean_fixture_passes_every_gating_dimension(df, fd):
    report = score(df, fd)
    assert report.ok
    for name in ("completeness", "validity", "uniqueness"):
        assert _dim(report, name).status == "pass"


def test_all_six_dimensions_are_reported(df, fd):
    report = score(df, fd)
    assert [d.name for d in report.dimensions] == [
        "completeness", "validity", "uniqueness", "consistency", "timeliness", "accuracy",
    ]
    assert len(report.as_rows()) == 6


# --- accuracy is never invented ----------------------------------------------
def test_accuracy_is_always_not_measured(df, fd):
    accuracy = _dim(score(df, fd), "accuracy")
    assert accuracy.status == "not_measured"
    assert accuracy.score is None


# --- uniqueness gates on a duplicate key -------------------------------------
def test_duplicate_primary_key_fails_uniqueness(df, fd):
    pk = fd.primary_key
    broken = df.copy()
    broken.loc[broken.index[1], pk] = broken.loc[broken.index[0], pk]
    report = score(broken, fd)
    assert _dim(report, "uniqueness").status == "fail"
    assert not report.ok


# --- validity gates on an out-of-contract value ------------------------------
def test_value_outside_allowed_set_fails_validity(df, fd):
    categorical = next(
        f.name for f in fd.features
        if f.is_categorical and f.values and f.name in df.columns
    )
    broken = df.copy()
    broken.loc[broken.index[0], categorical] = "not-an-allowed-value"
    report = score(broken, fd)
    assert _dim(report, "validity").status == "fail"
    assert not report.ok


# --- completeness gates when required fields empty out -----------------------
def test_empty_required_fields_fail_completeness(df, fd):
    feats = [f for f in fd.features if f.name in df.columns and (f.required or not f.nullable)]
    # Empty out enough required columns to drop below the 0.95 fail threshold.
    n_to_empty = int(len(feats) * 0.1) + 1
    broken = df.copy()
    for f in feats[:n_to_empty]:
        broken[f.name] = pd.NA
    report = score(broken, fd)
    assert _dim(report, "completeness").status == "fail"
    assert not report.ok


# --- consistency warns on a fallback, fails with no majority -----------------
def test_single_model_is_consistent(df, fd):
    one = df.copy()
    one["extraction_model"] = "model-a"
    assert _dim(score(one, fd), "consistency").status == "pass"


def test_minority_fallback_warns_not_fails(df, fd):
    mostly = df.copy()
    models = ["model-a"] * len(mostly)
    models[-1] = "model-b"  # one row on a fallback
    mostly["extraction_model"] = models
    consistency = _dim(score(mostly, fd), "consistency")
    assert consistency.status == "warn"
    assert score(mostly, fd).ok  # a warning does not block


def test_no_majority_model_fails_consistency(df, fd):
    split = df.copy()
    half = len(split) // 2
    split["extraction_model"] = ["model-a"] * half + ["model-b"] * (len(split) - half)
    report = score(split, fd)
    assert _dim(report, "consistency").status == "fail"
    assert not report.ok


# --- timeliness: every row dated, or the dimension is honest about it --------
def test_missing_timestamps_fail_timeliness(df, fd):
    broken = df.copy()
    broken["captured_at"] = pd.NaT
    assert _dim(score(broken, fd), "timeliness").status == "fail"


def test_no_timestamp_column_is_not_measured(df, fd):
    without = df.drop(columns=["captured_at"])
    assert _dim(score(without, fd), "timeliness").status == "not_measured"


# --- the report behaves like the other reports in the repo -------------------
def test_raise_if_failed_raises_only_on_a_failure(df, fd):
    score(df, fd).raise_if_failed()  # clean: does not raise
    broken = df.copy()
    broken.loc[broken.index[1], fd.primary_key] = broken.loc[broken.index[0], fd.primary_key]
    with pytest.raises(ValueError, match="data quality below threshold"):
        score(broken, fd).raise_if_failed()


def test_render_lists_each_dimension(df, fd):
    rendered = score(df, fd).render()
    assert "Data-quality scorecard:" in rendered
    for name in ("completeness", "validity", "uniqueness", "consistency", "timeliness", "accuracy"):
        assert name in rendered
