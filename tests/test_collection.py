"""Tests for the collection module - sieg 14/09, new module, new tests.

Network-touching functions (compliance.check_robots, scraper.scrape,
visual_features.extract_colours' requests.get, llm_extractor's provider
calls) are all tested with mocks - no real network access needed to run
these, same approach as the existing test_visual_features.py-style tests
in the code-skeleton review earlier this week.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.collection.compliance import (  # noqa: E402
    ComplianceCheck,
    ScrapingNotAllowed,
    assert_can_fetch,
    check_robots,
)
from comparator.collection.llm_extractor import (  # noqa: E402
    LLMExtractionError,
    ModelAssistedFields,
    extract_model_assisted,
)
from comparator.collection.scraper import extract  # noqa: E402
from comparator.collection.visual_features import extract_colours  # noqa: E402

SAMPLE_HTML = """
<html><head><title>ING - Savings - EN</title></head>
<body>
<img src="hero.jpg" alt="family at home">
<img src="icon.png" alt="">
<h1>Save with us</h1>
<p>Your money grows while you sleep. Open your account today, only until 30/09.
Rate: 2.75%</p>
<a href="#">Discover more</a>
<a href="#">Open an account</a>
<table><tr><td>compare</td></tr></table>
</body></html>
"""


# --- compliance --------------------------------------------------------------
def test_check_robots_allows_when_parser_says_yes():
    with patch("comparator.collection.compliance.RobotFileParser") as mock_cls:
        mock_cls.return_value.can_fetch.return_value = True
        result = check_robots("https://example.com/page")
    assert result.allowed is True


def test_check_robots_fails_closed_on_read_error():
    with patch("comparator.collection.compliance.RobotFileParser") as mock_cls:
        mock_cls.return_value.read.side_effect = ConnectionError("unreachable")
        result = check_robots("https://example.com/page")
    assert result.allowed is False
    assert "could not read" in result.reason


def test_assert_can_fetch_raises_when_disallowed():
    with patch("comparator.collection.compliance.check_robots") as mock_check:
        mock_check.return_value = ComplianceCheck(url="https://example.com/x", allowed=False, reason="disallowed")
        with pytest.raises(ScrapingNotAllowed):
            assert_can_fetch("https://example.com/x")


# --- scraper (deterministic extraction) --------------------------------------
def test_extract_word_and_sentence_counts():
    result = extract(SAMPLE_HTML, language="en")
    assert result["word_count"] > 0
    assert result["sentence_count"] >= 1


def test_extract_finds_the_rate():
    result = extract(SAMPLE_HTML, language="en")
    assert result["rate_shown"] is True
    assert result["rate_value_pct"] == pytest.approx(2.75)


def test_extract_detects_urgency_marker():
    result = extract(SAMPLE_HTML, language="en")
    assert result["urgency_marker_count"] >= 1  # "only until"


def test_extract_counts_ctas_by_keyword():
    result = extract(SAMPLE_HTML, language="en")
    assert result["cta_count"] == 2  # "Discover more", "Open an account"


def test_extract_detects_comparison_table():
    result = extract(SAMPLE_HTML, language="en")
    assert result["has_comparison_table"] is True


def test_second_person_ratio_is_share_of_pronouns_not_of_all_words():
    # sieg 15/09: was dividing by word_count, so a page saturated with
    # direct-address pronouns still scored ~0.02 and banded "rarely_direct"
    # regardless of actual tone - the denominator must be total personal
    # pronouns (second + first-person-plural), matching the dictionary's own
    # definition ("share of personal pronouns that address the reader").
    direct_html = (
        "<html><body><p>"
        + "Your money grows while you sleep, your way, for you and your family. "
        + ("filler word " * 100)
        + "</p></body></html>"
    )
    result = extract(direct_html, language="en")
    assert result["second_person_ratio"] > 0.5
    assert result["second_person_ratio_band"] == "mostly_direct"


def test_extract_alt_text_false_when_any_image_lacks_it():
    # the sample has one image with alt text and one without -> not all covered
    result = extract(SAMPLE_HTML, language="en")
    assert result["images_have_alt_text"] is False


def test_extract_meta_title():
    result = extract(SAMPLE_HTML, language="en")
    assert result["meta_title"] == "ING - Savings - EN"


def test_extract_leaves_render_dependent_fields_none():
    # sieg 14/09: these need a headless viewport - must stay None, not guessed
    result = extract(SAMPLE_HTML, language="en")
    for field in ("page_height_px", "hero_image_area_ratio", "total_image_area_ratio", "cta_contrast_ratio"):
        assert result[field] is None


def test_extract_readability_uses_the_right_formula_per_language():
    for lang, formula in (("nl", "flesch_douma_nl"), ("fr", "kandel_moles_fr"), ("en", "flesch_reading_ease_en")):
        result = extract(SAMPLE_HTML, language=lang)
        assert result["readability_formula"] == formula


# --- visual_features -----------------------------------------------------
def _fake_image_response(image: Image.Image) -> Mock:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    response = Mock()
    response.content = buffer.getvalue()
    response.raise_for_status = Mock()
    return response


def test_extract_colours_on_a_solid_image():
    solid_orange = Image.new("RGB", (100, 100), color=(255, 98, 0))
    with patch("comparator.collection.visual_features.requests.get", return_value=_fake_image_response(solid_orange)):
        result = extract_colours("https://example.com/hero.png", n_colours=1)
    assert result["dominant_colour_hex"] == "#ff6200"
    assert result["background_luminance"] is not None
    assert 0 <= result["background_luminance"] <= 1


def test_brand_colour_share_is_none_without_a_known_bank():
    solid_orange = Image.new("RGB", (100, 100), color=(255, 98, 0))
    with patch("comparator.collection.visual_features.requests.get", return_value=_fake_image_response(solid_orange)):
        result = extract_colours("https://example.com/hero.png", n_colours=1)
    assert result["brand_colour_share"] is None


def test_brand_colour_share_matches_the_banks_own_colour():
    ing_orange = Image.new("RGB", (100, 100), color=(255, 98, 0))  # #ff6200
    with patch("comparator.collection.visual_features.requests.get", return_value=_fake_image_response(ing_orange)):
        result = extract_colours("https://example.com/hero.png", bank="ing", n_colours=1)
    assert result["brand_colour_share"] == pytest.approx(1.0)


def test_brand_colour_share_is_low_when_the_image_is_not_the_brand_colour():
    # sieg 15/09: regression - used to report 1.0 here (the share of the most
    # frequent colour, mislabelled "brand"), for ANY bank, even ING (orange)
    # against a solid blue image.
    unrelated_blue = Image.new("RGB", (100, 100), color=(0, 0, 255))
    with patch("comparator.collection.visual_features.requests.get", return_value=_fake_image_response(unrelated_blue)):
        result = extract_colours("https://example.com/hero.png", bank="ing", n_colours=1)
    assert result["brand_colour_share"] == pytest.approx(0.0)


def test_extract_colours_handles_missing_url():
    result = extract_colours(None)
    assert result["dominant_colour_hex"] is None
    assert result["palette_hex"] == []


def test_extract_colours_handles_fetch_failure_gracefully():
    with patch("comparator.collection.visual_features.requests.get", side_effect=ConnectionError("nope")):
        result = extract_colours("https://example.com/broken.png")
    assert result["dominant_colour_hex"] is None  # must not raise


# --- llm_extractor ---------------------------------------------------------
_VALID_RESPONSE = {
    "primary_product": "Term account",
    "dominant_image_type": "photo",
    "people_present": True,
    "imagery_register": "lifestyle",
    "institutional_trust_signal_present": False,
    "youth_student_targeting": False,
    "secondary_bank_positioning": False,
    "expat_cross_border_targeting": False,
    "branch_network_cited_as_benefit": True,
    "first_time_investor_targeting": False,
    "senior_preretirement_targeting": False,
    "benefit_framing": "rational",
    "fab_level": "feature",
    "audience_segment": "retail",
    "is_bundled_offer": False,
    "cross_sell_delivery_model": "not_applicable",
    "rate_framing": "base_rate",
    "primary_cta_type": "self_service_online",
    "switching_framing": "not_applicable",
    "regulatory_disclosure_prominence": "prominent",
    "hidden_conditions_behind_free_claim": False,
    "esg_claim_specificity": "no_claim",
    "green_product_specific_benefit": False,
    "fast_digital_onboarding_claim": False,
}


def test_extract_model_assisted_validates_a_good_response():
    with patch("comparator.collection.llm_extractor._call_llm", return_value=__import__("json").dumps(_VALID_RESPONSE)):
        result = extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account")
    assert isinstance(result, ModelAssistedFields)
    assert result.primary_product == "Term account"


def test_extract_model_assisted_strips_markdown_fences():
    fenced = "```json\n" + __import__("json").dumps(_VALID_RESPONSE) + "\n```"
    with patch("comparator.collection.llm_extractor._call_llm", return_value=fenced):
        result = extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account")
    assert result.dominant_image_type == "photo"


def test_extract_model_assisted_retries_once_then_raises():
    with patch("comparator.collection.llm_extractor._call_llm", return_value="not json at all"):
        with pytest.raises(LLMExtractionError):
            extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account", retries=1)


def test_groq_tried_before_fallbacks(monkeypatch):
    # sieg 14/09: confirms the provider ORDER matches .env.example, not just
    # that "a" provider gets called.
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-openrouter-key")
    calls = []

    def fake_call(url, api_key, model, prompt):
        calls.append(url)
        if "groq" in url:
            raise __import__("requests").RequestException("groq down")
        return __import__("json").dumps(_VALID_RESPONSE)

    with patch("comparator.collection.llm_extractor._call_openai_compatible", side_effect=fake_call):
        extract_model_assisted("text", image_count=1, has_animation=False, product_family="term_account")

    assert any("groq" in c for c in calls), "groq must be tried first"
    assert any("openrouter" in c for c in calls), "fallback must be tried after groq fails"
