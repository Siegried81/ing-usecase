# Data-quality scorecard

*Generated from the dataset by `scripts/run_analysis.py`. The dataset is scored on the standard data-quality dimensions (the ones a BCBS 239 / DAMA programme reports on), reusing the feature dictionary's own rules so a value is valid here exactly when it is valid in `schema.validate()`.*

**Overall: PASS** - 51 rows, 104 columns checked. Completeness, validity and uniqueness are gating; consistency and timeliness are reported but warn only; accuracy is not measurable here.

> Dataset: `data/processed/campaigns_scored.csv`

| Dimension | Score | Status | What it asks | Detail |
| --- | --- | --- | --- | --- |
| Completeness | 99.8% | pass | are the required fields populated | 60 required field(s) 99.8% filled; most blank: section_count (-6), text_image_layout (-1) |
| Validity | 100.0% | pass | do values sit inside the declared types, ranges and allowed sets | 3243 checked value(s), 100.0% within the contract |
| Uniqueness | 100.0% | pass | is the primary key free of duplicates | page_id: 51/51 rows unique |
| Consistency | 96.1% | warn | were comparable features produced the same way across the dataset | 49/51 rows on deepseek/deepseek-flash; other model(s): groq/openai/gpt-oss-120b (2) - recorded fallback (NFR-02) |
| Timeliness | 100.0% | pass | is every row dated, so the capture window is known | 51/51 rows timestamped - captured 2026-09-21 to 2026-09-23; valid for that window only |
| Accuracy | n/a | not_measured | do values agree with a trusted reference | no golden source; model_assisted values validated against human labels on a sample only. Measured against a reference feed in production. |
