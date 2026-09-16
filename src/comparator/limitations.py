"""D-09 - Limitations & next steps, read off the dataset rather than remembered.

steph 16/09, new module. The RACI puts D-09 on me, and it is the deliverable
most likely to be written from memory at 11pm on Day 9 - which is exactly when
the inconvenient limitations get forgotten.

So it is generated from the dataset that actually exists. If two captures
failed, it says which two and why. If the rubric scores are missing, it says
so. If a bank is absent, it says which question that makes unanswerable. A
limitation nobody can quietly drop is worth more than a well-written paragraph.

Nothing in here is aspirational. Every line is a fact about the data in hand,
or a known property of the method that no amount of collecting will fix.
"""

from __future__ import annotations

import pandas as pd

from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.rubric import rubric_features

FOCUS_BANK = "ing"
# Below this, group means are anecdotes with error bars we cannot compute.
THIN_GROUP = 3


def _bullet(text: str) -> str:
    return f"- {text}"


def _severity_block(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return [f"### {title}", ""] + [_bullet(i) for i in items] + [""]


def assess(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    focus: str = FOCUS_BANK,
) -> dict:
    """Collect every limitation the dataset itself can demonstrate."""
    fd = fd or load_dictionary()
    blocking: list[str] = []
    material: list[str] = []
    standing: list[str] = []

    banks = df.drop_duplicates("bank")
    n_banks = len(banks)
    usable = df
    if "capture_quality" in df.columns:
        usable = df[df["capture_quality"] != "unusable"]

    # --- captures that are not the page we meant to collect ------------------
    if "capture_quality" in df.columns:
        broken = df[df["capture_quality"] == "unusable"]
        for _, row in broken.iterrows():
            blocking.append(
                f"**{row['bank']}** could not be captured: {row.get('capture_quality_note', 'unusable')}. "
                f"Source: {row.get('url', 'n/a')}. The row is excluded; the bank is effectively absent."
            )
        suspect = df[df["capture_quality"] == "suspect"]
        for _, row in suspect.iterrows():
            material.append(
                f"**{row['bank']}** capture is thin but plausible: {row.get('capture_quality_note', '')}. "
                "Included, but a human should confirm it is the real campaign page."
            )

    # --- the focus bank is the whole point -----------------------------------
    usable_banks = set(usable["bank"]) if "bank" in usable.columns else set()
    if focus not in usable_banks:
        blocking.append(
            f"**{focus.upper()} is not in the usable data.** BO-01 (position {focus.upper()}) and "
            f"BO-02 (traditional or challenger) cannot be answered at all until a usable "
            f"{focus} page is collected. Every other finding is about the market without us in it."
        )

    # --- group sizes ---------------------------------------------------------
    if "bank_category" in usable.columns:
        counts = usable.drop_duplicates("bank")["bank_category"].value_counts().to_dict()
        for category in ("traditional", "challenger"):
            n = counts.get(category, 0)
            if n < THIN_GROUP:
                material.append(
                    f"Only **{n} {category} bank(s)** in the usable data. A group mean over "
                    f"{n} bank(s) is an anecdote; effect sizes between the groups are "
                    "descriptive shorthand, not evidence of a market pattern."
                )

    # --- comparability: like for like ----------------------------------------
    if "product_family" in usable.columns:
        families = sorted(usable["product_family"].dropna().unique())
        if len(families) > 1:
            material.append(
                f"The usable pages span **{len(families)} different product families** ({families}). "
                "DR-04 requires comparisons within one family — a mortgage page and a current-account "
                "page differ because the products differ, not because the banks communicate differently. "
                "Any cross-bank claim from this dataset is confounded by product."
            )

    if "language" in usable.columns:
        languages = sorted(usable["language"].dropna().unique())
        if len(languages) > 1:
            material.append(
                f"Pages are in **{len(languages)} languages** ({languages}). Word counts and readability "
                "are not comparable across languages; only the banded versions travel."
            )

    # --- human scores --------------------------------------------------------
    missing_rubric = [
        f.name for f in rubric_features(fd)
        if f.name not in usable.columns or usable[f.name].isna().all()
    ]
    if missing_rubric:
        blocking.append(
            f"**{len(missing_rubric)} of {len(rubric_features(fd))} rubric features are unscored** "
            f"({missing_rubric[:4]}{' ...' if len(missing_rubric) > 4 else ''}). "
            "Every judgement-based dimension — tone, layout archetype, AIDA coverage, persuasion "
            "levers — is therefore absent from the comparison. Run the Day 5 scoring session "
            "(`scripts/rubric_sheet.py emit`)."
        )
    elif "capture_quality" in usable.columns:
        standing.append(
            "Rubric features carry the opinion of the people who scored them. Inter-rater "
            "agreement is reported by `scripts/rubric_sheet.py agreement` and belongs in the "
            "data presentation (NFR-05)."
        )

    # --- one judge per bank --------------------------------------------------
    if "extraction_model" in usable.columns:
        models = sorted(str(m) for m in usable["extraction_model"].dropna().unique())
        if len(models) > 1:
            material.append(
                f"Model-assisted features were produced by **more than one model** ({models}). "
                "Part of any difference between those banks is a difference between two LLMs (NFR-02)."
            )
        elif models:
            standing.append(
                f"Model-assisted features were all produced by `{models[0]}`, at temperature 0. "
                "They carry that model's judgement, validated against human labels only on a sample."
            )

    # --- one moment in time --------------------------------------------------
    if "captured_at" in usable.columns:
        stamps = pd.to_datetime(usable["captured_at"], errors="coerce", utc=True).dropna()
        if not stamps.empty:
            standing.append(
                f"Every conclusion is valid for the capture window "
                f"**{stamps.min():%Y-%m-%d} to {stamps.max():%Y-%m-%d}** and no later. Campaign "
                "pages change without notice (DR-05)."
            )

    # --- method limits no amount of collecting fixes -------------------------
    standing += [
        "**No performance data exists in this project.** Nothing links a design choice to a click, "
        "a conversion or a sale. Every recommendation is a hypothesis ING could test, never a cause "
        "(PRD 5.2).",
        "Only the open web is covered. Social media, in-app and email banners are out of scope and "
        "may well be where a bank's real communication happens.",
        "`total_image_area_ratio` sums image bounding boxes, so overlapping images are counted twice "
        "and the value is capped at 1.0. `above_fold_element_count` depends on what counts as an "
        "element. Both are exact about geometry and approximate about meaning.",
        "The generated campaigns are **not reproducible**: the same brief at temperature 0 produced "
        "different copy and a different hit rate on five separate runs. A committed generated "
        "artefact is one sample, not the output.",
        "Hitting a generation target shows the model followed instructions. It says nothing about "
        "whether the campaign would perform better (plan risk P-08).",
    ]

    return {
        "n_banks": n_banks,
        "n_usable_banks": len(usable_banks),
        "n_pages": len(df),
        "n_usable_pages": len(usable),
        "blocking": blocking,
        "material": material,
        "standing": standing,
    }


NEXT_STEPS = [
    ("Collect a usable ING page", "Nothing about ING's position can be said without it. The current "
     "capture is a JavaScript shell; a longer settle time or a different entry URL is the first thing to try."),
    ("Fix the product-family mix", "Collect the same product family across every bank. The current "
     "targets file is a pipeline test, not a comparable scope (DR-04)."),
    ("Run the Day 5 scoring session", "13 rubric features, two independent raters, then report "
     "agreement. Until then the comparison is automatic features only."),
    ("Handle consent walls in collection", "Two of six captures were defeated by a page that never "
     "rendered its content. Detect and dismiss the consent layer, or record the bank as uncollectable."),
    ("Make generation reproducible", "Store the generated artefact and evaluate that, rather than "
     "regenerating on every run."),
    ("Extend beyond the open web", "Social media and in-app banners, using the same feature framework — "
     "the extension the brief names, and the reason the framework is worth keeping."),
]


def render(assessment: dict, *, synthetic: bool = False) -> str:
    """Render D-09 as markdown."""
    lines = [
        "# Limitations & next steps",
        "",
        "*Deliverable D-09. Generated from the dataset by `scripts/run_analysis.py`, so it "
        "describes the data that actually exists rather than the data we meant to collect.*",
        "",
        f"**{assessment['n_usable_pages']} usable page(s) across "
        f"{assessment['n_usable_banks']} bank(s)**, from {assessment['n_pages']} collected.",
        "",
    ]
    if synthetic:
        lines += ["> **This run used synthetic fixture data.** The limitations below are real "
                  "properties of the pipeline, but the counts describe invented rows.", ""]

    lines += ["## What this analysis cannot support", ""]
    lines += _severity_block("Blocking — a question cannot be answered at all", assessment["blocking"])
    lines += _severity_block("Material — findings survive, but weakened", assessment["material"])
    lines += _severity_block("Standing — true regardless of how much we collect", assessment["standing"])

    lines += ["## Next steps", ""]
    for i, (title, detail) in enumerate(NEXT_STEPS, 1):
        lines.append(f"{i}. **{title}.** {detail}")
    lines.append("")
    return "\n".join(lines)
