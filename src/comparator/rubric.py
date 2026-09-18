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

    # steph 16/09: merging rubric scores changes the inputs of derived features
    # (aida_coverage_score, persuasion_lever_count). Nothing recomputed them, so
    # the merged dataset failed validation on two features whose sources were
    # sitting in the same row.
    from comparator.derive import recompute_derived

    return recompute_derived(out, fd)


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


# -----------------------------------------------------------------------------
# sieg 16/09, new. agreement() above reports raw % match - useful, but it does
# not correct for chance. Two raters who both score mostly "3" on a 1-5 scale
# will show high raw agreement even scoring at random, because there are only
# 5 buckets to land in. NFR-05 asks for the disagreement to be reported
# honestly, and a chance-inflated number is not honest. Cohen's kappa corrects
# for exactly this: kappa = (observed - expected-by-chance) / (1 - expected).
#
# One function for human-vs-human AND human-vs-model, deliberately: the model
# is just another rater in its own sheet (rubric_model.py), so the same pair-
# wise computation applies without a special case for which "rater" it is.
def _cohens_kappa(a: pd.Series, b: pd.Series, *, ordinal: bool) -> float | None:
    """Pairwise Cohen's kappa between two aligned rating series.

    `ordinal=True` (numeric 1-5 scales) uses linear weights, so a 3-vs-4
    disagreement counts as a smaller miss than a 1-vs-5 one - matching the
    "within one point" leniency agreement() already applies, but as a real
    statistic instead of a fixed threshold. `ordinal=False` (categoricals) is
    unweighted: every mismatch counts the same, there is no natural distance
    between e.g. "hero_stacked" and "card_grid".
    """
    paired = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(paired) < 2:
        return None

    categories = sorted(set(paired["a"]) | set(paired["b"]), key=str)
    k = len(categories)
    if k < 2:
        return None  # every rater picked the same single value - kappa is undefined, not 1.0
    index = {c: i for i, c in enumerate(categories)}

    if ordinal:
        weights = [[abs(i - j) / (k - 1) for j in range(k)] for i in range(k)]
    else:
        weights = [[0.0 if i == j else 1.0 for j in range(k)] for i in range(k)]

    observed = [[0.0] * k for _ in range(k)]
    for av, bv in zip(paired["a"], paired["b"]):
        observed[index[av]][index[bv]] += 1
    n = len(paired)

    row_marg = [sum(row) / n for row in observed]
    col_marg = [sum(observed[i][j] for i in range(k)) / n for j in range(k)]

    p_o = sum(weights[i][j] * observed[i][j] / n for i in range(k) for j in range(k))
    p_e = sum(weights[i][j] * row_marg[i] * col_marg[j] for i in range(k) for j in range(k))

    if p_e >= 1.0:
        return None  # degenerate: expected chance disagreement is total, kappa undefined
    # p_o/p_e above are weighted DISAGREEMENT (weight 0 = perfect match), so
    # kappa is 1 - ratio, not (p_o - p_e) / (1 - p_e) as for the unweighted form.
    return round(1 - (p_o / p_e), 3) if p_e > 0 else None


@dataclass
class KappaAgreement:
    """Chance-corrected agreement per feature, per pair of raters (NFR-05)."""

    table: pd.DataFrame

    def render(self) -> str:
        if self.table.empty:
            return "Not enough overlapping scores to compute kappa for any feature."
        lines = ["Cohen's kappa - chance-corrected agreement (NFR-05)", "",
                 self.table.to_string(index=False)]
        # Landis & Koch (1977) - the standard reference bands, not our invention.
        weak = self.table[self.table["kappa"] < 0.4]
        if not weak.empty:
            lines += ["", "Below 0.4 (fair or worse, Landis & Koch): "
                      f"{list(zip(weak['feature'], weak['raters']))}. "
                      "Raw % agreement on these may look fine while being close to chance."]
        return "\n".join(lines)


def kappa_agreement(sheets: list[pd.DataFrame], fd: FeatureDictionary | None = None) -> KappaAgreement:
    """Cohen's kappa for every feature, for every pair of raters present.

    Works the same whether the "raters" are two humans, or a human and the
    model's own sheet (rubric_model.py) - it only ever sees a rater column
    and a set of per-page scores, never who or what produced them.
    """
    fd = fd or load_dictionary()
    if len(sheets) < 2:
        return KappaAgreement(pd.DataFrame(columns=["feature", "raters", "pages", "kappa"]))

    combined = pd.concat(sheets, ignore_index=True)
    raters = sorted(combined[RATER_COLUMN].dropna().unique())
    rows = []
    for feature in rubric_features(fd):
        if feature.name not in combined.columns:
            continue
        wide = combined.pivot_table(
            index="page_id", columns=RATER_COLUMN, values=feature.name, aggfunc="first"
        )
        for i, r1 in enumerate(raters):
            for r2 in raters[i + 1:]:
                if r1 not in wide.columns or r2 not in wide.columns:
                    continue
                k = _cohens_kappa(wide[r1], wide[r2], ordinal=feature.is_numeric)
                if k is None:
                    continue
                pages = wide[[r1, r2]].dropna().shape[0]
                rows.append({"feature": feature.name, "raters": f"{r1} vs {r2}",
                             "pages": pages, "kappa": k})
    table = pd.DataFrame(rows)
    if not table.empty:
        table = table.sort_values("kappa").reset_index(drop=True)
    return KappaAgreement(table)


def read_sheets(paths: list[str | Path]) -> list[pd.DataFrame]:
    return [pd.read_csv(p) for p in paths]


# -----------------------------------------------------------------------------
# Siegried's Day 5 disagreement table, generated from the sheets
# -----------------------------------------------------------------------------
# steph 16/09. docs/day5_scoring_disagreement_template.md is a markdown table
# with one column per rater, filled in by hand after the session. That is a
# second place for the same numbers to live, and the file itself says its
# summary row is what goes in the deck - so a transcription slip would land
# straight in front of the stakeholders.
#
# The sheets already hold every score. This renders Siegried's table FROM them,
# so the deck number is computed rather than copied. The "why" and "rubric fix"
# columns stay empty on purpose: those are the human judgements the session
# exists to produce, and nothing here can invent them.
def disagreement_table(
    sheets: list[pd.DataFrame],
    fd: FeatureDictionary | None = None,
    *,
    page_ids: list[str] | None = None,
) -> str:
    """Render the Day 5 disagreement table from the completed scoring sheets."""
    fd = fd or load_dictionary()
    if not sheets:
        return "No scoring sheets found. Run `scripts/rubric_sheet.py emit` first."

    combined = pd.concat(sheets, ignore_index=True)
    raters = sorted(str(r) for r in combined[RATER_COLUMN].dropna().unique())
    pages = page_ids or sorted(str(p) for p in combined["page_id"].dropna().unique())
    features = [f for f in rubric_features(fd) if f.name in combined.columns]

    lines = [
        "# Day 5 — joint rubric scoring, disagreement tracking",
        "",
        "> Generated from the scoring sheets by `scripts/rubric_sheet.py report`.",
        "> Scores are read from the CSVs, never retyped. The last two columns are",
        "> for the session itself — nothing can fill those in for you.",
        "",
        f"**Raters:** {', '.join(raters) or 'none'}  |  **Pages scored:** {len(pages)}",
        "",
    ]

    for page in pages:
        rows = combined[combined["page_id"] == page]
        bank = rows["bank"].dropna().iloc[0] if "bank" in rows and not rows["bank"].dropna().empty else "?"
        lines += [f"## {page}  ({bank})", "",
                  "| Feature | " + " | ".join(raters) + " | Agree? | If disagree: why | Rubric fix needed? |",
                  "| --- | " + " | ".join("---" for _ in raters) + " | --- | --- | --- |"]

        for feature in features:
            values = []
            for rater in raters:
                cell = rows[rows[RATER_COLUMN].astype("string") == rater][feature.name].dropna()
                # sieg 18/09: list-valued features (accent_locations, persuasion_levers)
                # are pipe-separated, and "|" is the Markdown table delimiter - an
                # unescaped value broke every table row after it once a rater actually
                # filled in a multi-item list (bug pre-dates this fix; only showed up
                # once a real value produced more than one list item).
                values.append("" if cell.empty else str(cell.iat[0]).replace("|", "\\|"))

            scored = [v for v in values if v]
            if len(scored) < 2:
                agree = "—"
            elif feature.is_numeric:
                numbers = pd.to_numeric(pd.Series(scored), errors="coerce").dropna()
                agree = "Y" if not numbers.empty and (numbers.max() - numbers.min()) <= 1 else "N"
            else:
                agree = "Y" if len(set(scored)) == 1 else "N"

            lines.append(f"| `{feature.name}` | " + " | ".join(values) + f" | {agree} |  |  |")
        lines.append("")

    # steph 16/09: raw % agreement AND Sieg's chance-corrected kappa. His own
    # note is the reason both belong here - "raw % agreement on these may look
    # fine while being close to chance" - and this table is what goes in the
    # deck, so it should not carry only the flattering half.
    lines += ["## Summary — what goes in the deck", "",
              "```", agreement(sheets, fd).render(), "```", "",
              "```", kappa_agreement(sheets, fd).render(), "```", ""]
    if len(sheets) < 2:
        lines += ["Only one rater has scored so far, so no agreement figure exists yet. "
                  "NFR-05 needs at least two independent raters.", ""]
    return "\n".join(lines)
