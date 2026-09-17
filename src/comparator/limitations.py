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

from comparator.analysis import language_excluded_features  # sieg 17/09: accurate comparability note
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
    scope=None,
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
            # sieg 17/09, FIXED. This used to claim "only the banded versions
            # travel" - false: comparable_features() never substituted the band,
            # it kept comparing the raw within_language value across languages
            # (audit finding, HIGH). Now that comparable_features() actually
            # excludes them (analysis.language_excluded_features()), this note
            # describes what really happens instead of what was supposed to.
            #
            # sieg 17/09, second pass: dropped the "see charts.md" pointer - it
            # only exists on the run_analysis.py path. This module is also
            # consumed by export_web_report.py (business web UI), which never
            # writes charts.md, so pointing every reader at it was the same
            # "claims what the pipeline doesn't actually do" mistake this note
            # had just been fixed for, one level up.
            excluded = language_excluded_features(fd, usable)
            material.append(
                f"Pages are in **{len(languages)} languages** ({languages}). "
                f"{len(excluded)} within_language feature(s) ({excluded}) are excluded from every "
                "cross-bank comparison while that is true (comparability in the dictionary). "
                "Band versions exist but are not compared in by default."
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
        "(PRD 5.2). Google Trends search interest is available for ING, KBC and CBC as *context* "
        "and does not change this: it measures what people searched for, not what a campaign "
        "achieved, it covers three of the nine banks, and the pages captured are today's pages "
        "rather than the pages live during any older spike.",
        "Only the open web is covered. Social media, in-app and email banners are out of scope and "
        "may well be where a bank's real communication happens.",
        "`total_image_area_ratio` sums image bounding boxes, so overlapping images are counted twice "
        "and the value is capped at 1.0. `above_fold_element_count` depends on what counts as an "
        "element. Both are exact about geometry and approximate about meaning.",
        # steph 17/09: this used to say flatly "not reproducible", on the strength of
        # five runs that disagreed. Measured since: our half is deterministic, and
        # four of those five runs had re-collected in between, so the data - and
        # therefore the derived targets and the prompt - legitimately changed.
        # The narrower statement is the true one, and the business UI renders this
        # text verbatim, so an over-claim here reaches a stakeholder.
        "The generated campaigns are **mostly, not perfectly, reproducible**. Our side is "
        "deterministic: the same dataset produces a byte-identical prompt, and each generated "
        "artefact records that prompt's fingerprint. The model is the variable part — identical "
        "requests usually return identical copy but not always, because temperature controls "
        "sampling and not how the model routes internally. Treat a committed campaign as one "
        "sample rather than as the output.",
        "Hitting a generation target shows the model followed instructions. It says nothing about "
        "whether the campaign would perform better (plan risk P-08).",
    ]

    # sieg 17/09 audit, point 1: --product-family drops every bank with no page
    # in the chosen family, and the OUTPUT FILES never said so - Belfius (other)
    # and BNP (mortgage) simply were not in bank_profiles.json. The console said
    # it; the artefacts a reader actually opens did not.
    if scope is not None and getattr(scope, "family", None):
        if scope.dropped_banks:
            material.append(
                f"**{len(scope.dropped_banks)} bank(s) are absent from this comparison entirely**: "
                f"{', '.join(scope.dropped_banks)}. They have real, usable captures but no page in "
                f"the '{scope.family}' product family, and comparing across families would confound "
                "every difference with the product (DR-04). They are in the dataset, not in these "
                "results - collect them a page in this family to include them."
            )

    uncollectable = []
    if "capture_quality" in df.columns and "bank" in df.columns:
        broken_banks = set(df[df["capture_quality"] == "unusable"]["bank"])
        uncollectable = sorted(broken_banks - set(usable_banks))

    return {
        "uncollectable_banks": uncollectable,
        "families_pooled": int(usable["product_family"].nunique()) if "product_family" in usable else 0,
        "unscored_rubric_features": missing_rubric,
        "family": getattr(scope, "family", None) if scope is not None else None,
        "dropped_banks": list(getattr(scope, "dropped_banks", [])) if scope is not None else [],
        "n_banks": n_banks,
        "n_usable_banks": len(usable_banks),
        "n_pages": len(df),
        "n_usable_pages": len(usable),
        "blocking": blocking,
        "material": material,
        "standing": standing,
    }


# sieg 17/09 audit, point 2: this was a frozen list. It still told the team to
# "collect a usable ING page" and described "two of six captures defeated by a
# consent wall" long after ING was fixed and the dataset had grown - stale advice
# sitting inside a file whose whole premise is that it describes the data in
# hand. Built from the assessment now, like everything else here.
STANDING_NEXT_STEPS = [
    ("Run the Day 5 scoring session", "Two independent human raters, then report agreement "
     "alongside the model's own sheet. Until then the judgement-based dimensions carry one "
     "model's opinion and nothing to check it against."),
    ("Make generation attributable", "Store the generated artefact and its prompt hash and "
     "evaluate that, rather than regenerating on every run."),
    ("Extend beyond the open web", "Social media and in-app banners, using the same feature "
     "framework — the extension the brief names, and the reason the framework is worth keeping."),
]


def next_steps(assessment: dict) -> list[tuple[str, str]]:
    """The steps this dataset actually calls for, in priority order."""
    steps: list[tuple[str, str]] = []

    for bank in assessment.get("uncollectable_banks", []):
        steps.append((
            f"Recover a usable capture for {bank}",
            "It has no usable page, so it is absent from every comparison. See its "
            "capture_quality_note for what failed.",
        ))

    dropped = assessment.get("dropped_banks") or []
    if dropped:
        steps.append((
            f"Collect {', '.join(dropped)} a page in the compared product family",
            f"They have usable captures but none in '{assessment.get('family')}', so they sit out "
            "of the comparison entirely rather than for any analytical reason.",
        ))

    if assessment.get("families_pooled", 0) > 1 and not assessment.get("family"):
        steps.append((
            "Restrict the comparison to one product family",
            "Pooling families confounds every cross-bank difference with the product (DR-04). "
            "Pass --product-family.",
        ))

    if assessment.get("unscored_rubric_features"):
        steps.append((
            f"Score the {len(assessment['unscored_rubric_features'])} unscored rubric feature(s)",
            "Vision-only features cannot be model-scored; they need a human with the screenshot.",
        ))

    return steps + STANDING_NEXT_STEPS


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
    # sieg 17/09 audit, point 3: this headline counts the WHOLE dataset, while
    # charts.md and bank_profiles.json count what survived the product-family
    # filter. Two honest views of one run, but nothing said so, and side by side
    # they read as contradictory.
    if assessment.get("family"):
        dropped = assessment.get("dropped_banks") or []
        lines += [
            f"> **These counts are pre-filter.** The comparison itself was restricted to the "
            f"`{assessment['family']}` product family, so `charts.md` and `bank_profiles.json` "
            f"report a smaller set"
            + (f" — {', '.join(dropped)} have usable captures but no page in that family."
               if dropped else "."),
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
    for i, (title, detail) in enumerate(next_steps(assessment), 1):
        lines.append(f"{i}. **{title}.** {detail}")
    lines.append("")
    return "\n".join(lines)
