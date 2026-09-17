# Limitations & next steps

*Deliverable D-09. Generated from the dataset by `scripts/run_analysis.py`, so it describes the data that actually exists rather than the data we meant to collect.*

**12 usable page(s) across 9 bank(s)**, from 12 collected.

> **These counts are pre-filter.** The comparison itself was restricted to the `current_account_pack` product family, so `charts.md` and `bank_profiles.json` report a smaller set — belfius, bnp_paribas_fortis have usable captures but no page in that family.

## What this analysis cannot support

### Blocking — a question cannot be answered at all

- **3 of 13 rubric features are unscored** (['text_image_layout', 'layout_archetype', 'mobile_first_design_signal']). Every judgement-based dimension — tone, layout archetype, AIDA coverage, persuasion levers — is therefore absent from the comparison. Run the Day 5 scoring session (`scripts/rubric_sheet.py emit`).

### Material — findings survive, but weakened

- The usable pages span **4 different product families** (['current_account_pack', 'mortgage', 'other', 'savings_account']). DR-04 requires comparisons within one family — a mortgage page and a current-account page differ because the products differ, not because the banks communicate differently. Any cross-bank claim from this dataset is confounded by product.
- Pages are in **2 languages** (['fr', 'nl']). Word counts and readability are not comparable across languages; only the banded versions travel.
- **2 bank(s) are absent from this comparison entirely**: belfius, bnp_paribas_fortis. They have real, usable captures but no page in the 'current_account_pack' product family, and comparing across families would confound every difference with the product (DR-04). They are in the dataset, not in these results - collect them a page in this family to include them.

### Standing — true regardless of how much we collect

- Model-assisted features were all produced by `deepseek/deepseek-chat`, at temperature 0. They carry that model's judgement, validated against human labels only on a sample.
- Every conclusion is valid for the capture window **2026-09-16 to 2026-09-16** and no later. Campaign pages change without notice (DR-05).
- **No performance data exists in this project.** Nothing links a design choice to a click, a conversion or a sale. Every recommendation is a hypothesis ING could test, never a cause (PRD 5.2). Google Trends search interest is available for ING, KBC and CBC as *context* and does not change this: it measures what people searched for, not what a campaign achieved, it covers three of the nine banks, and the pages captured are today's pages rather than the pages live during any older spike.
- Only the open web is covered. Social media, in-app and email banners are out of scope and may well be where a bank's real communication happens.
- `total_image_area_ratio` sums image bounding boxes, so overlapping images are counted twice and the value is capped at 1.0. `above_fold_element_count` depends on what counts as an element. Both are exact about geometry and approximate about meaning.
- The generated campaigns are **not reproducible**: the same brief at temperature 0 produced different copy and a different hit rate on five separate runs. A committed generated artefact is one sample, not the output.
- Hitting a generation target shows the model followed instructions. It says nothing about whether the campaign would perform better (plan risk P-08).

## Next steps

1. **Collect belfius, bnp_paribas_fortis a page in the compared product family.** They have usable captures but none in 'current_account_pack', so they sit out of the comparison entirely rather than for any analytical reason.
2. **Score the 3 unscored rubric feature(s).** Vision-only features cannot be model-scored; they need a human with the screenshot.
3. **Run the Day 5 scoring session.** Two independent human raters, then report agreement alongside the model's own sheet. Until then the judgement-based dimensions carry one model's opinion and nothing to check it against.
4. **Make generation attributable.** Store the generated artefact and its prompt hash and evaluate that, rather than regenerating on every run.
5. **Extend beyond the open web.** Social media and in-app banners, using the same feature framework — the extension the brief names, and the reason the framework is worth keeping.
