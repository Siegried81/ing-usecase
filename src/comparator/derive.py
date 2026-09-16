"""Recompute the features the dictionary marks as `derived`.

steph 16/09, new module. The dictionary says a derived feature is "computed
from other features in this dictionary. Never entered by hand." Collection
computed them at scrape time and nothing ever recomputed them afterwards - so
the moment the rubric scores were merged in, `aida_coverage_score` and
`persuasion_lever_count` stayed empty and the dataset failed validation on two
features whose inputs were sitting in the same row.

One function, applied after anything that changes a source feature. It never
invents a value: if the inputs are missing the derived feature stays missing,
which is the honest outcome and what the validator will report.
"""

from __future__ import annotations

import pandas as pd

from comparator import bands
from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.schema import parse_list

AIDA_STAGES = ("aida_attention", "aida_interest", "aida_desire", "aida_action")

_READABILITY_EDGES = [(90, "very_easy"), (70, "easy"), (50, "medium"), (30, "hard")]

# derived feature -> (source feature, function)
BAND_RULES = {
    "word_count_band": ("word_count", bands.word_count_band),
    "sentence_count_band": ("sentence_count", bands.sentence_count_band),
    "avg_sentence_length_band": ("avg_sentence_length", bands.avg_sentence_length_band),
    "second_person_ratio_band": ("second_person_ratio", bands.second_person_ratio_band),
    "first_person_plural_band": ("first_person_plural_count", bands.first_person_plural_band),
    "disclaimer_word_share_band": ("disclaimer_word_share", bands.disclaimer_word_share_band),
    "text_to_image_ratio_band": ("text_to_image_ratio", bands.text_to_image_ratio_band),
}


def _readability_band(score) -> str | None:
    if score is None or pd.isna(score):
        return None
    return next((label for edge, label in _READABILITY_EDGES if score >= edge), "very_hard")


def _truthy(value) -> bool | None:
    """Accept the several shapes a boolean takes across CSV round-trips."""
    if value is None or (isinstance(value, float) and pd.isna(value)) or value is pd.NA:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "yes", "1", "1.0", "t", "y"}:
        return True
    if text in {"false", "no", "0", "0.0", "f", "n"}:
        return False
    return None


def recompute_derived(df: pd.DataFrame, fd: FeatureDictionary | None = None) -> pd.DataFrame:
    """Fill every derived feature from its sources. Missing inputs stay missing."""
    fd = fd or load_dictionary()
    out = df.copy()

    for target, (source, fn) in BAND_RULES.items():
        if target in fd and source in out.columns:
            values = pd.to_numeric(out[source], errors="coerce")
            out[target] = [fn(v) if pd.notna(v) else None for v in values]

    if "readability_band" in fd and "readability_score" in out.columns:
        scores = pd.to_numeric(out["readability_score"], errors="coerce")
        out["readability_band"] = [_readability_band(v) for v in scores]

    if "has_animation" in fd and "animated_asset_count" in out.columns:
        counts = pd.to_numeric(out["animated_asset_count"], errors="coerce")
        out["has_animation"] = [None if pd.isna(v) else bool(v > 0) for v in counts]

    if "aida_coverage_score" in fd and all(s in out.columns for s in AIDA_STAGES):
        def coverage(row) -> object:
            flags = [_truthy(row[s]) for s in AIDA_STAGES]
            # All four must be known: "2 of the 4 we bothered to score" is not a score.
            return pd.NA if any(f is None for f in flags) else int(sum(flags))

        out["aida_coverage_score"] = out.apply(coverage, axis=1)

    if "persuasion_lever_count" in fd and "persuasion_levers" in out.columns:
        def count(cell) -> object:
            if cell is None or (isinstance(cell, float) and pd.isna(cell)) or cell is pd.NA:
                return pd.NA
            return len(set(parse_list(cell)))

        out["persuasion_lever_count"] = out["persuasion_levers"].map(count)

    return out
