"""D-09 - Limitations & next steps, read off the dataset rather than remembered.

The RACI puts D-09 on me, and it is the deliverable
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

from comparator.analysis import language_excluded_features  # Accurate comparability note
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
            # The wording must state what comparable_features() really does -
            # it EXCLUDES within_language features across languages
            # (analysis.language_excluded_features()), it does not substitute
            # their banded versions. A limitations note that describes an
            # intention rather than the code is worse than none.
            #
            # For the same reason there is no "see charts.md" pointer here:
            # charts.md only exists on the run_analysis.py path, and this
            # module is also consumed by export_web_report.py (business web UI),
            # which never writes it.
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
            "levers — is therefore absent from the comparison. Score the sheet and merge it "
            "(`scripts/rubric_sheet.py merge`)."
        )
    # A feature present but incomplete is silently dropped from the
    # comparison - bank_vectors() does dropna(axis=1, how="any"), so one bank
    # missing one value removes that column for every bank. With a single rater
    # this is the likeliest way the comparison quietly narrows, so it is named.
    partly_scored = []
    for feature in rubric_features(fd):
        if feature.name not in usable.columns:
            continue
        filled = usable[feature.name].notna()
        if filled.any() and not filled.all():
            banks_missing = sorted(usable.loc[~filled, "bank"].dropna().unique())
            if banks_missing:
                partly_scored.append((feature.name, banks_missing))
    if partly_scored:
        named = ", ".join(f"`{n}` ({len(b)} bank(s))" for n, b in partly_scored[:4])
        material.append(
            f"**{len(partly_scored)} judged feature(s) are scored on some banks but not all** "
            f"({named}{' ...' if len(partly_scored) > 4 else ''}). A feature missing on even one "
            "bank is dropped from the cross-bank comparison entirely, so these carry no weight "
            "in the positioning, the peer gaps or the similarity — they are absent from the "
            "result rather than partially present in it."
        )

    # Always said, never conditional: it is true of every run of this pipeline,
    # and it is the sentence a reader needs before they weigh a judged number.
    # The taxonomy once held six banking families plus "other", which collapsed
    # insurance, credit cards and partner perks into a single token and inverted
    # the measure on the pages that cross-sell hardest. Those three values were
    # since added, so what remains is the shape of the measure rather than a gap
    # in it: the score counts how many distinct types a page names, so it cannot
    # tell a page that mentions one product once from one that pushes it hard.
    standing.append(
        "**The cross-sell score counts distinct product types, not selling effort.** "
        "`cross_sold_products` names nine product types plus `other`, and a page's "
        "score is how many of the nine it mentions, averaged over the bank's pages. "
        "A page that pushes one product ten times and a page that mentions it once "
        "score identically, and anything outside the nine still collapses into a "
        "single `other` counted once. Read the score as breadth of coverage, never "
        "as how hard a page cross-sells."
    )

    # Five features are withdrawn in analysis.CAPTURE_INVALID_FEATURES. They are
    # named here because a reader of this file alone would otherwise see a
    # complete-looking dataset and assume every column in it was compared.
    standing.append(
        "**Five features are measured but never compared.** `cta_count` and "
        "`cta_contrast_ratio` are withdrawn because no counting rule reproduced a "
        "human count of calls to action across fourteen banks: navigation, several "
        "links pointing at one target, and clickable product cards are marked up "
        "differently by every bank, so the number reports the markup convention. "
        "`has_animation` and `animated_asset_count` are withdrawn because the rule "
        "asks whether the stylesheet declares an animation, not whether the page "
        "moves — across the compared pages exactly one carries real motion. The "
        "`has_comparison_table` is withdrawn because it tests for an HTML `<table>` "
        "element: traditional banks mark their tariff grids up as tables, while N26 "
        "and Revolut build the same plan comparison in CSS, so the 0.57-against-0.00 "
        "split it produced is a difference in authoring style, not in strategy. The "
        "columns stay in the dataset; they are excluded from every comparison and "
        "no finding rests on them."
    )

    # No dataset field records this: capture_quality is "ok" for all three, and
    # every affected value is in range, so schema.validate cannot catch it. It is
    # written down here rather than left as something the next reader discovers.
    standing.append(
        "**Three captures were taken with a cookie-consent modal over the page.** "
        "Argenta, BNP Paribas Fortis and Crelan. Their screenshot-derived features "
        "— `background_luminance`, `hero_image_area_ratio`, `accent_colour_count`, "
        "`brand_colour_share` and `above_fold_element_count` — describe the modal "
        "rather than the page beneath it, which is why those three report a "
        "near-zero hero area. Text-derived and judged features are unaffected, so "
        "the word, urgency, persuasion and rubric findings stand."
    )

    # background_luminance, and every colour feature with it, is read off ONE
    # rendering of the page: headless Chrome, default light colour scheme, at a
    # fixed viewport. A visitor whose browser or operating system forces dark
    # mode can see a materially different page, and nothing here measures that.
    # Worth saying plainly because "page brightness" sounds like a property of
    # the bank and is partly a property of how we looked at it.
    standing.append(
        "**Page colour is measured on one rendering.** `background_luminance`, "
        "`brand_colour_share` and the palette features come from a single capture in "
        "headless Chrome with the default light colour scheme. A visitor using dark "
        "mode, or a browser extension that forces it, may see a substantially darker "
        "page than the one measured here — that difference is unmeasured, and any "
        "brightness comparison should be read as a comparison of our captures."
    )

    standing.append(
        "The judged features carry the opinion of a single person. No inter-rater "
        "reliability was measured — that is the chosen scope of this proof of concept, "
        "not an oversight. Single-judge bias is a question for the real product and is "
        "listed under next steps."
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
        "(PRD 5.2). Google Trends search interest is available as *context* and does not change "
        "this: it measures what people searched for, not what a campaign achieved, it says which "
        "brand was looked up and never why, and the pages captured here are today's pages "
        "rather than the pages live during any earlier movement in search interest.",
        "Only the open web is covered. Social media, in-app and email banners are out of scope and "
        "may well be where a bank's real communication happens.",
        "`total_image_area_ratio` sums image bounding boxes, so overlapping images are counted twice "
        "and the value is capped at 1.0. `above_fold_element_count` depends on what counts as an "
        "element. Both are exact about geometry and approximate about meaning.",
        # "Mostly, not perfectly" is the measured statement, not a hedge: our
        # half is deterministic, and runs that appear to disagree had
        # re-collected in between, so the data - and therefore the derived
        # targets and the prompt - legitimately changed. The business UI renders
        # this text verbatim, so an over-claim here reaches a stakeholder.
        "The generated campaigns are **mostly, not perfectly, reproducible**. Our side is "
        "deterministic: the same dataset produces a byte-identical prompt, and each generated "
        "artefact records that prompt's fingerprint. The model is the variable part — identical "
        "requests usually return identical copy but not always, because temperature controls "
        "sampling and not how the model routes internally. Treat a committed campaign as one "
        "sample rather than as the output.",
        "Hitting a generation target shows the model followed instructions. It says nothing about "
        "whether the campaign would perform better (plan risk P-08).",
    ]

    # Audit, point 1: --product-family drops every bank with no page
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
        "partly_scored_rubric_features": [n for n, _ in partly_scored],
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


# Audit, point 2: this was a frozen list. It still told the team to
# "collect a usable ING page" and described "two of six captures defeated by a
# consent wall" long after ING was fixed and the dataset had grown - stale advice
# sitting inside a file whose whole premise is that it describes the data in
# hand. Built from the assessment now, like everything else here.
STANDING_NEXT_STEPS = [
    ("Measure single-judge bias", "Every judged feature in this run carries one person's "
     "reading. A second independent rater on a sample, with agreement reported, is what would "
     "turn these dimensions from a defensible opinion into a measured one. Out of scope here, "
     "and the first thing to add for a production build."),
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
            f"Collect a page in the compared product family for {', '.join(dropped)}",
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
            "These are judged from the rendered page, so they need a person with the "
            "screenshot open; nothing can infer them from the text.",
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
    # Audit, point 3: this headline counts the WHOLE dataset, while
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
