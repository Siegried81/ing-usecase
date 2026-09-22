# Limitations & next steps

*Deliverable D-09. Generated from the dataset by `scripts/run_analysis.py`, so it describes the data that actually exists rather than the data we meant to collect.*

**50 usable page(s) across 14 bank(s)**, from 50 collected.

> **These counts are pre-filter.** The comparison itself was restricted to the `current_account_pack` product family, so `charts.md` and `bank_profiles.json` report a smaller set.

## What this analysis cannot support

### Material — findings survive, but weakened

- The usable pages span **7 different product families** (['current_account_pack', 'investment', 'mortgage', 'other', 'pension', 'savings_account', 'term_account']). DR-04 requires comparisons within one family — a mortgage page and a current-account page differ because the products differ, not because the banks communicate differently. Any cross-bank claim from this dataset is confounded by product.
- Pages are in **2 languages** (['fr', 'nl']). 8 within_language feature(s) (['avg_sentence_length', 'disclaimer_word_share', 'first_person_plural_count', 'readability_score', 'second_person_ratio', 'sentence_count', 'text_to_image_ratio', 'word_count']) are excluded from every cross-bank comparison while that is true (comparability in the dictionary). Band versions exist but are not compared in by default.
- **10 judged feature(s) are scored on some banks but not all** (`clarity_score` (12 bank(s)), `rate_prominence` (12 bank(s)), `value_prop_clarity` (12 bank(s)), `text_image_layout` (12 bank(s)) ...). A feature missing on even one bank is dropped from the cross-bank comparison entirely, so these carry no weight in the positioning, the peer gaps or the similarity — they are absent from the result rather than partially present in it.

### Standing — true regardless of how much we collect

- The judged features carry the opinion of a single person. No inter-rater reliability was measured — that is the chosen scope of this proof of concept, not an oversight. Single-judge bias is a question for the real product and is listed under next steps.
- Model-assisted features were all produced by `deepseek/deepseek-flash`, at temperature 0. They carry that model's judgement, validated against human labels only on a sample.
- Every conclusion is valid for the capture window **2026-09-21 to 2026-09-21** and no later. Campaign pages change without notice (DR-05).
- **No performance data exists in this project.** Nothing links a design choice to a click, a conversion or a sale. Every recommendation is a hypothesis ING could test, never a cause (PRD 5.2). Google Trends search interest is available as *context* and does not change this: it measures what people searched for, not what a campaign achieved, it says which brand was looked up and never why, and the pages captured here are today's pages rather than the pages live during any earlier movement in search interest.
- Only the open web is covered. Social media, in-app and email banners are out of scope and may well be where a bank's real communication happens.
- `total_image_area_ratio` sums image bounding boxes, so overlapping images are counted twice and the value is capped at 1.0. `above_fold_element_count` depends on what counts as an element. Both are exact about geometry and approximate about meaning.
- The generated campaigns are **mostly, not perfectly, reproducible**. Our side is deterministic: the same dataset produces a byte-identical prompt, and each generated artefact records that prompt's fingerprint. The model is the variable part — identical requests usually return identical copy but not always, because temperature controls sampling and not how the model routes internally. Treat a committed campaign as one sample rather than as the output.
- Hitting a generation target shows the model followed instructions. It says nothing about whether the campaign would perform better (plan risk P-08).

## Next steps

1. **Measure single-judge bias.** Every judged feature in this run carries one person's reading. A second independent rater on a sample, with agreement reported, is what would turn these dimensions from a defensible opinion into a measured one. Out of scope here, and the first thing to add for a production build.
2. **Make generation attributable.** Store the generated artefact and its prompt hash and evaluate that, rather than regenerating on every run.
3. **Extend beyond the open web.** Social media and in-app banners, using the same feature framework — the extension the brief names, and the reason the framework is worth keeping.
