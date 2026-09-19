"""Tests for the model-assisted re-extraction script (sieg 19/09).

No real HTTP/LLM call - _call_llm is mocked, per this repo's rule against
real network calls in tests.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("reextract_model_fields", ROOT / "scripts" / "reextract_model_fields.py")
reextract_model_fields = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reextract_model_fields)

from comparator.dictionary import load_dictionary  # noqa: E402

_VALID_RESPONSE = {
    "primary_product": "Compte courant", "dominant_image_type": "photo", "people_present": True,
    "imagery_register": "lifestyle", "institutional_trust_signal_present": False,
    "youth_student_targeting": False, "secondary_bank_positioning": False,
    "expat_cross_border_targeting": False, "branch_network_cited_as_benefit": False,
    "first_time_investor_targeting": False, "senior_preretirement_targeting": False,
    "benefit_framing": "rational", "fab_level": "feature", "audience_segment": "retail",
    "is_bundled_offer": True, "cross_sell_delivery_model": "internal_advisor_led",
    "rate_framing": "base_rate", "primary_cta_type": "self_service_online",
    "switching_framing": "not_applicable", "regulatory_disclosure_prominence": "not_applicable",
    "hidden_conditions_behind_free_claim": False, "esg_claim_specificity": "no_claim",
    "green_product_specific_benefit": False, "fast_digital_onboarding_claim": True,
    "target_personas": ["family", "mass_market"], "cross_sold_products": ["savings_account"],
}


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


def _base_row(html_path: str) -> dict:
    return {
        "page_id": "testbank_current_account_pack_fr_01", "bank": "testbank",
        "bank_category": "traditional", "product_family": "current_account_pack",
        "page_role": "campaign_landing", "url": "https://example.invalid/page",
        "language": "fr", "captured_at": "2026-09-15T09:00:00+00:00",
        "collection_method": "manual_capture", "robots_allowed": True,
        "snapshot_html_path": html_path, "screenshot_path": None,
        "data_source": "real",
    }


def test_reextract_skips_rows_with_no_html_on_disk(fd):
    df = pd.DataFrame([_base_row("data/raw/does/not/exist.html")])
    with patch("comparator.collection.llm_extractor._call_llm") as mock_llm:
        out = reextract_model_fields.reextract(df, fd)
    mock_llm.assert_not_called()
    assert "target_personas" not in out.columns or pd.isna(out.iloc[0].get("target_personas"))


def test_reextract_fills_target_personas_and_cross_sold_products(fd, tmp_path):
    html_path = tmp_path / "page.html"
    html_path.write_text("<html><body><p>Compte courant pour toute la famille.</p></body></html>", encoding="utf-8")
    df = pd.DataFrame([_base_row(str(html_path))])

    with patch("comparator.collection.llm_extractor._call_llm", return_value=(json.dumps(_VALID_RESPONSE), "test/model")):
        out = reextract_model_fields.reextract(df, fd)

    assert list(out.iloc[0]["target_personas"]) == ["family", "mass_market"]
    assert list(out.iloc[0]["cross_sold_products"]) == ["savings_account"]
    assert out.iloc[0]["extraction_model"] == "test/model"


def test_reextract_leaves_the_row_unchanged_on_llm_failure(fd, tmp_path):
    html_path = tmp_path / "page.html"
    html_path.write_text("<html><body><p>Compte courant.</p></body></html>", encoding="utf-8")
    df = pd.DataFrame([_base_row(str(html_path))])

    with patch("comparator.collection.llm_extractor._call_llm", return_value=("not json", "test/model")):
        out = reextract_model_fields.reextract(df, fd)

    assert out.iloc[0]["page_id"] == "testbank_current_account_pack_fr_01"
    assert "target_personas" not in out.columns or pd.isna(out.iloc[0].get("target_personas"))
