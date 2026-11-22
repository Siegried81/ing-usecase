"""Regression tests for the line-by-line review of the presentation modules.

Each test pins one defect found while reading report.py, ai_score.py,
site_generator.py, geo_trends.py and rubric.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import ai_score  # noqa: E402
from comparator.analysis import (  # noqa: E402
    category_comparison,
    cluster_banks,
    feature_accounting,
    ing_vs_peers,
    positioning_axis,
    similarity_matrix,
)
from comparator.banks import display_name  # noqa: E402
from comparator.collection.llm_extractor import LLMExtractionError  # noqa: E402
from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.geo_trends import BANK_DISPLAY_NAMES  # noqa: E402
from comparator.report import build_chart_report  # noqa: E402
from comparator.site_generator import (  # noqa: E402
    Hero,
    PageContent,
    Section,
    render_page,
)


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


@pytest.fixture(scope="module")
def df(fd):
    return build_fixture(fd)


def _companion(df, fd, accounting):
    categories = df.drop_duplicates("bank").set_index("bank")["bank_category"]
    return build_chart_report(
        positioning=positioning_axis(df, fd),
        categories=categories,
        deviations=ing_vs_peers(df, fd),
        comparison=category_comparison(df, fd),
        distances=similarity_matrix(df, fd),
        clusters=cluster_banks(df, fd),
        accounting=accounting,
    )


def test_band_note_is_only_written_when_bands_were_really_excluded(df, fd):
    accounting = feature_accounting(df, fd)
    accounting["band_redundant"] = []
    assert "excluded on purpose" not in _companion(df, fd, accounting)


def test_band_note_states_the_real_number_of_excluded_bands(df, fd):
    accounting = feature_accounting(df, fd)
    accounting["band_redundant"] = ["word_count_band", "sentence_count_band", "readability_band"]
    text = _companion(df, fd, accounting)
    assert "The 3 band features" in text
    assert "four bands" not in text


def test_simplicity_tie_between_two_bands_is_the_mean_not_the_alphabetical_pick():
    rows = pd.DataFrame({"readability_band": ["hard", "very_hard"]})
    assert ai_score.score_simplicity(rows) == 1.25


def test_simplicity_with_a_single_mode_is_unchanged():
    rows = pd.DataFrame({"readability_band": ["easy", "easy", "hard"]})
    assert ai_score.score_simplicity(rows) == 7.5


def test_persona_taxonomy_size_matches_the_dictionary(fd):
    assert ai_score.PERSONA_TAXONOMY_SIZE == len(fd["target_personas"].values)


def _page() -> PageContent:
    return PageContent(
        slug="index", page_title="T", meta_description="d",
        hero=Hero(eyebrow="E", headline="H", subheading="s", primary_cta="Start"),
        sections=[Section(heading="H", body=["b"])],
        faq=[], disclaimer="d",
    )


@pytest.mark.parametrize("language,skip", [
    ("fr", "Aller au contenu"), ("nl", "Naar de inhoud"), ("en", "Skip to content"),
])
def test_skip_link_follows_the_page_language(language, skip):
    html = render_page(_page(), language)
    assert f">{skip}</a>" in html
    if language != "en":
        assert "Skip to content" not in html


def test_main_navigation_label_is_localised():
    assert 'aria-label="Principal"' in render_page(_page(), "fr")
    assert 'aria-label="Principal"' not in render_page(_page(), "nl")


def test_geo_bank_names_come_from_the_shared_display_names():
    for key, name in BANK_DISPLAY_NAMES.items():
        assert name == display_name(key)


def test_chart_companion_title_follows_the_focus_bank(df, fd):
    categories = df.drop_duplicates("bank").set_index("bank")["bank_category"]
    text = build_chart_report(
        positioning=positioning_axis(df, fd, focus="kbc"),
        categories=categories,
        deviations=ing_vs_peers(df, fd, focus="kbc"),
        comparison=category_comparison(df, fd),
        distances=similarity_matrix(df, fd),
        clusters=cluster_banks(df, fd),
        focus="kbc",
    )
    assert "## 1. Where does KBC sit?" in text


# --- generate_page: one fixed prompt, bounded retries -------------------------
def test_generate_page_sends_the_same_prompt_on_every_attempt(monkeypatch):
    import json

    from comparator.recommendations import RecommendationSet
    from comparator.site_generator import PAGES, generate_page

    seen = []

    def fake_llm(prompt, **kwargs):
        seen.append((prompt, kwargs.get("system_prompt")))
        return "not json", "m"

    monkeypatch.setattr("comparator.site_generator._call_llm", fake_llm)
    recs = RecommendationSet(generated_at="t", model="m", summary="s", recommendations=[])
    with pytest.raises(LLMExtractionError):
        generate_page(PAGES[0], recs, "fr", "s", retries=2)
    assert len(seen) == 3
    assert len(set(seen)) == 1
    assert json  # keep the import local to the test


# --- reputation: model output is checked before it is counted ------------------
def test_theme_counts_ignore_titles_the_model_invented_and_count_a_headline_once():
    from unittest.mock import patch

    from comparator import reputation

    fetched = [{"title": "ING launches app", "url": "https://news.example/1"},
               {"title": "ING results up", "url": "https://news.example/2"}]
    model = reputation.ReputationModel(
        theme_headlines={
            "product_launch": ["ING launches app", "ING invented story"],
            "innovation_digital": ["ing  LAUNCHES app"],
            "made_up_theme": ["ING results up"],
            "financial_results": ["ING results up"],
        },
        notable_headlines=[],
    )
    with patch("comparator.reputation.fetch_headlines", return_value=fetched), \
         patch("comparator.reputation.classify_headlines", return_value=model), \
         patch.object(reputation, "_save_cache"), patch.object(reputation, "_load_cache", return_value={}):
        snap = reputation.bank_snapshot("ING", api_key="k")
    assert snap["themes"]["innovation_digital"] == 1
    assert snap["themes"]["product_launch"] == 0
    assert snap["themes"]["financial_results"] == 1
    assert sum(snap["themes"].values()) == 2
    assert snap["theme_headlines"]["financial_results"][0]["url"] == "https://news.example/2"


def test_removed_wrappers_and_ignored_params_stay_removed():
    import inspect

    from comparator import generation, profiles
    from comparator.site_generator import _fallback_page

    assert not hasattr(generation, "guardrails")
    assert list(inspect.signature(profiles.render_markdown).parameters) == ["profile"]
    assert "_summary" not in inspect.signature(_fallback_page).parameters
