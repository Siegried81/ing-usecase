# Limitations & next steps

*Deliverable D-09. Generated from the dataset by `scripts/run_analysis.py`, so it describes the data that actually exists rather than the data we meant to collect.*

**4 usable page(s) across 4 bank(s)**, from 4 collected.

## What this analysis cannot support

### Blocking — a question cannot be answered at all

- **ING is not in the usable data.** BO-01 (position ING) and BO-02 (traditional or challenger) cannot be answered at all until a usable ing page is collected. Every other finding is about the market without us in it.
- **13 of 13 rubric features are unscored** (['formality_score', 'clarity_score', 'rate_prominence', 'value_prop_clarity'] ...). Every judgement-based dimension — tone, layout archetype, AIDA coverage, persuasion levers — is therefore absent from the comparison. Run the Day 5 scoring session (`scripts/rubric_sheet.py emit`).

### Material — findings survive, but weakened

- Only **2 traditional bank(s)** in the usable data. A group mean over 2 bank(s) is an anecdote; effect sizes between the groups are descriptive shorthand, not evidence of a market pattern.
- Only **2 challenger bank(s)** in the usable data. A group mean over 2 bank(s) is an anecdote; effect sizes between the groups are descriptive shorthand, not evidence of a market pattern.
- The usable pages span **2 different product families** (['current_account_pack', 'other']). DR-04 requires comparisons within one family — a mortgage page and a current-account page differ because the products differ, not because the banks communicate differently. Any cross-bank claim from this dataset is confounded by product.

### Standing — true regardless of how much we collect

- Model-assisted features were all produced by `deepseek/deepseek-chat`, at temperature 0. They carry that model's judgement, validated against human labels only on a sample.
- Every conclusion is valid for the capture window **2026-09-16 to 2026-09-16** and no later. Campaign pages change without notice (DR-05).
- **No performance data exists in this project.** Nothing links a design choice to a click, a conversion or a sale. Every recommendation is a hypothesis ING could test, never a cause (PRD 5.2).
- Only the open web is covered. Social media, in-app and email banners are out of scope and may well be where a bank's real communication happens.
- `total_image_area_ratio` sums image bounding boxes, so overlapping images are counted twice and the value is capped at 1.0. `above_fold_element_count` depends on what counts as an element. Both are exact about geometry and approximate about meaning.
- The generated campaigns are **not reproducible**: the same brief at temperature 0 produced different copy and a different hit rate on five separate runs. A committed generated artefact is one sample, not the output.
- Hitting a generation target shows the model followed instructions. It says nothing about whether the campaign would perform better (plan risk P-08).

## Next steps

1. **Collect a usable ING page.** Nothing about ING's position can be said without it. The current capture is a JavaScript shell; a longer settle time or a different entry URL is the first thing to try.
2. **Fix the product-family mix.** Collect the same product family across every bank. The current targets file is a pipeline test, not a comparable scope (DR-04).
3. **Run the Day 5 scoring session.** 13 rubric features, two independent raters, then report agreement. Until then the comparison is automatic features only.
4. **Handle consent walls in collection.** Two of six captures were defeated by a page that never rendered its content. Detect and dismiss the consent layer, or record the bank as uncollectable.
5. **Make generation reproducible.** Store the generated artefact and evaluate that, rather than regenerating on every run.
6. **Extend beyond the open web.** Social media and in-app banners, using the same feature framework — the extension the brief names, and the reason the framework is worth keeping.
