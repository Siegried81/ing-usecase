"""Tests for src/comparator/generation_guardrails.py - sieg 15/09, new module, new tests.

No network calls involved - the guardrail check is pure logic over a dict, there
is nothing here to mock.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.generation_guardrails import check_generated_campaign  # noqa: E402

_SAFE_ROW = {
    "data_source": "llm_generated",
    "disclaimer_present": True,
    "regulatory_disclosure_prominence": "prominent",
}


def test_a_compliant_row_passes():
    report = check_generated_campaign(_SAFE_ROW)
    assert report.ok
    assert report.violations == []


def test_unlabelled_row_is_a_violation():
    row = {**_SAFE_ROW, "data_source": "real"}
    report = check_generated_campaign(row)
    assert not report.ok
    assert any("llm_generated" in v for v in report.violations)


def test_missing_disclaimer_is_a_violation():
    row = {**_SAFE_ROW, "disclaimer_present": False}
    report = check_generated_campaign(row)
    assert not report.ok
    assert any("disclaimer_present" in v for v in report.violations)


def test_absent_regulatory_disclosure_is_a_violation():
    row = {**_SAFE_ROW, "regulatory_disclosure_prominence": "absent"}
    report = check_generated_campaign(row)
    assert not report.ok
    assert any("regulatory_disclosure_prominence" in v for v in report.violations)


def test_multiple_violations_are_all_reported():
    report = check_generated_campaign({})
    assert not report.ok
    assert len(report.violations) == 2  # data_source and disclaimer_present; prominence defaults to None, not "absent"
