"""The bridge between a collected dataset and the human rubric scores.

steph 16/09, new module. The first real collection run stops at exactly this
gap: 12 core, required features are rubric-scored by a person, so a collected
dataset can never pass strict validation on its own. There was no mechanism to
get those scores in - the plan books a joint scoring session for Day 5 but
nothing said what people would actually fill in.

Three jobs:

  emit      one scoring sheet per rater, pre-filled with page_id, bank, and the
            screenshot path, so a rater scores while looking at the page rather
            than from memory.
  merge     completed sheets back into the dataset, averaging numeric scores
            and taking the majority for categoricals.
  agreement how much the raters disagreed, per feature.

That last one is not a nicety. NFR-05 requires judgement-based features to be
"scored independently by >=2 people on a sample, and the disagreement
reported". Reporting agreement is what separates a defensible score from one
person's taste, and it is the number the data audience will ask for.

Scores are never invented here. A sheet that is not filled in stays empty, and
the schema validator says the feature is missing - which is the honest outcome.
"""

from __future__ import annotations

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
        "Two people score the same pages independently, then disagreement is measured",
        "(`python3 scripts/rubric_sheet.py agreement`). Do not confer while scoring —",
        "the disagreement number is only meaningful if the scores are independent.",
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


def _consensus(values: pd.Series, feature) -> object:
    """One agreed value from several raters."""
    clean = values.dropna()
    if clean.empty:
        return pd.NA
    if feature.is_numeric:
        return round(float(pd.to_numeric(clean, errors="coerce").dropna().mean()), 2)
    return clean.astype("string").mode().iat[0]  # majority; ties resolve to first alphabetically


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
        consensus[page_id] = {f.name: _consensus(group[f.name], f) for f in features}

    out = df.copy()
    for feature in features:
        out[feature.name] = out["page_id"].map(
            lambda pid, name=feature.name: consensus.get(pid, {}).get(name, pd.NA)
        )
    return out


@dataclass
class Agreement:
    """How much two or more raters disagreed, per feature (NFR-05)."""

    table: pd.DataFrame

    def render(self) -> str:
        if self.table.empty:
            return "No feature was scored by more than one rater - agreement cannot be measured."
        lines = ["Inter-rater agreement (NFR-05)", ""]
        lines.append(self.table.to_string(index=False))
        weak = self.table[self.table["agreement"] < 0.6]["feature"].tolist()
        if weak:
            lines += ["", f"Weak agreement (<60%): {weak}.",
                      "Tighten the rubric wording for these before trusting them in a finding."]
        return "\n".join(lines)


def agreement(sheets: list[pd.DataFrame], fd: FeatureDictionary | None = None) -> Agreement:
    """Per-feature agreement across raters.

    Categorical: share of pages where every rater chose the same value.
    Numeric: share of pages where all raters landed within one point, which is
    the useful question for a 1-5 scale - exact-match would understate agreement
    between a 3 and a 4 that are one considered step apart.
    """
    fd = fd or load_dictionary()
    if len(sheets) < 2:
        return Agreement(pd.DataFrame(columns=["feature", "pages", "agreement", "basis"]))

    combined = pd.concat(sheets, ignore_index=True)
    rows = []
    for feature in rubric_features(fd):
        if feature.name not in combined.columns:
            continue
        agreed, counted = 0, 0
        for _, group in combined.groupby("page_id", observed=True):
            values = group[feature.name].dropna()
            if len(values) < 2:
                continue
            counted += 1
            if feature.is_numeric:
                numeric = pd.to_numeric(values, errors="coerce").dropna()
                if not numeric.empty and (numeric.max() - numeric.min()) <= 1:
                    agreed += 1
            elif values.astype("string").nunique() == 1:
                agreed += 1
        if counted:
            rows.append({
                "feature": feature.name,
                "pages": counted,
                "agreement": round(agreed / counted, 2),
                "basis": "within 1 point" if feature.is_numeric else "exact match",
            })
    table = pd.DataFrame(rows)
    if not table.empty:
        table = table.sort_values("agreement").reset_index(drop=True)
    return Agreement(table)


def read_sheets(paths: list[str | Path]) -> list[pd.DataFrame]:
    return [pd.read_csv(p) for p in paths]
