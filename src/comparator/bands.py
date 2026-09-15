"""Fixed-threshold bands that turn a within_language raw value into a
cross_language categorical, same idea as the existing readability_band.

sieg 14/09, new module - Sieg's call (14/09): "convert to band equivalents
like readability_band". Centralised here so fixtures.py (synthetic) and
collection/scraper.py (real) use the exact same cutoffs - duplicating
thresholds in two files is how they silently drift apart.

HONEST LIMITATION, worth restating every time one of these is used: unlike
readability_band (where the underlying FORMULA already normalises for
language), these are fixed universal cutoffs. A French sentence saying the
same thing as an English one typically runs ~15-20% longer, so these bands
REDUCE the cross-language comparability problem, they do not eliminate it.
Good enough for "which bank leans long/short", not for a precise ranking.
"""
from __future__ import annotations


def _band(value: float | int | None, edges: list[tuple[float, str]], default: str) -> str | None:
    """edges: [(upper_bound, label), ...] in ascending order; value < first
    upper_bound gets that label, and so on. `default` covers anything above
    the last edge."""
    if value is None:
        return None
    for upper, label in edges:
        if value < upper:
            return label
    return default


WORD_COUNT_EDGES = [(150, "very_short"), (350, "short"), (600, "medium")]
WORD_COUNT_DEFAULT = "long"

SENTENCE_COUNT_EDGES = [(8, "very_short"), (18, "short"), (35, "medium")]
SENTENCE_COUNT_DEFAULT = "long"

AVG_SENTENCE_LENGTH_EDGES = [(12, "short_sentences"), (20, "medium_sentences")]
AVG_SENTENCE_LENGTH_DEFAULT = "long_sentences"

SECOND_PERSON_RATIO_EDGES = [(0.2, "rarely_direct"), (0.5, "sometimes_direct")]
SECOND_PERSON_RATIO_DEFAULT = "mostly_direct"

FIRST_PERSON_PLURAL_EDGES = [(3, "rare"), (8, "occasional")]
FIRST_PERSON_PLURAL_DEFAULT = "frequent"

DISCLAIMER_WORD_SHARE_EDGES = [(0.05, "minimal"), (0.15, "moderate")]
DISCLAIMER_WORD_SHARE_DEFAULT = "heavy"

TEXT_TO_IMAGE_RATIO_EDGES = [(1.0, "image_heavy"), (3.0, "balanced")]
TEXT_TO_IMAGE_RATIO_DEFAULT = "text_heavy"


def word_count_band(value) -> str | None:
    return _band(value, WORD_COUNT_EDGES, WORD_COUNT_DEFAULT)


def sentence_count_band(value) -> str | None:
    return _band(value, SENTENCE_COUNT_EDGES, SENTENCE_COUNT_DEFAULT)


def avg_sentence_length_band(value) -> str | None:
    return _band(value, AVG_SENTENCE_LENGTH_EDGES, AVG_SENTENCE_LENGTH_DEFAULT)


def second_person_ratio_band(value) -> str | None:
    return _band(value, SECOND_PERSON_RATIO_EDGES, SECOND_PERSON_RATIO_DEFAULT)


def first_person_plural_band(value) -> str | None:
    return _band(value, FIRST_PERSON_PLURAL_EDGES, FIRST_PERSON_PLURAL_DEFAULT)


def disclaimer_word_share_band(value) -> str | None:
    return _band(value, DISCLAIMER_WORD_SHARE_EDGES, DISCLAIMER_WORD_SHARE_DEFAULT)


def text_to_image_ratio_band(value) -> str | None:
    return _band(value, TEXT_TO_IMAGE_RATIO_EDGES, TEXT_TO_IMAGE_RATIO_DEFAULT)
