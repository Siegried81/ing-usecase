"""The bridge between a collected dataset and the human rubric scores.

New module. The first real collection run stops at exactly this
gap: 12 core, required features are rubric-scored by a person, so a collected
dataset can never pass strict validation on its own. There was no mechanism to
get those scores in.

SCOPE CHANGE. The project now runs on ONE judged sheet, by one named
person, and the inter-rater layer is gone: no agreement, no Cohen's kappa, no
disagreement table, no model-written rubric to compare against. That was a
deliberate narrowing, not an omission - this is a proof of concept, and
single-judge bias is a question for the real product. limitations.py says so in
those words, and next_steps() lists it as future work.

Two jobs remain:

  make_sheet  one scoring sheet, pre-filled with page_id, bank and the
              screenshot path, so a rater scores while looking at the page
              rather than from memory.
  merge       that sheet back into the dataset, one value per page.

Scores are never invented here. A sheet that is not filled in stays empty, and
the schema validator says the feature is missing - which is the honest outcome.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from comparator.dictionary import FeatureDictionary, load_dictionary

# Columns copied into the sheet so a rater has the page in front of them.
CONTEXT_COLUMNS = ("page_id", "bank", "bank_category", "product_family",
                   "language", "url", "screenshot_path", "capture_quality")

RATER_COLUMN = "rater"


def rubric_features(fd: FeatureDictionary | None = None) -> list:
    """Every feature a human has to score."""
    fd = fd or load_dictionary()
    return fd.select(extraction="rubric")


def make_sheet(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    rater: str = "",
    skip_unusable: bool = True,
) -> pd.DataFrame:
    """Build an empty scoring sheet for one rater.

    Unusable captures are dropped by default - asking someone to score the tone
    of a maintenance page wastes their afternoon and pollutes the average.
    """
    fd = fd or load_dictionary()
    rows = df
    if skip_unusable and "capture_quality" in rows.columns:
        rows = rows[rows["capture_quality"] != "unusable"]

    context = [c for c in CONTEXT_COLUMNS if c in rows.columns]
    sheet = rows[context].copy()
    sheet.insert(0, RATER_COLUMN, rater)
    for feature in rubric_features(fd):
        sheet[feature.name] = pd.NA
    return sheet.reset_index(drop=True)


def sheet_guide(fd: FeatureDictionary | None = None) -> str:
    """What each rubric feature means and what may be entered, as markdown.

    Generated from the dictionary so the guide a rater reads and the values the
    validator accepts cannot drift apart.
    """
    fd = fd or load_dictionary()
    lines = [
        "# Rubric scoring guide",
        "",
        "> Generated from `config/feature_dictionary.yaml`. Score each page with the",
        "> screenshot open. Leave a cell blank rather than guessing — a missing score is",
        "> reported honestly; an invented one is not.",
        "",
        "One named person scores every page against these scales. No second rater",
        "and no reliability measure: that is the chosen scope of this proof of",
        "concept, and single-judge bias is recorded as future work rather than",
        "answered here. Write the page id you scored from, and leave a cell blank",
        "whenever the page does not give you the evidence to fill it.",
        "",
    ]
    for feature in rubric_features(fd):
        lines += [f"## `{feature.name}`", "", " ".join(feature.definition.split()), ""]
        if feature.values:
            lines += ["Allowed values:", ""]
            lines += [f"- `{v}`" for v in feature.values]
            lines.append("")
        elif feature.range:
            lines += [f"Enter a whole number from **{feature.min}** to **{feature.max}**.", ""]
        if feature.rubric:
            lines.append("| Level | Means |")
            lines.append("| --- | --- |")
            for level, text in sorted(feature.rubric.items()):
                lines.append(f"| **{level}** | {' '.join(str(text).split())} |")
            lines.append("")
        if feature.notes:
            lines += [f"*{' '.join(feature.notes.split())}*", ""]
    return "\n".join(lines)


def _single_value(values: pd.Series, feature) -> object:
    """The one judged value for a page.

    This was _consensus(), averaging numeric scores and taking the
    majority for categoricals across several raters. With one sheet there is
    nothing to reconcile, and the averaging was only ever safe because
    agreement() reported the spread it hid - that reporting is gone, so
    averaging would now bury a disagreement instead of surfacing it. If a page
    somehow carries more than one row, the first non-empty value wins and the
    rest are ignored rather than blended into a number nobody wrote.
    """
    clean = values.dropna()
    return pd.NA if clean.empty else clean.iat[0]


def merge_scores(
    df: pd.DataFrame,
    sheets: list[pd.DataFrame],
    fd: FeatureDictionary | None = None,
) -> pd.DataFrame:
    """Fold completed sheets into the dataset, one consensus value per page."""
    fd = fd or load_dictionary()
    if not sheets:
        return df.copy()

    combined = pd.concat(sheets, ignore_index=True)
    features = [f for f in rubric_features(fd) if f.name in combined.columns]

    consensus = {}
    for page_id, group in combined.groupby("page_id", observed=True):
        consensus[page_id] = {f.name: _single_value(group[f.name], f) for f in features}

    out = df.copy()
    for feature in features:
        out[feature.name] = out["page_id"].map(
            lambda pid, name=feature.name: consensus.get(pid, {}).get(name, pd.NA)
        )

    # Merging rubric scores changes the inputs of derived features
    # (aida_coverage_score, persuasion_lever_count). Nothing recomputed them, so
    # the merged dataset failed validation on two features whose sources were
    # sitting in the same row.
    from comparator.derive import recompute_derived

    return recompute_derived(out, fd)


def _read_sheet(path: str | Path) -> pd.DataFrame:
    """Read one scoring sheet, sniffing comma vs semicolon.

    These sheets get hand-edited in Excel between sessions, and
    Excel's CSV export defaults to ";" under a French/Belgian locale - one
    sheet has already flipped between "," and ";" more than once. Sniffing
    the header line rather than assuming either survives the next re-save.
    """
    path = Path(path)
    header = path.read_text(encoding="utf-8").splitlines()[0]
    sep = ";" if header.count(";") > header.count(",") else ","
    frame = pd.read_csv(path, sep=sep)
    return _normalise_lists(frame)


def _normalise_lists(frame: pd.DataFrame, fd: FeatureDictionary | None = None) -> pd.DataFrame:
    """Accept a comma-separated list where the schema wants pipes.

    A rater typing "buttons, background" means the same two values as
    "buttons|background", but the validator rejects the first and the whole
    dataset fails to load on a separator. Normalising on read keeps the
    judgement and drops the punctuation argument.
    """
    fd = fd or load_dictionary()
    for feature in rubric_features(fd):
        if not feature.is_list or feature.name not in frame.columns:
            continue
        frame[feature.name] = frame[feature.name].apply(
            lambda cell: cell if not isinstance(cell, str) or "," not in cell
            else "|".join(part.strip() for part in cell.split(",") if part.strip())
        )
    return frame


def read_sheets(paths: list[str | Path]) -> list[pd.DataFrame]:
    return [_read_sheet(p) for p in paths]
