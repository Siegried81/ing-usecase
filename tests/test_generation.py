"""Tests for step 5 - campaign generation and its evaluation (steph 15/09).

No test here calls a model. The parts worth testing are the target derivation,
the HTML rendering, and the scoring loop - everything that has to be right for
the evaluation to mean anything.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.collection.scraper import extract  # noqa: E402
from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.generation import (  # noqa: E402
    GUARDRAIL_BLOCKED_FEATURES,
    MEASURED_FEATURES,
    GeneratedCampaign,
    TargetSpec,
    build_brief,
    build_targets,
    evaluate,
    guardrails,
    hit_rate,
    score,
    to_html,
)


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


@pytest.fixture(scope="module")
def df(fd):
    return build_fixture(fd)


@pytest.fixture()
def campaign():
    return GeneratedCampaign(
        headline="Put your savings to work",
        subheading="A term account that works while you do",
        body_paragraphs=[
            "You choose the term. You know the return before you start.",
            "Your money is locked for the period you pick, at a rate of [RATE].",
        ],
        cta_label="Open your term account",
        additional_cta_labels=["Learn more about terms"],
        layout_archetype="hero_stacked",
        background_style="light",
        accent_colour_hex="#ff6200",
        image_briefs=["A person closing a laptop at a kitchen table, warm light"],
        disclaimer_placeholder="[LEGAL: capital availability and early-withdrawal conditions]",
        persuasion_levers_used=["authority", "scarcity"],
    )


# --- targets -----------------------------------------------------------------
def test_both_variants_are_built(df, fd):
    targets = build_targets(df, fd)
    assert set(targets) == {"on_brand", "challenger_style"}
    assert targets["on_brand"].specs and targets["challenger_style"].specs


def test_targets_only_name_measurable_features(df, fd):
    for target in build_targets(df, fd).values():
        for spec in target.specs:
            assert spec.feature in MEASURED_FEATURES, (
                f"{spec.feature} cannot be measured from generated HTML, so it must not be a target"
            )


def test_targets_never_ask_for_something_the_guardrails_forbid(df, fd):
    """Asking for numeric claims while banning invented figures guarantees a miss."""
    for target in build_targets(df, fd).values():
        named = {s.feature for s in target.specs}
        assert not (named & set(GUARDRAIL_BLOCKED_FEATURES))


def test_the_two_variants_actually_differ(df, fd):
    targets = build_targets(df, fd)
    on_brand = {s.feature: s.describe() for s in targets["on_brand"].specs}
    challenger = {s.feature: s.describe() for s in targets["challenger_style"].specs}
    shared = set(on_brand) & set(challenger)
    assert any(on_brand[f] != challenger[f] for f in shared), "the contrast IS the insight"


def test_both_variants_require_a_disclaimer(df, fd):
    for target in build_targets(df, fd).values():
        assert any(s.feature == "disclaimer_present" and s.value is True for s in target.specs)


def test_spec_hit_and_miss():
    spec = TargetSpec("word_count", "range", low=100, high=200)
    assert spec.hit(150) is True
    assert spec.hit(400) is False
    assert spec.hit(None) is None


def test_exact_spec_is_case_insensitive():
    assert TargetSpec("layout", "exact", value="hero_stacked").hit("HERO_STACKED") is True


# --- rendering and scoring ---------------------------------------------------
def test_rendered_html_is_readable_by_the_real_extractor(campaign):
    """The whole evaluation rests on this: same extractor as the real pages."""
    features = extract(to_html(campaign), language="en")
    assert features["word_count"] > 0
    assert features["image_count"] == len(campaign.image_briefs)
    assert features["cta_count"] >= 1, "the CTA must be machine-detectable"
    assert features["cta_above_fold"] is True
    assert features["disclaimer_present"] is True


def test_rendered_html_escapes_copy(campaign):
    campaign.headline = 'Save <b>more</b> & "win"'
    assert "<b>more</b>" not in to_html(campaign)


def test_scored_row_is_labelled_generated(campaign):
    row = score(campaign, variant="on_brand")
    assert row["data_source"] == "llm_generated"
    assert row["page_id"].startswith("generated_")


def test_scored_row_passes_the_guardrails(campaign):
    assert guardrails(score(campaign, variant="on_brand")).ok


def test_a_row_without_a_disclaimer_fails_the_guardrails(campaign):
    row = score(campaign, variant="on_brand")
    row["disclaimer_present"] = False
    assert not guardrails(row).ok


def test_generated_rows_carry_the_model_that_wrote_them(campaign):
    row = score(campaign, variant="on_brand", model_id="deepseek/deepseek-chat")
    assert row["extraction_model"] == "deepseek/deepseek-chat"


# --- evaluation --------------------------------------------------------------
def test_scorecard_covers_every_target(df, fd, campaign):
    target = build_targets(df, fd)["challenger_style"]
    scorecard = evaluate(score(campaign, variant="challenger_style"), target)
    assert len(scorecard) == len(target.specs)
    assert set(scorecard["result"]) <= {"hit", "miss", "not measured"}


def test_hit_rate_ignores_unmeasured_criteria(df, fd, campaign):
    target = build_targets(df, fd)["on_brand"]
    scorecard = evaluate(score(campaign, variant="on_brand"), target)
    assert 0.0 <= hit_rate(scorecard) <= 1.0


def test_brief_states_the_targets_it_will_be_judged_on(df, fd):
    target = build_targets(df, fd)["challenger_style"]
    prompt = build_brief(df, target, fd).to_prompt()
    for spec in target.specs:
        assert spec.feature in prompt


def test_brief_states_the_counts_the_model_is_judged_on(df, fd):
    """image_count and cta_count are measured from the output, so they must be asked for."""
    target = build_targets(df, fd)["challenger_style"]
    prompt = build_brief(df, target, fd).to_prompt()
    named = {s.feature for s in target.specs}
    if "image_count" in named:
        assert "entries in image_briefs" in prompt
    if "cta_count" in named:
        assert "additional_cta_labels" in prompt


def test_every_cta_is_rendered_and_counted(campaign):
    campaign.additional_cta_labels = ["Learn more", "Discover the rates"]
    features = extract(to_html(campaign), language="en")
    assert features["cta_count"] == 3, "main CTA plus both additional ones"


def test_challenger_brief_carries_competitor_patterns_but_on_brand_does_not(df, fd):
    targets = build_targets(df, fd)
    assert build_brief(df, targets["challenger_style"], fd).competitor_patterns
    assert not build_brief(df, targets["on_brand"], fd).competitor_patterns
