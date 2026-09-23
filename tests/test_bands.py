"""Tests for src/comparator/bands.py - New module, new tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import bands  # noqa: E402


def test_word_count_band_edges():
    assert bands.word_count_band(0) == "very_short"
    assert bands.word_count_band(149) == "very_short"
    assert bands.word_count_band(150) == "short"
    assert bands.word_count_band(349) == "short"
    assert bands.word_count_band(350) == "medium"
    assert bands.word_count_band(599) == "medium"
    assert bands.word_count_band(600) == "long"
    assert bands.word_count_band(10_000) == "long"


def test_word_count_band_none_stays_none():
    assert bands.word_count_band(None) is None


def test_text_to_image_ratio_band_edges():
    # Rescaled with the edges. The feature is WORDS PER IMAGE
    # (scraper.py), not an area ratio - 0.5 would be a page with one word per
    # two images, which cannot occur. See bands.py for the recalibration note.
    assert bands.text_to_image_ratio_band(20.0) == "image_heavy"
    assert bands.text_to_image_ratio_band(70.0) == "balanced"
    assert bands.text_to_image_ratio_band(150.0) == "text_heavy"


def test_text_to_image_bands_separate_the_two_business_models():
    """The band only earns its place if it does not collapse to one value."""
    assert bands.text_to_image_ratio_band(25.0) != bands.text_to_image_ratio_band(120.0)


def test_second_person_ratio_band_edges():
    assert bands.second_person_ratio_band(0.1) == "rarely_direct"
    assert bands.second_person_ratio_band(0.3) == "sometimes_direct"
    assert bands.second_person_ratio_band(0.8) == "mostly_direct"


def test_every_band_function_handles_none():
    # every band function must degrade to None, not raise, on a missing value
    for fn in (
        bands.word_count_band, bands.sentence_count_band, bands.avg_sentence_length_band,
        bands.second_person_ratio_band, bands.first_person_plural_band,
        bands.disclaimer_word_share_band, bands.text_to_image_ratio_band,
        bands.readability_band,
    ):
        assert fn(None) is None


# Audit finding (LOW): readability_band was duplicated identically
# in collection/scraper.py and derive.py - now both call this one function.
def test_readability_band_edges():
    assert bands.readability_band(95) == "very_easy"
    assert bands.readability_band(90) == "very_easy"
    assert bands.readability_band(89) == "easy"
    assert bands.readability_band(70) == "easy"
    assert bands.readability_band(69) == "medium"
    assert bands.readability_band(50) == "medium"
    assert bands.readability_band(49) == "hard"
    assert bands.readability_band(30) == "hard"
    assert bands.readability_band(29) == "very_hard"
    assert bands.readability_band(0) == "very_hard"
