"""Tests for the capture quality gate (steph 16/09).

The two cases at the top are real: they are the rows the first live collection
run produced, and they are why this module exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.collection.quality import (  # noqa: E402
    MIN_PLAUSIBLE_WORDS,
    assess_capture,
)


def _row(**overrides) -> dict:
    base = dict(word_count=600, image_count=6, cta_count=3,
                page_height_px=4000, meta_title="Épargner - Banque")
    base.update(overrides)
    return base


# --- the two real failures ---------------------------------------------------
def test_the_real_ing_shell_is_caught():
    """ing.be rendered 5730px tall and produced 16 words: the <title>, twice."""
    report = assess_capture(
        _row(word_count=16, image_count=0, cta_count=0, page_height_px=5730,
             meta_title="Épargner en tant que particulier - ING Belgique"),
        "Épargner en tant que particulier - ING Belgique "
        "Épargner en tant que particulier - ING Belgique",
    )
    assert report.verdict == "unusable"
    assert not report.usable
    assert any("only the page title" in r for r in report.reasons)


def test_the_real_bnp_maintenance_page_is_caught():
    report = assess_capture(
        _row(word_count=87, image_count=4, cta_count=1, page_height_px=925),
        "Oops! The website is now unvailable. We are currently doing maintenance work.",
    )
    assert report.verdict == "unusable"
    assert any("maintenance" in r for r in report.reasons)


# --- must not fire on real pages ---------------------------------------------
def test_a_normal_campaign_page_passes():
    report = assess_capture(_row(), "A long page about a savings account. " * 60)
    assert report.verdict == "ok"
    assert report.usable


def test_a_short_challenger_page_is_suspect_not_discarded():
    """A real challenger landing page can carry 150 words. Flag, do not drop."""
    report = assess_capture(
        _row(word_count=110, image_count=9, cta_count=4),
        "Your money, your terms. " * 20,
    )
    assert report.verdict == "suspect"
    assert report.usable, "a human decides on this one, the pipeline does not"


# --- individual signals ------------------------------------------------------
def test_essentially_no_text_is_unusable_whatever_else_is_true():
    assert assess_capture(_row(word_count=10), "tiny").verdict == "unusable"


def test_tall_page_with_almost_no_text_is_flagged():
    report = assess_capture(_row(word_count=60, page_height_px=6000), "short " * 60)
    assert report.verdict in {"suspect", "unusable"}
    assert any("shell or consent wall" in r for r in report.reasons)


def test_no_images_and_no_ctas_is_flagged():
    report = assess_capture(_row(image_count=0, cta_count=0), "words " * 600)
    assert any("no images and no calls to action" in r for r in report.reasons)


def test_error_phrases_are_matched_in_french_and_dutch():
    for text in ("Le site est temporairement indisponible",
                 "De pagina is tijdelijk niet beschikbaar"):
        assert assess_capture(_row(), text).verdict == "unusable"


def test_consent_wording_alone_does_not_condemn_a_long_page():
    """Every European bank page mentions cookies. That is not a broken capture."""
    text = "We use cookies. " + "Real content about a term account. " * 80
    assert assess_capture(_row(word_count=700), text).verdict == "ok"


def test_the_note_is_readable_for_the_limitations_section():
    report = assess_capture(_row(word_count=5), "x")
    assert report.note() and "only 5 words" in report.note()


def test_a_clean_row_says_so_rather_than_being_silent():
    assert assess_capture(_row(), "words " * 500).note() == "looks like a campaign page"


def test_plausibility_floor_is_the_boundary():
    below = assess_capture(_row(word_count=MIN_PLAUSIBLE_WORDS - 1), "w " * 200)
    at = assess_capture(_row(word_count=MIN_PLAUSIBLE_WORDS), "w " * 200)
    assert below.verdict == "suspect"
    assert at.verdict == "ok"
