"""Tests for the recommendations tab and the 10-page site generator.

steph 18/09, new modules, new tests. No network and no model call: the LLM
entry points are monkeypatched, because the value being tested is the local
logic - that a feature id the model invented is dropped, that only the ticked
recommendations reach the builder, and that ten pages are rendered in ING's
house style whatever the model returns.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.collection.llm_extractor import LLMExtractionError  # noqa: E402

from comparator.recommendations import (  # noqa: E402
    Recommendation,
    RecommendationSet,
    _digest,
    build_recommendations,
    parse_response,
    select,
)
from comparator.site_generator import (  # noqa: E402
    PAGES,
    Hero,
    PageContent,
    Section,
    _content_text,
    _detected_language,
    _download_assets,
    _fallback_page,
    generate_page,
    generate_site,
    render_page,
)

_REPORT = {
    "scope": {"product_family_label": "Current-account packs", "pages": 9,
              "banks": ["ING", "KBC"], "n_features": 32, "languages": ["fr", "nl"]},
    "headline": {"focus": "ING", "score": 0.222, "verdict": "clearly with the traditional banks",
                 "has_focus": True},
    "peerGaps": [
        {"feature": "rate_shown", "label": "Shows a rate", "focusValue": 0.0, "peerMean": 0.667,
         "gapSd": -1.2, "direction": "below", "extraction": "automatic"},
        {"feature": "cta_count", "label": "Calls to action", "focusValue": 3.0, "peerMean": 15.9,
         "gapSd": -1.1, "direction": "below", "extraction": "automatic"},
    ],
    "separation": [{"feature": "second_person_ratio", "label": "Speaks to “you”",
                    "traditional": 0.3, "challenger": 0.5, "effect": 0.8,
                    "higherAt": "challenger"}],
    "deckClaims": [], "limitations": {}, "banks": [], "generated_at": "2026-09-18T09:00:00Z",
}

_RAW = json.dumps({
    "summary": "ING is clear but under-equipped to convert.",
    "recommendations": [
        {"title": "Add a visible rate", "priority": "high", "finding": "rate_shown is 0.0 vs 0.667",
         "recommendation": "Show the rate above the fold", "features": ["rate_shown", "not_a_feature"],
         "page_targets": ["index"]},
        {"title": "More calls to action", "priority": "medium", "finding": "cta_count is 3 vs 15.9",
         "recommendation": "Add two more CTAs", "features": ["cta_count"], "page_targets": ["index"]},
    ],
})


def test_digest_rounds_long_floats_before_they_reach_the_model():
    # sieg 20/09: regression test - a real report's raw float (e.g.
    # 0.5912291666666667) must not reach the prompt at full precision, since
    # the model was copying it verbatim into recommendation prose.
    report = {
        **_REPORT,
        "peerGaps": [{"feature": "background_luminance", "label": "Page brightness",
                      "focusValue": 0.19775, "peerMean": 0.5912291666666667,
                      "gapSd": -1.1666666666, "direction": "below", "extraction": "automatic"}],
    }
    digest = json.loads(_digest(report))
    gap = digest["focus_gaps_vs_peers"][0]
    assert gap["peer_mean"] == 0.59
    assert gap["gap_sd"] == -1.17
    assert gap["focus_value"] == 0.2


def test_parse_response_accepts_a_json_fence():
    parsed = parse_response(f"```json\n{_RAW}\n```")
    assert parsed.summary.startswith("ING is clear")
    assert len(parsed.recommendations) == 2


def test_build_recommendations_drops_feature_ids_the_report_does_not_have(monkeypatch):
    monkeypatch.setattr("comparator.recommendations._call_llm", lambda *a, **k: (_RAW, "deepseek/deepseek-chat"))
    result = build_recommendations(_REPORT)
    assert result.model == "deepseek/deepseek-chat"
    assert [r.id for r in result.recommendations] == ["R1", "R2"]
    # "not_a_feature" is not in the report, so it is not linkable evidence.
    assert result.recommendations[0].features == ["rate_shown"]


def test_build_recommendations_retries_on_invalid_json(monkeypatch):
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        return ("not json", "m") if calls["n"] == 1 else (_RAW, "m")

    monkeypatch.setattr("comparator.recommendations._call_llm", flaky)
    result = build_recommendations(_REPORT)
    assert calls["n"] == 2
    assert len(result.recommendations) == 2


def test_select_keeps_only_the_chosen_ids_in_the_original_order():
    full = RecommendationSet(
        generated_at="t", model="m", summary="s",
        recommendations=[
            Recommendation("R1", "a", "high", "f", "r"),
            Recommendation("R2", "b", "low", "f", "r"),
            Recommendation("R3", "c", "medium", "f", "r"),
        ],
    )
    chosen = select(full, ["R3", "R1"])
    assert [r.id for r in chosen.recommendations] == ["R1", "R3"]
    assert chosen.summary == "s"


def test_recommendation_set_round_trips_through_json():
    full = RecommendationSet(generated_at="t", model="m", summary="s",
                             recommendations=[Recommendation("R1", "a", "high", "f", "r", ["x"], ["index"])])
    again = RecommendationSet.from_dict(json.loads(json.dumps(full.to_dict())))
    assert again == full


def _content(slug: str, image: str = "home") -> PageContent:
    return PageContent(
        slug=slug, page_title=f"Title {slug}", meta_description="d",
        hero=Hero(eyebrow="E", headline="<script>alert(1)</script>", subheading="sub",
                  primary_cta="Ouvrir un compte", image=image),
        sections=[Section(heading="H", body=["b"], bullets=["x"], cta_label="Ouvrir un compte")],
        faq=[], disclaimer="disclaimer", recommendations_implemented=["R1"],
    )


def test_render_page_links_all_ten_pages_and_escapes_model_output():
    html = render_page(_content("index"), "fr")
    for spec in PAGES:
        target = "index.html" if spec.slug == "index" else f"{spec.slug}.html"
        assert target in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert 'src="assets/logo-white.svg"' in html


def test_render_page_uses_the_ing_brand_assets():
    for slug in ("comptes-epargne", "credit-hypothecaire"):
        spec = next(p for p in PAGES if p.slug == slug)
        html = render_page(_content(slug, spec.image), "fr")
        assert f'src="assets/{spec.image}.svg"' in html


def _page_json(headline: str, body: str, lang_marker: str) -> str:
    return json.dumps({
        "slug": "index",
        "page_title": headline,
        "meta_description": lang_marker,
        "hero": {"eyebrow": lang_marker, "headline": headline, "subheading": body,
                 "primary_cta": lang_marker, "secondary_cta": None, "image": "home"},
        "sections": [{"heading": headline, "body": [body, body], "bullets": [body], "cta_label": None}],
        "faq": [{"q": body, "a": body}],
        "disclaimer": lang_marker,
        "recommendations_implemented": ["R1"],
    })


_FRENCH = ("Ouvrez votre compte en ligne en quelques minutes et gardez le controle de votre argent, "
           "vous pouvez le faire avec votre telephone et votre carte, pour vous et vos projets.")
_DUTCH = ("Open uw rekening online in enkele minuten en houd de controle over uw geld, "
          "u kunt het doen met uw telefoon en uw kaart, voor u en uw plannen.")


def test_detected_language_places_clear_dutch_and_french_apart():
    assert _detected_language(_DUTCH) == "nl"
    assert _detected_language(_FRENCH) == "fr"


def test_generate_page_retries_when_the_model_answers_in_the_wrong_language(monkeypatch):
    calls = {"n": 0}

    def fake_llm(*args, **kwargs):
        calls["n"] += 1
        return (_page_json("Open uw rekening", _DUTCH, _DUTCH) if calls["n"] == 1
                else _page_json("Ouvrez votre compte", _FRENCH, _FRENCH), "m")

    monkeypatch.setattr("comparator.site_generator._call_llm", fake_llm)
    recs = RecommendationSet(generated_at="t", model="m", summary="s", recommendations=[])
    spec = next(p for p in PAGES if p.slug == "index")
    page = generate_page(spec, recs, "fr", "s", retries=1)
    assert calls["n"] == 2
    assert page.hero.headline == "Ouvrez votre compte"


def test_generate_page_retries_when_a_selected_recommendation_is_not_expressed(monkeypatch):
    calls = {"n": 0}
    no_rate = ("Notre compte courant vous simplifie la vie. Vous gardez le controle de vos "
               "paiements et de votre budget, pour vous et vos projets, avec votre carte.")
    with_rate = no_rate + " Le taux de votre compte est indique clairement des le depart."

    def fake_llm(*args, **kwargs):
        calls["n"] += 1
        body = no_rate if calls["n"] == 1 else with_rate
        return (_page_json("Votre compte courant", body, body), "m")

    monkeypatch.setattr("comparator.site_generator._call_llm", fake_llm)
    recs = RecommendationSet(generated_at="t", model="m", summary="s", recommendations=[
        Recommendation("R1", "Add a visible rate", "high", "f", "r", ["rate_shown"], ["index"]),
    ])
    spec = next(p for p in PAGES if p.slug == "index")
    page = generate_page(spec, recs, "fr", "s", retries=2)
    assert calls["n"] == 2
    assert "taux" in _content_text(page).lower()


def test_missing_coverage_ignores_unbriefed_pages_and_unmappable_features():
    from comparator.site_generator import _missing_coverage
    page = _content("contact")
    recs = RecommendationSet(generated_at="t", model="m", summary="s", recommendations=[
        Recommendation("R1", "rate", "high", "f", "r", ["rate_shown"], ["index"]),
        Recommendation("R2", "layout", "low", "f", "r", ["layout_archetype"], ["contact"]),
    ])
    # R1 does not target contact, R2 has no machine-checkable cue.
    assert _missing_coverage(page, recs) == []


def test_download_assets_builds_a_white_logo_from_ings_own_svg(monkeypatch, tmp_path):
    svg = '<svg><path fill="#006" d="M0"/><path fill="#f60" d="M1"/></svg>'

    class _Response:
        content = svg.encode()

        def raise_for_status(self):
            return None

    monkeypatch.setattr("comparator.site_generator.requests.get", lambda *a, **k: _Response())
    warnings = _download_assets(tmp_path)
    assert warnings == []
    assert (tmp_path / "logo-full.svg").read_text() == svg
    white = (tmp_path / "logo-white.svg").read_text()
    assert 'fill="#ffffff"' in white
    assert 'fill="#006"' not in white
    # The orange lion must survive the recolor.
    assert 'fill="#f60"' in white


def test_fallback_page_is_complete_and_honest():
    spec = PAGES[0]
    page = _fallback_page(spec, "summary")
    assert page.slug == spec.slug
    assert page.hero.primary_cta
    assert page.disclaimer
    assert page.recommendations_implemented == []


def test_generate_site_writes_ten_pages_and_marks_fallbacks(monkeypatch, tmp_path):
    def fake_assets(dest: Path):
        dest.mkdir(parents=True, exist_ok=True)
        return []

    monkeypatch.setattr("comparator.site_generator._download_assets", fake_assets)

    def fake_generate_page(spec, recs, language, summary, retries=2):
        if spec.slug == "contact":
            raise LLMExtractionError("model down")
        return _content(spec.slug, spec.image)

    monkeypatch.setattr("comparator.site_generator.generate_page", fake_generate_page)

    recs = RecommendationSet(generated_at="t", model="m", summary="s",
                             recommendations=[Recommendation("R1", "a", "high", "f", "r", ["x"], ["index"])])
    manifest = generate_site(_REPORT, recs, language="fr", out_dir=tmp_path, max_workers=2)

    assert len(manifest["pages"]) == 10
    assert (tmp_path / "index.html").is_file()
    assert (tmp_path / "manifest.json").is_file()
    assert [p["slug"] for p in manifest["pages"] if p["used_fallback"]] == ["contact"]
    assert manifest["language"] == "fr"
