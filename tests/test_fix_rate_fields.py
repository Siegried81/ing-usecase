"""Tests for the rate-field-only re-extraction script (sieg 20/09).

Pure parsing, no network/LLM call at all - nothing to mock.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("fix_rate_fields", ROOT / "scripts" / "fix_rate_fields.py")
fix_rate_fields = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix_rate_fields)

from comparator.dictionary import load_dictionary  # noqa: E402


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


def _base_row(html_path: str, **overrides) -> dict:
    row = {
        "page_id": "testbank_current_account_pack_fr_01", "bank": "testbank",
        "bank_category": "traditional", "product_family": "current_account_pack",
        "page_role": "campaign_landing", "url": "https://example.invalid/page",
        "language": "fr", "captured_at": "2026-09-15T09:00:00+00:00",
        "collection_method": "manual_capture", "robots_allowed": True,
        "snapshot_html_path": html_path, "screenshot_path": None,
        "data_source": "real", "rate_shown": True, "rate_value_pct": 100.0,
    }
    row.update(overrides)
    return row


def test_fix_rate_fields_skips_rows_with_no_html_on_disk(fd):
    df = pd.DataFrame([_base_row("data/raw/does/not/exist.html")])
    out = fix_rate_fields.fix_rate_fields(df, fd)
    assert bool(out.iloc[0]["rate_shown"]) is True
    assert out.iloc[0]["rate_value_pct"] == 100.0


def test_fix_rate_fields_clears_a_false_positive_rate(fd, tmp_path):
    html_path = tmp_path / "page.html"
    html_path.write_text("<html><body><p>100% en ligne, ouvrez votre compte.</p></body></html>", encoding="utf-8")
    df = pd.DataFrame([_base_row(str(html_path))])

    out = fix_rate_fields.fix_rate_fields(df, fd)

    assert bool(out.iloc[0]["rate_shown"]) is False
    assert pd.isna(out.iloc[0]["rate_value_pct"])


def test_fix_rate_fields_leaves_other_columns_untouched(fd, tmp_path):
    html_path = tmp_path / "page.html"
    html_path.write_text("<html><body><p>Taux: 2.5%</p></body></html>", encoding="utf-8")
    df = pd.DataFrame([_base_row(str(html_path), target_personas=["family"])])

    out = fix_rate_fields.fix_rate_fields(df, fd)

    assert list(out.iloc[0]["target_personas"]) == ["family"]
    assert out.iloc[0]["rate_value_pct"] == pytest.approx(2.5)
