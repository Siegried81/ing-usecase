"""Tests for the collection module.

Network-touching functions (compliance.check_robots, scraper.scrape,
visual_features.extract_colours' requests.get, llm_extractor's provider
calls) are all tested with mocks - no real network access needed to run
these, same approach as the existing test_visual_features.py-style tests
elsewhere in this suite.
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
    USER_AGENT,
    ComplianceCheck,
    ScrapingNotAllowed,
    assert_can_fetch,
    check_robots,
    clear_cache,
)
from comparator.collection.llm_extractor import (  # noqa: E402
    LLMExtractionError,
    ModelAssistedFields,
    extract_model_assisted,
    extract_model_assisted_with_provenance,
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
def _robots_response(status: int = 200, text: str = ""):
    """Minimal stand-in for the requests.Response compliance.py reads."""
    from unittest.mock import MagicMock

    response = MagicMock()
    response.status_code = status
    response.text = text
    response.raise_for_status.side_effect = (
        None if status < 400 else __import__("requests").HTTPError(f"{status}")
    )
    return response


def test_check_robots_fails_closed_on_read_error():
    # compliance.py fetches robots.txt with requests - the same stack as the
    # page fetch - so that is what this patches, not RobotFileParser.read().
    # The assertion is the point: an unreadable robots.txt must fail closed.
    clear_cache()
    with patch("comparator.collection.compliance.requests.get",
               side_effect=ConnectionError("unreachable")):
        result = check_robots("https://example.com/page")
    assert result.allowed is False
    assert "could not read" in result.reason


def test_robots_is_read_with_the_same_http_stack_that_fetches_the_page():
    """If we can fetch the page, we must be able to read its rules."""
    clear_cache()
    with patch("comparator.collection.compliance.requests.get",
               return_value=_robots_response(200, "User-agent: *\nAllow: /")) as get:
        assert check_robots("https://example.com/page").allowed is True
    assert get.call_args.kwargs["headers"]["User-Agent"] == USER_AGENT


def test_disallow_rule_is_honoured():
    clear_cache()
    with patch("comparator.collection.compliance.requests.get",
               return_value=_robots_response(200, "User-agent: *\nDisallow: /private/")):
        assert check_robots("https://example.com/private/x").allowed is False
        assert check_robots("https://example.com/public/x").allowed is True


def test_missing_robots_means_nothing_is_disallowed():
    """404 = the site publishes no rules. Standard-library semantics, preserved."""
    clear_cache()
    with patch("comparator.collection.compliance.requests.get",
               return_value=_robots_response(404)):
        assert check_robots("https://example.com/page").allowed is True


def test_auth_required_on_robots_means_the_whole_site_is_off_limits():
    clear_cache()
    for status in (401, 403):
        clear_cache()
        with patch("comparator.collection.compliance.requests.get",
                   return_value=_robots_response(status)):
            assert check_robots("https://example.com/page").allowed is False


def test_server_error_on_robots_fails_closed():
    clear_cache()
    with patch("comparator.collection.compliance.requests.get",
               return_value=_robots_response(503)):
        assert check_robots("https://example.com/page").allowed is False


def test_robots_is_fetched_once_per_domain():
    """We check before every page AND every hero image - re-downloading the same
    robots.txt a dozen times is rude to the sites we are asking (LC-05)."""
    clear_cache()
    with patch("comparator.collection.compliance.requests.get",
               return_value=_robots_response(200, "User-agent: *\nAllow: /")) as get:
        for i in range(5):
            check_robots(f"https://example.com/page-{i}")
    assert get.call_count == 1


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


def test_extract_ignores_percentages_that_are_not_a_rate():
    # Regression test for the "100% online" false-positive bug -
    # a bare percentage with no rate keyword nearby must not be reported as a rate.
    html = "<html><body><p>100% online, open your account in minutes.</p></body></html>"
    result = extract(html, language="en")
    assert result["rate_shown"] is False
    assert result["rate_value_pct"] is None


def test_extract_detects_urgency_marker():
    result = extract(SAMPLE_HTML, language="en")
    assert result["urgency_marker_count"] >= 1  # "only until"


def test_urgency_counts_a_dated_deadline_with_no_listed_term():
    # The ING pack offer's own phrasing: the deadline is in the date, and none
    # of the _URGENCY_MARKERS terms appear, so a term list alone scores 0.
    html = ("<html><body><p>Déposez 50 € et recevez 50 €. Si vous ouvrez votre premier "
            "pack avant le 11/10/2026 inclus.</p></body></html>")
    assert extract(html, language="fr")["urgency_marker_count"] == 1


def test_urgency_ignores_a_deadline_preposition_with_no_date():
    # "before" on its own is ordinary prose, not a deadline.
    html = "<html><body><p>Read the terms before you open an account with us.</p></body></html>"
    assert extract(html, language="en")["urgency_marker_count"] == 0


def test_urgency_counts_a_listed_term_that_is_also_a_preposition_once():
    # "jusqu'au" is both an _URGENCY_MARKERS term and a deadline preposition;
    # counting it twice would inflate exactly the pages the term list already
    # handled.
    html = "<html><body><p>Offre valable jusqu'au 13/10/2026.</p></body></html>"
    assert extract(html, language="fr")["urgency_marker_count"] == 1


def test_urgency_counts_a_spelled_out_date():
    html = "<html><body><p>Aanbod geldig tot 11 oktober 2026.</p></body></html>"
    assert extract(html, language="nl")["urgency_marker_count"] == 1


def test_extract_counts_ctas_by_keyword():
    result = extract(SAMPLE_HTML, language="en")
    assert result["cta_count"] == 2  # "Discover more", "Open an account"


def test_responsive_picture_sources_are_not_animation():
    # A bare <source> must not count as motion: <picture><source srcset> is a
    # STATIC responsive image, standard on every modern site. Measured on 16
    # real captures, 217 of 219 <source> tags were inside <picture>. Deck claim
    # H3 ("ING is the only traditional bank using animation") is tested against
    # exactly this column.
    html = """<html><body>
    <picture>
      <source srcset="hero.avif" type="image/avif">
      <source srcset="hero.webp" type="image/webp">
      <img src="hero.jpg" alt="hero">
    </picture>
    </body></html>"""
    result = extract(html, language="en")
    assert result["has_animation"] is False
    assert result["animated_asset_count"] == 0


def test_video_still_counts_as_animation():
    # The <video> parent fires, so a <video><source> is still detected -
    # only the BARE <source> case changed.
    html = """<html><body>
    <video autoplay loop><source src="clip.mp4" type="video/mp4"></video>
    </body></html>"""
    result = extract(html, language="en")
    assert result["has_animation"] is True


def test_css_keyframes_still_count_as_animation():
    # Team decision: CSS motion stays in scope. The dictionary
    # defines animated_asset_count as "GIF, video, Lottie, CSS keyframe
    # animation", so the detector must keep matching it or the code and the
    # contract disagree. Pinned as a test so the <picture> fix above cannot be
    # widened into dropping CSS by accident.
    html = """<html><head><style>
    @keyframes fade { from { opacity: 0 } to { opacity: 1 } }
    </style></head><body><p>Texte.</p></body></html>"""
    result = extract(html, language="en")
    assert result["has_animation"] is True


def test_extract_counts_french_imperative_ctas():
    # Verified live on kbc.be: real buttons say "Ouvrez un compte à vue"
    # (imperative), not "ouvrir" (infinitive). With infinitives alone in
    # _CTA_KEYWORDS the page scores cta_count=0.
    html = """<html><body><p>Texte.</p>
    <a href="#">Ouvrez un compte à vue</a>
    <a href="#">Découvrez nos offres</a>
    </body></html>"""
    result = extract(html, language="fr")
    assert result["cta_count"] == 2


def test_cta_count_deduplicates_repeated_links():
    # The same label+href repeated is one call to action, not four.
    # This is the shape Crelan's product lists had ("En savoir plus sur X" x4).
    html = """<html><body>
    <a href="/habitation">En savoir plus sur habitation</a>
    <a href="/habitation">En savoir plus sur habitation</a>
    <a href="/habitation">En savoir plus sur habitation</a>
    <a href="/mobilite">En savoir plus sur mobilite</a>
    </body></html>"""
    result = extract(html, language="fr")
    assert result["cta_count"] == 2


def test_cta_count_ignores_navigation_and_footer_chrome():
    # slide 12's "ING is behind on calls to action" came from counting menu and
    # footer link lists. A body CTA still counts; chrome does not.
    html = """<html><body>
    <nav><a href="/a">Ouvrir un compte</a><a href="/b">En savoir plus</a></nav>
    <header><a href="/c">Ouvrir un compte</a></header>
    <p>Texte.</p>
    <a href="/d">Ouvrir un compte</a>
    <footer><a href="/e">En savoir plus sur habitation</a><a href="/f">En savoir plus</a></footer>
    </body></html>"""
    result = extract(html, language="fr")
    # only the body CTA and the header CTA survive (header is not chrome: a
    # top-of-page CTA is something a visitor clicks)
    assert result["cta_count"] == 2


def test_cta_count_ignores_hidden_links():
    html = """<html><body>
    <a href="/a" aria-hidden="true">Ouvrir un compte</a>
    <a href="/b" hidden>En savoir plus</a>
    <a href="/c">Ouvrir un compte</a>
    </body></html>"""
    result = extract(html, language="fr")
    assert result["cta_count"] == 1


def test_extract_detects_comparison_table():
    result = extract(SAMPLE_HTML, language="en")
    assert result["has_comparison_table"] is True


def test_second_person_ratio_is_share_of_pronouns_not_of_all_words():
    # The denominator is total personal pronouns (second + first-person-plural),
    # matching the dictionary's definition ("share of personal pronouns that
    # address the reader"). Dividing by word_count instead leaves a page
    # saturated with direct address at ~0.02, banded "rarely_direct".
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


# Verified live on belfius.be, whose hero image has no og:image and falls back
# to a RELATIVE <img src>. Unresolved, that goes straight to requests.get() in
# extract_colours(), which raises MissingSchema - silently swallowed there, so
# the row just gets null colours with no error.
def test_hero_image_url_is_resolved_to_absolute():
    html = '<html><body><img src="/images/hero.jpg"></body></html>'
    result = extract(html, language="en", page_url="https://example.com/page")
    assert result["_hero_image_url"] == "https://example.com/images/hero.jpg"


def test_hero_image_url_without_a_page_url_stays_relative():
    """No page_url (e.g. a direct extract() call in a test) - can't resolve, so
    the raw value is returned unchanged rather than guessed at."""
    html = '<html><body><img src="/images/hero.jpg"></body></html>'
    result = extract(html, language="en")
    assert result["_hero_image_url"] == "/images/hero.jpg"


# Regression - verified live on n26.com, which has no
# disclaimer/legal-classed element but uses real footnotes (<sup>N</sup> in
# the body, a matching "N ..." paragraph elsewhere) - the class/id heuristic
# alone scored disclaimer_present=False despite real disclosure text present.
def test_disclaimer_detected_from_footnote_markers():
    html = """<html><body>
    <p>Deux retraits sans frais par mois<sup>1</sup>, carte physique en option<sup>2</sup>.</p>
    <p>1 N26 Standard inclut deux retraits mensuels sans frais.</p>
    <p>2 Des frais de 10 euros s'appliquent pour la carte physique.</p>
    </body></html>"""
    result = extract(html, language="fr")
    assert result["disclaimer_present"] is True
    assert result["disclaimer_word_share"] > 0


def test_footnote_heuristic_does_not_fire_on_an_ordinary_numbered_list():
    """No <sup> markers at all here - a numbered list must not be mistaken
    for footnotes just because its items start with a digit."""
    html = """<html><body>
    <p>How it works</p>
    <p>1 Open the app and sign up.</p>
    <p>2 Verify your identity.</p>
    <p>3 Start using your account.</p>
    </body></html>"""
    result = extract(html, language="en")
    assert result["disclaimer_present"] is False


def test_extract_leaves_render_dependent_fields_none():
    # These need a headless viewport - must stay None, not guessed
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


# extract_colours() runs assert_can_fetch() before the image GET, so every
# test below that expects the fetch to happen has to patch it too - otherwise
# it makes a real network call to example.com/robots.txt.
def test_extract_colours_on_a_solid_image():
    solid_orange = Image.new("RGB", (100, 100), color=(255, 98, 0))
    with patch("comparator.collection.visual_features.assert_can_fetch"), \
         patch("comparator.collection.visual_features.requests.get", return_value=_fake_image_response(solid_orange)):
        result = extract_colours("https://example.com/hero.png", n_colours=1)
    assert result["dominant_colour_hex"] == "#ff6200"
    assert result["background_luminance"] is not None
    assert 0 <= result["background_luminance"] <= 1


def test_brand_colour_share_is_none_without_a_known_bank():
    solid_orange = Image.new("RGB", (100, 100), color=(255, 98, 0))
    with patch("comparator.collection.visual_features.assert_can_fetch"), \
         patch("comparator.collection.visual_features.requests.get", return_value=_fake_image_response(solid_orange)):
        result = extract_colours("https://example.com/hero.png", n_colours=1)
    assert result["brand_colour_share"] is None


def test_brand_colour_share_matches_the_banks_own_colour():
    ing_orange = Image.new("RGB", (100, 100), color=(255, 98, 0))  # #ff6200
    with patch("comparator.collection.visual_features.assert_can_fetch"), \
         patch("comparator.collection.visual_features.requests.get", return_value=_fake_image_response(ing_orange)):
        result = extract_colours("https://example.com/hero.png", bank="ing", n_colours=1)
    assert result["brand_colour_share"] == pytest.approx(1.0)


def test_brand_colour_share_is_low_when_the_image_is_not_the_brand_colour():
    # Without a known brand hex this reports the share of the most frequent
    # colour, mislabelled "brand" - 1.0 for ANY bank, even ING (orange)
    # against a solid blue image.
    unrelated_blue = Image.new("RGB", (100, 100), color=(0, 0, 255))
    with patch("comparator.collection.visual_features.assert_can_fetch"), \
         patch("comparator.collection.visual_features.requests.get", return_value=_fake_image_response(unrelated_blue)):
        result = extract_colours("https://example.com/hero.png", bank="ing", n_colours=1)
    assert result["brand_colour_share"] == pytest.approx(0.0)


def test_extract_colours_handles_missing_url():
    result = extract_colours(None)
    assert result["dominant_colour_hex"] is None
    assert result["palette_hex"] == []


def test_extract_colours_handles_fetch_failure_gracefully():
    with patch("comparator.collection.visual_features.assert_can_fetch"), \
         patch("comparator.collection.visual_features.requests.get", side_effect=ConnectionError("nope")):
        result = extract_colours("https://example.com/broken.png")
    assert result["dominant_colour_hex"] is None  # must not raise


def test_extract_colours_respects_the_compliance_gate():
    # New test for the audit fix - a robots.txt disallow on the
    # image itself must stop the fetch (never bypassed) and still degrade to
    # "no colours" rather than raising, per this function's existing contract.
    with patch(
        "comparator.collection.visual_features.assert_can_fetch",
        side_effect=ScrapingNotAllowed("disallowed"),
    ), patch("comparator.collection.visual_features.requests.get") as mock_get:
        result = extract_colours("https://example.com/hero.png", bank="ing")
    mock_get.assert_not_called()
    assert result["dominant_colour_hex"] is None


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
    "target_personas": ["family", "student"],
    "cross_sold_products": ["mortgage", "pension"],
}


def test_extract_model_assisted_validates_a_good_response():
    with patch("comparator.collection.llm_extractor._call_llm", return_value=(__import__("json").dumps(_VALID_RESPONSE), "test/model")):
        result = extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account")
    assert isinstance(result, ModelAssistedFields)
    assert result.primary_product == "Term account"


# target_personas is the first list-valued model_assisted field.
def test_extract_model_assisted_reads_target_personas():
    with patch("comparator.collection.llm_extractor._call_llm", return_value=(__import__("json").dumps(_VALID_RESPONSE), "test/model")):
        result = extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account")
    assert result.target_personas == ["family", "student"]


def test_extract_model_assisted_defaults_target_personas_to_empty_list_when_omitted():
    without_personas = {k: v for k, v in _VALID_RESPONSE.items() if k != "target_personas"}
    with patch("comparator.collection.llm_extractor._call_llm", return_value=(__import__("json").dumps(without_personas), "test/model")):
        result = extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account")
    assert result.target_personas == []


def test_extract_model_assisted_reads_cross_sold_products():
    with patch("comparator.collection.llm_extractor._call_llm", return_value=(__import__("json").dumps(_VALID_RESPONSE), "test/model")):
        result = extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account")
    assert result.cross_sold_products == ["mortgage", "pension"]


def test_extract_model_assisted_strips_markdown_fences():
    fenced = "```json\n" + __import__("json").dumps(_VALID_RESPONSE) + "\n```"
    with patch("comparator.collection.llm_extractor._call_llm", return_value=(fenced, "test/model")):
        result = extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account")
    assert result.dominant_image_type == "photo"


def test_extract_model_assisted_retries_once_then_raises():
    with patch("comparator.collection.llm_extractor._call_llm", return_value=("not json at all", "test/model")):
        with pytest.raises(LLMExtractionError):
            extract_model_assisted("some page text", image_count=3, has_animation=False, product_family="term_account", retries=1)


# a label outside the dictionary used to pass the pydantic model
# (typed only as str) and fail much later in schema.validate().
def test_extract_model_assisted_retries_an_off_dictionary_label_then_raises():
    bad = {**_VALID_RESPONSE, "regulatory_disclosure_prominence": "very_prominent"}
    with patch("comparator.collection.llm_extractor._call_llm",
               return_value=(__import__("json").dumps(bad), "test/model")) as call:
        with pytest.raises(LLMExtractionError, match="regulatory_disclosure_prominence"):
            extract_model_assisted("t", image_count=1, has_animation=False,
                                   product_family="term_account", retries=1)
    assert call.call_count == 2


def test_extract_model_assisted_rejects_an_unknown_persona():
    bad = {**_VALID_RESPONSE, "target_personas": ["students"]}
    with patch("comparator.collection.llm_extractor._call_llm",
               return_value=(__import__("json").dumps(bad), "test/model")):
        with pytest.raises(LLMExtractionError, match="target_personas"):
            extract_model_assisted("t", image_count=1, has_animation=False,
                                   product_family="term_account", retries=0)


def test_a_malformed_provider_body_falls_through_to_the_next_provider(monkeypatch):
    # HTTP 200 with an error object used to raise KeyError out of the chain,
    # so no fallback was ever tried.
    import requests as _requests

    _clear_provider_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k1")
    monkeypatch.setenv("GROQ_API_KEY", "k2")

    class _Response:
        def __init__(self, body):
            self._body = body

        def raise_for_status(self):
            return None

        def json(self):
            return self._body

    good = {"choices": [{"message": {"content": __import__("json").dumps(_VALID_RESPONSE)}}]}
    bodies = iter([{"error": {"message": "quota"}}, good])
    monkeypatch.setattr(_requests, "post", lambda *a, **k: _Response(next(bodies)))
    _fields, model_id = extract_model_assisted_with_provenance(
        "t", image_count=1, has_animation=False, product_family="term_account")
    assert model_id.startswith("groq/")


def _clear_provider_keys(monkeypatch):
    """Provider tests read the real environment, so a developer who
    has DEEPSEEK_API_KEY exported would get different ordering than CI. Clear
    them all, then set only the ones the test is about."""
    for var in ("DEEPSEEK_API_KEY", "GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3",
                "OPENROUTER_API_KEY", "CEREBRAS_API_KEY", "SAMBANOVA_API_KEY"):
        monkeypatch.delenv(var, raising=False)


def test_groq_tried_before_other_fallbacks(monkeypatch):
    # Confirms the provider ORDER matches .env.example, not just
    # that "a" provider gets called.
    # Unchanged in intent. DeepSeek now sits ahead of Groq
    # (Decision 6), so this test pins the order BELOW DeepSeek by leaving its
    # key unset - see test_deepseek_is_tried_first for the new head of the chain.
    _clear_provider_keys(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-openrouter-key")
    calls = []

    def fake_call(url, api_key, model, prompt, system_prompt=None, **kwargs):
        calls.append(url)
        if "groq" in url:
            raise __import__("requests").RequestException("groq down")
        return __import__("json").dumps(_VALID_RESPONSE)

    with patch("comparator.collection.llm_extractor._call_openai_compatible", side_effect=fake_call):
        extract_model_assisted("text", image_count=1, has_animation=False, product_family="term_account")

    assert any("groq" in c for c in calls), "groq must be tried first"
    assert any("openrouter" in c for c in calls), "fallback must be tried after groq fails"


def test_deepseek_is_tried_first(monkeypatch):
    """Decision 6: DeepSeek is the pinned model, so it leads the chain."""
    _clear_provider_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-deepseek-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    calls = []

    def fake_call(url, api_key, model, prompt, system_prompt=None, **kwargs):
        calls.append(url)
        return __import__("json").dumps(_VALID_RESPONSE)

    with patch("comparator.collection.llm_extractor._call_openai_compatible", side_effect=fake_call):
        extract_model_assisted("text", image_count=1, has_animation=False, product_family="term_account")

    assert "deepseek" in calls[0], f"deepseek must lead the chain, got {calls[0]}"


def test_extraction_records_which_model_answered(monkeypatch):
    """The whole point of Decision 6: the row must say who labelled it."""
    _clear_provider_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-deepseek-key")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")

    def fake_call(url, api_key, model, prompt, system_prompt=None, **kwargs):
        return __import__("json").dumps(_VALID_RESPONSE)

    with patch("comparator.collection.llm_extractor._call_openai_compatible", side_effect=fake_call):
        _fields, model_id = extract_model_assisted_with_provenance(
            "text", image_count=1, has_animation=False, product_family="term_account"
        )
    assert model_id == "deepseek/deepseek-chat"


def test_fallback_is_recorded_not_silent(monkeypatch):
    """A dataset labelled by two models must be able to say so (NFR-02)."""
    _clear_provider_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-deepseek-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")

    def fake_call(url, api_key, model, prompt, system_prompt=None, **kwargs):
        if "deepseek" in url:
            raise __import__("requests").RequestException("deepseek down")
        return __import__("json").dumps(_VALID_RESPONSE)

    with patch("comparator.collection.llm_extractor._call_openai_compatible", side_effect=fake_call):
        _fields, model_id = extract_model_assisted_with_provenance(
            "text", image_count=1, has_animation=False, product_family="term_account"
        )
    assert model_id.startswith("groq/"), "the row must record the model that actually answered"


# --- colour measured on the page, not the hero crop -------------
def test_brand_share_counts_every_pixel_not_just_the_top_palette():
    """A brand accent is a few percent of a full page and never makes the top-5
    quantised palette - the palette shortcut scored every bank exactly 0.000,
    which was a property of the method, not of the banks."""
    from PIL import Image

    from comparator.collection.visual_features import extract_colours_from_image

    img = Image.new("RGB", (200, 200), (255, 255, 255))
    for y in range(8):                      # 4% of the image, ING orange
        for x in range(200):
            img.putpixel((x, y), (255, 98, 0))

    assert extract_colours_from_image(img, bank="ing")["brand_colour_share"] == pytest.approx(0.04, abs=0.01)


def test_brand_share_is_specific_to_the_bank():
    from PIL import Image

    from comparator.collection.visual_features import extract_colours_from_image

    img = Image.new("RGB", (100, 100), (255, 98, 0))          # solid ING orange
    assert extract_colours_from_image(img, bank="ing")["brand_colour_share"] > 0.9
    assert extract_colours_from_image(img, bank="kbc")["brand_colour_share"] == 0.0


def test_background_luminance_separates_a_dark_page_from_a_light_one():
    from PIL import Image

    from comparator.collection.visual_features import extract_colours_from_image

    light = extract_colours_from_image(Image.new("RGB", (50, 50), (255, 255, 255)))
    dark = extract_colours_from_image(Image.new("RGB", (50, 50), (20, 20, 25)))
    assert light["background_luminance"] > 0.9
    assert dark["background_luminance"] < 0.1


def test_unknown_bank_gets_no_brand_share_rather_than_a_wrong_one():
    """'s finding, kept: without a known bank the honest answer is None."""
    from PIL import Image

    from comparator.collection.visual_features import extract_colours_from_image

    assert extract_colours_from_image(Image.new("RGB", (40, 40), (10, 10, 200)))["brand_colour_share"] is None


# --- declarative shadow DOM in manually saved pages -------------
# A browser "save page as complete" writes shadow content out as
# <template shadowrootmode>. BeautifulSoup does not walk into those, so
# the saved ING pages parsed as 14 words while carrying 4,858 inside
# templates - the shadow-DOM bug again, arriving through a different door.
DECLARATIVE_SHADOW_HTML = """
<html><body>
  <h1>Visible heading</h1>
  <ing-app-page>
    <template shadowrootmode="open">
      <p>Ouvrez un compte a vue en quelques minutes seulement aujourd'hui.</p>
      <img src="hero.png" alt="hero">
      <a href="#x">Decouvrir le compte</a>
    </template>
  </ing-app-page>
</body></html>
"""


def test_declarative_shadow_content_is_recovered():
    from comparator.collection.scraper import flatten_declarative_shadow_roots

    flat, count = flatten_declarative_shadow_roots(DECLARATIVE_SHADOW_HTML)
    assert count == 1
    assert "quelques minutes" in flat


def test_extract_sees_shadow_content_without_being_asked():
    """Applied inside extract(), so a manual capture and a live capture are
    measured the same way."""
    features = extract(DECLARATIVE_SHADOW_HTML, language="fr", page_url="https://example.invalid/x")
    assert features["word_count"] > 8, "the shadow paragraph must be counted"
    assert features["image_count"] == 1
    assert features["cta_count"] >= 1


def test_a_page_without_shadow_roots_is_untouched():
    from comparator.collection.scraper import flatten_declarative_shadow_roots

    plain = "<html><body><p>hello</p></body></html>"
    flat, count = flatten_declarative_shadow_roots(plain)
    assert count == 0 and flat == plain


def test_ordinary_templates_are_left_alone():
    """A <template> without a shadowroot attribute is an inert stamp-out
    template - its content is not on the page and must not be counted."""
    from comparator.collection.scraper import flatten_declarative_shadow_roots

    html = "<html><body><template><p>not rendered</p></template></body></html>"
    _flat, count = flatten_declarative_shadow_roots(html)
    assert count == 0


def test_chrome_exclusion_catches_a_menu_built_from_plain_divs():
    # Two of the fourteen captured banks (hellobank, keytrade) build their menu
    # with <div class="navbar-container"> around <ul class="desktop-menu"> and
    # carry no <nav>, no role="navigation" and no <footer>. Matching on tag and
    # role alone let their whole mega-menu be eligible as calls to action.
    html = """<html><body>
      <div class="navbar-container"><ul class="desktop-menu">
        <li><a href="/a">Ouvrir un compte</a></li>
        <li><a href="/b">Découvrir nos offres</a></li>
      </ul></div>
      <main><a href="/go">Ouvrez votre compte</a></main>
    </body></html>"""
    from bs4 import BeautifulSoup
    from comparator.collection.scraper import _count_ctas

    count, _ = _count_ctas(BeautifulSoup(html, "html.parser"))
    assert count == 1, "only the body CTA counts; the div-based menu is chrome"
