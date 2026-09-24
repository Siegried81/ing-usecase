# Model-written score sheets — reference only, NEVER a rater

These are model output. They are kept so the "can a model do the judged
scoring?" question can be answered with a measurement instead of an opinion,
and they must never be merged into `campaigns_scored.csv`.

They live in this subfolder, not next to `siegried_scores.csv`, precisely so a
`data/rubric/*_scores.csv` glob cannot pick them up by accident. The judged
columns in the dataset come from one human sheet, by one named person.

| File | Written by | Judged features it filled | Exact agreement with the human sheet |
| --- | --- | --- | --- |
| `deepseek_flash.csv` | the project's pinned model, text only | **1 of 13** (`formality_score`) | 6% (n=51) |
| `claude.csv` | a vision-capable model | 13 of 13 | 41% (n=608) |
| `vision_proposed.csv` | a vision model, as proposals | 13 of 13 | 49% (n=591) |

Why deepseek filled only one: 12 of the 13 judged features are declared in
`config/feature_dictionary.yaml` with `source: screenshot`. A text-only model
cannot see them, so scoring them would be a confident answer to a question the
evidence cannot settle. Leaving them blank is the gate working, not a failure.

`vision_proposed.csv` is also the record of why the project runs on a single
judge: a sheet submitted as an independent human rating was found to be
identical to it on all 117 paired judgements.
