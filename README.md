# Banking Campaigns Comparator

How Belgian banks communicate comparable products differently, and what ING could
learn from it. A two-week proof of concept for ING DACI / Customer AI, built
14–25 September 2026 by Siegried (lead, marketing framework), Dan (collection,
extraction) and Stephane (analysis, GenAI).

**The one thing this project refuses to claim:** no performance data exists here.
Nothing links a design choice to a click, a conversion or a sale. Every finding is
of the form *"ING does X differently"*, never *"X works better"*. That ceiling is
structural, not caution — there is no outcome variable in the dataset at all.

A full technical walkthrough — what every module does, the measurement decisions,
and the twenty bugs that shaped them — is in
[`technical_deep_dive.md`](technical_deep_dive.md).

## What it does

Collects real public campaign pages from Belgian banks, measures each one against
a single declared feature dictionary, compares banks within one product family,
and turns the gaps into recommendations and a generated demo site.

```
targets.yaml → robots gate → capture (static / headless / headful)
             → deterministic extraction + one LLM call per page
             → human rubric sheet → validated dataset
             → analysis → report.json → recommendations → generated site
```

## Scope, as measured

| | |
| --- | --- |
| Dataset | **51 pages · 14 banks · 6 product families** (`current_account_pack` 18, `investment` 9, `savings_account` 9, `pension` 8, `mortgage` 5, `term_account` 2) |
| Positioning view | one family at a time (DR-04) — currently the 18 current-account pages, 33 comparable features |
| Languages | French 48, English 2, Dutch 1 — so the 8 numeric `within_language` features are **excluded** from cross-bank comparison rather than compared across languages |
| Feature dictionary | **104 features** (66 core, 38 extended); working and frozen copies byte-identical |
| Human judgement | **one judged sheet**, one named rater, 13 rubric features |
| Capture methods | 45 headless, 6 headful, **zero** manual-only |
| Labelling model | `deepseek/deepseek-flash` on 49 rows, `groq/openai/gpt-oss-120b` on 2 (fallback, recorded not silent) |
| Tests | 449 passing, no network — proven by re-running with sockets disabled |
| CI | `.github/workflows/tests.yml` — ruff (pyflakes), pytest, schema-freeze check, plus a React type-check and build |

## Quick start

The fixture path needs no API key and no network:

```bash
pip install -r requirements.txt
cp .env.example .env
python3 scripts/make_fixture.py       # synthetic dataset — every row invented
python3 scripts/run_analysis.py
python3 -m pytest tests/ -q
```

Fixture archetypes encode the kickoff deck's *claims*, so a fixture run always
confirms them. Never read a fixture result as evidence.

Because `data/`, `outputs/` and the judged sheet are committed (team decision,
21/09), a fresh clone can regenerate `outputs/` from step 4 onward without
re-collecting. Re-running collection needs an LLM key, a Playwright Chromium
install and network access; re-scoring the rubric needs a human.

Real-data command order, the mandatory re-merge rule and the failure modes a range
check cannot catch are in [`docs/pipeline.md`](docs/pipeline.md).

## The design, in five points

- **One measuring stick.** Every number comes from
  `config/feature_dictionary.yaml`. The schema, the validator and the generated
  docs are derived from it, so they cannot drift apart. Each feature declares how
  it was produced (`automatic`, `rubric`, `model_assisted`, `derived`) and how far
  it can be compared (`cross_language`, `within_language`, `within_capture_window`).
- **One pinned model.** A difference between two banks must be a difference
  between two banks, not between two judges. A provider fallback is allowed but
  always **recorded** on the row, and the validator warns when a dataset mixes
  models.
- **Judgement is labelled.** Human-scored and machine-measured values look
  different on screen. One judged sheet means no reliability figure is claimed —
  stated outright rather than left to be inferred.
- **Compliance is a gate, not a setting.** `assert_can_fetch()` checks live
  `robots.txt` before every fetch, including hero images and same-origin
  sub-resources, and fails closed. There is no flag to skip it, and a row with
  `robots_allowed = false` is a hard validation error.
- **Withdrawal is a first-class outcome.** Five features are measured but never
  compared, because each turned out to describe the capture rather than the bank.
  The exclusion lives in the analysis and is printed in the feature accounting, so
  a re-run cannot quietly undo it.

Full reasoning in [`docs/design.md`](docs/design.md).

## Documentation map

| File | What it is |
| --- | --- |
| [`technical_deep_dive.md`](technical_deep_dive.md) | **this system, explained** — every module, the measurement decisions, the bugs and their fixes |
| [`docs/pipeline.md`](docs/pipeline.md) | runbook — commands in order, where data lands, the quality gate |
| [`docs/design.md`](docs/design.md) | design — the dictionary contract, the freeze rule, what the validator refuses |
| [`docs/decisions.md`](docs/decisions.md) | dated decision log, append-only |
| [`docs/D01_scope_and_compliance_note.md`](docs/D01_scope_and_compliance_note.md) | banks in scope, per-domain robots.txt findings, what was excluded and why |
| [`docs/D06_business_narrative.md`](docs/D06_business_narrative.md) | the business insights, written for the ING audience |
| [`docs/feature_dictionary.md`](docs/feature_dictionary.md) | generated from the YAML — never edit by hand |
| [`data/rubric/SCORING_GUIDE.md`](data/rubric/SCORING_GUIDE.md) | how a rater fills the 13 judgement-based features |
| [`web/README.md`](web/README.md) | the React business UI |
| [`outputs/limitations.md`](outputs/limitations.md) | generated (D-09) — what this run cannot support, read off the dataset |

`outputs/charts.md`, `outputs/bank_profiles.md`, `outputs/limitations.md` and
`outputs/search_interest_context.md` are all generated every run. Do not hand-edit
them; a correction a re-run undoes is not a correction.

## Layout

```
config/feature_dictionary.yaml   the contract (+ .frozen.yaml, the Day 2 snapshot)
src/comparator/
  dictionary.py schema.py        load, type, validate the dataset
  bands.py banks.py derive.py    thresholds, canonical bank facts, derived features
  collection/                    compliance gate, scraper, headless render,
                                 colour, one-call LLM extractor, quality gate
  analysis.py                    comparable features, positioning, similarity, deck claims
  ai_score.py cross_sell.py      composite scores, all arithmetic, no LLM
  rubric.py                      emit the judged sheet, merge it back
  benchmarks.py trends.py        search interest as context, never as an outcome
  reputation.py                  news themes, never sentiment
  generation.py site_generator.py  step 5 and the 10-page demo site
  recommendations.py             LLM advice grounded in one report
  report.py charts.py            the generated chart companion and the four PNGs
  limitations.py freeze.py       D-09 from the data, and the schema freeze rule
search_interest/                 standalone Google Trends share-of-search pipeline
scripts/                         run_collection, run_analysis, export_web_report,
                                 serve_web, rubric_sheet, deterministic re-derive scripts
web/                             React business UI
streamlit_app.py                 earlier dashboard; superseded by the React operator tabs
tests/                           449 tests, all network mocked
```

## Known open items

Recorded rather than fixed, because the project window closed on 25 September:

1. **Single-judge bias is unmeasured.** The chosen scope of a POC, and the first
   thing a production build should add: a second independent rater on a sample,
   with agreement reported.
2. **`report.json` still publishes a `cta_count` scorecard "hit"** in its
   `generated` block, because `export_web_report.py` reads step-5 artefacts dated
   22/09 from disk instead of recomputing them. The same file's limitations say
   the feature is never compared. A re-run of `scripts/run_generation.py` would
   resolve it.
3. **`decisions.md` D6 still names `deepseek-chat`**, a model that appears on zero
   rows. The log is append-only and was never amended; `design.md` records the
   switch. Needs a dated entry from the D6 owner.
4. **`within_capture_window` is declared but never enforced.** Two rate features
   carry it; no code excludes them when a dataset spans capture dates, unlike the
   `within_language` gate which is fully enforced.
5. **`src/comparator/banks.py` has no test.** 58 lines, and it owns the
   traditional-vs-challenger split every group comparison depends on.
6. **The repository is heavy.** `docs/` alone is ~102 MB, mostly one video and the
   decks. Tracked data was a deliberate 21/09 decision so a fresh clone works
   without re-collecting; revisit if the diffs stop being reviewable.
