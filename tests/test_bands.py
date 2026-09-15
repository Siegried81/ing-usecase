"""Tests for src/comparator/bands.py - sieg 14/09, new module, new tests."""
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
    assert bands.text_to_image_ratio_band(0.5) == "image_heavy"
    assert bands.text_to_image_ratio_band(2.0) == "balanced"
    assert bands.text_to_image_ratio_band(5.0) == "text_heavy"


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
    ):
        assert fn(None) is None
