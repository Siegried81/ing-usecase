# Technical deep dive

What each module does and why the measurement rules are what they are. Overview:
[ARCHITECTURE.md](ARCHITECTURE.md); runbook: [pipeline.md](pipeline.md); decisions:
[decisions.md](decisions.md).

## 1. Shape of the system

Two pipelines joined only by files on disk.

```
scripts/collection_targets.yaml
  → compliance.assert_can_fetch      live robots.txt, fails closed
  → static_fetch | headless_render | headful_render
  → scraper.extract()                deterministic features
  → visual_features                  colour from the screenshot
  → llm_extractor                    one structured call per page
  → quality.assess_capture()         is this a campaign page at all?
  → data/processed/campaigns.csv  → rubric_sheet emit / merge → campaigns_scored.csv
  → run_analysis.py | export_web_report.py | run_generation.py
  → outputs/, web/public/*.json, recommendations.py, site_generator.py
```

`search_interest/` is a separate Google Trends pipeline (own config, SQLite
database, Streamlit app). It imports nothing from `src/comparator`; the main
pipeline reads two CSVs from `search_interest/export/` through `trends.py`. The
coupling is file-shaped so neither side can break the other at import time.

## 2. The contract

`config/feature_dictionary.yaml` is the single source of truth for the schema, the
validator, the generated docs, the rubric sheet and the rater guide. Each feature
declares `type`, `extraction` (`automatic`, `model_assisted`, `rubric`, `derived`),
`comparability`, `tier` (`core` required, `extended` never blocking) and its allowed
`values` or `range`.

Enforcement:

- **Load time** (`dictionary.py`): unknown keys, unknown dimension or tier, a
  categorical without values, a required feature outside `core`, or anything other
  than exactly one non-nullable primary key raises.
- **Validation time** (`schema.py`): a column absent from the dictionary is an
  error; so are out-of-range values, nulls in non-nullable columns and any row with
  `robots_allowed = false`.
- **Comparison time** (`analysis.comparable_features`): computed from feature type,
  dimension and comparability, never from a hand-written column list.
- **Freeze** (`freeze.py` and `tests/test_schema.py`): a change is breaking if a
  feature is removed or renamed, a type changes, an allowed value disappears, a
  range is added or narrowed, a tier is demoted, or a nullable column becomes
  non-nullable. Additions and wider enums pass.

**Data quality.** `dq.py` scores the dataset by dimension, reusing the dictionary's
rules so "valid" has one definition. Completeness, validity and uniqueness gate;
consistency (which carries the recorded model fallback) and timeliness warn;
accuracy is reported as not measurable, because there is no golden source.
`scripts/check_data_quality.py` runs it in CI; the report is
`outputs/dq_report.md`.

**Comparability.** `within_language` features are excluded from cross-bank
comparison whenever the dataset holds more than one language
(`analysis.language_excluded_features`), and the exclusion is printed in the
feature accounting and in the generated limitations. `bands.py` converts such
numbers to ordinal bands with fixed cutoffs; that reduces the cross-language
problem without removing it. `within_capture_window` is declared on two rate
features but not enforced anywhere.

## 3. Modules

**Core.** `dictionary.py` parses the YAML into frozen `Feature` objects.
`schema.py` types, validates and writes the CSV (list columns pipe-separated).
`bands.py` holds the threshold functions shared by the fixture and the scraper.
`banks.py` owns bank to traditional/challenger and display names. `derive.py`
recomputes the `derived` features and never invents a missing input.

**Collection.**

- `compliance.py`: the robots gate (fetched with `requests`, cached per domain,
  fails closed). Called before the HTML fetch, before Playwright is imported,
  before the hero-image fetch and when importing a manual capture. Cross-origin
  sub-resources of a render are not robots-checked (blocking fonts and CDNs would
  corrupt the measured geometry); `site_generator.py` fetches ING's own SVGs outside
  the gate.
- `scraper.py`: word counts, readability per language, CTA counting (distinct
  calls to action, chrome excluded), rate detection (needs a rate keyword near the
  number), urgency markers (terms and dated deadlines), footnotes, shadow-DOM
  flattening.
- `render.py`: Playwright at a fixed 1440x900 viewport for the geometry features a
  static fetch cannot produce.
- `visual_features.py`: `background_luminance` on the first screen,
  `brand_colour_share` over the full-page screenshot.
- `llm_extractor.py`: all model-assisted fields in one structured call, pydantic
  validated, cross-checked against the dictionary's allowed values. DeepSeek is
  pinned; Groq (three rotating keys), OpenRouter, Cerebras, SambaNova and local
  Ollama are fallbacks recorded in `extraction_model`. The model sees only the first
  `PAGE_TEXT_LIMIT` characters of a page, so footer cross-sell often sits below the
  cut; raising it means re-extracting every page.
- `quality.py`: separates a campaign page from a JS shell, a maintenance notice or
  a consent wall; the verdict goes in `capture_quality`.

**Analysis** (`analysis.py`).

- `comparison_matrix()` is the one place the standardised matrix is built, shared by
  `positioning_axis()` and `similarity_matrix()`; one-hot blocks are scaled by
  `1/sqrt(k)` after standardisation.
- `ing_vs_peers()` flags a gap `reportable` only with at least 3 peers, non-zero
  spread, peers not near zero and `|gap| <= 8 SD`. Unreportable gaps are ranked last,
  never dropped.
- `check_deck_claims()` has three verdicts: supported, not supported, not testable.
  A tie is never "supported".
- `CAPTURE_INVALID_FEATURES` lists withdrawn features with the reason, honoured by
  `comparable_features()`.
- No p-value is computed. Cohen's d describes separation; `recurring_patterns()`
  reports correlation with an explicit no-causation note.

**Scoring.**

| Module | Measures | Caveat |
| --- | --- | --- |
| `ai_score.py` | Six 0-10 axes per bank, arithmetic only | Six independent means, not a validated scale |
| `cross_sell.py` | Distinct add-on product types per page | Breadth, not effort |
| `rubric.py` | Nothing: emits the sheet, merges it back | First non-empty value wins, nothing is averaged |
| `benchmarks.py` | What three attention-selected brands do differently | Selected on search attention alone, not a causal claim |
| `reputation.py` | Belgian headlines per theme, 90-day window | Themes, never sentiment |
| `market_context.py`, `research.py` | Share prices, paper search | Standalone, not wired into the report |

**Generation and reporting.**

- `generation.py` derives a numeric target from the data, briefs a model, renders
  HTML and measures it with the same extractor used on real pages. Rate and
  numeric-claim targets are blocked (`GUARDRAIL_BLOCKED_FEATURES`).
- `site_generator.py` builds the demo site: the skeleton (page keys, nav,
  stylesheet) is fixed in code and only the content is generated, one call per page,
  with retries for wrong language, missing explanations and unexpressed
  recommendations.
- `recommendations.py` turns `report.json` into ranked changes tied to a measured
  feature; invented feature ids are dropped and reputation-based advice may not cite
  page features.
- `report.py` and `charts.py` write the chart companion and PNGs; a chart drawn
  without the focus bank retitles itself and stamps a warning.
- `limitations.py` writes the limitations from the dataset on every run.

**Surfaces.** `streamlit_app.py` is the key-free operator dashboard with cached
loaders and visible warnings for missing files. `web/` is React 18 + Vite fed by
`report.json`, `operations.json` and `trends.json`, plus live calls to
`scripts/serve_web.py` (FastAPI) for recommendations, site generation and research.
`serve_web.py` re-derives no number. `scripts/one_off/` holds single-use
re-collection YAMLs.

## 4. Testing and CI

- No network: an autouse fixture in `tests/conftest.py` makes `socket.connect` raise
  for non-loopback addresses. Mocking is stdlib only (`unittest.mock`, `monkeypatch`).
- Some tests skip when an optional dependency is absent (`pytrends`, `streamlit`, a
  built `web/dist`); CI installs the optional requirement files so they run.
- Assertions worth keeping: the robots gate fires before Playwright starts; an
  unreadable `robots.txt` fails closed; the working dictionary matches the frozen
  snapshot; the download endpoint rejects path traversal; the rubric deliverable
  never claims a reliability measure; `banks.py` pins the group split.
- A withdrawn claim gets a regression test so a corrected mistake cannot return.
- CI (`tests.yml`): ruff (rules in `ruff.toml`), pytest, schema freeze, data-quality
  gate, and a job that type-checks and builds the React UI.

## 5. Design lessons

1. The dominant bug class is a measurement that runs cleanly and measures the wrong
   thing; check numbers against the stored page, not just ranges.
2. An empty result and a failed request must not share a return value.
3. Fix the generator, not the artefact: a hand-edited output is undone by the next run.
4. Derive constraints from the source of truth instead of restating them.
5. "We cannot measure this defensibly" is a valid outcome: withdraw the feature,
   record the reason, make the exclusion visible.

## 6. Reproducibility

Analysis onward is reproducible from the tracked data with pinned packages and no
API key (without fresh reputation or geo-trends output). Reproducing from an empty
`data/` needs an LLM key, a Playwright Chromium install and a human rater for the
judged sheet. `data/raw/` captures are not versioned, so the deterministic
re-derive scripts also need a re-capture. Dependencies are pinned in
`requirements*.txt`; `pytrends` and `streamlit` live in their own files. Generated
campaigns are mostly, not perfectly, reproducible: the code is deterministic, the
model is not, and each artefact records a SHA-256 fingerprint of its prompt.

## 7. Known gaps

- `report.json`'s `generated` block is read from disk and can predate a withdrawal;
  re-run `scripts/run_generation.py` then the export.
- `within_capture_window` is not enforced.
- `generation_guardrails` does not run on the site path; "no invented rate" rests on
  the prompt and a fixed footer.
- Single-judge bias is unmeasured.
