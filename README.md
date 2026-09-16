# Banking Campaigns Comparator

How Belgian banks communicate similar products differently, and what ING can learn
from it. A two-week proof of concept for ING DACI / Customer AI.

| | |
| --- | --- |
| **Requirements** | [`docs/ing_requirements.docx`](docs/ing_requirements.docx) — what must be built (PRD) |
| **Plan** | [`docs/ing_approach_and_project_plan.docx`](docs/ing_approach_and_project_plan.docx) — how, by whom, by when |
| **Feature dictionary** | [`config/feature_dictionary.yaml`](config/feature_dictionary.yaml) — the contract |
| **Decisions** | [`docs/decisions.md`](docs/decisions.md) — what was decided, when, and why |
| **Team** | Siegried (lead, marketing framework) · Dan (collection, extraction) · Stephane (analysis, GenAI) |
| **Window** | Mon 14 – Fri 25 September 2026 |

## Status

Day 3 of 10 (sieg 16/09). The analysis chain runs end to end on synthetic fixture
data. Real collection is under way: 4 of the (at least) 6 currently-configured
banks are captured; rubric fields wait for the Day 5 joint scoring session, and
headless-render geometry fields wait on a working Chromium in the collection
environment. See
[`docs/D01_scope_and_compliance_note.md`](docs/D01_scope_and_compliance_note.md)
for the current status of each bank.

| Deliverable | State |
| --- | --- |
| Feature dictionary v0.1 (D-03) | frozen (Day 2) — 97 features, `feature_dictionary.frozen.yaml` in sync |
| Dataset schema + validator (D-04) | built and tested |
| Analysis skeleton (D-05) | runs end to end on fixture data |
| Bank profile cards | generated, 9 banks (on fixture data) |
| Real captures (D-02) | in progress — KBC/N26/Belfius/ING captured; BNP Fortis/Revolut/Argenta/Crelan/bunq still to collect, see D-01 |

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in DEEPSEEK_API_KEY - .env is gitignored

python3 scripts/make_fixture.py           # synthetic dataset, for wiring only
python3 scripts/run_analysis.py           # the full chain: profiles, positioning, charts
python3 scripts/run_generation.py         # step 5: generate 2 variants and score them
python3 scripts/run_generation.py --dry-run   # ...without calling a model
python3 scripts/check_schema_freeze.py    # enforce the Day 2 freeze rule

# real data
python3 scripts/run_collection.py --config scripts/collection_targets.yaml --method headless
python3 scripts/rubric_sheet.py emit      # scoring sheets for the 13 human-scored features
python3 scripts/rubric_sheet.py agreement --sheets data/rubric/*_scores.csv
python3 scripts/run_analysis.py --dataset data/processed/campaigns.csv --no-strict
python3 scripts/build_feature_docs.py     # regenerate docs/feature_dictionary.md
python3 -m pytest tests/ -q               # 158 tests
```

Outputs land in `outputs/`: four charts, `charts.md` explaining what each one
measures and what it cannot support, the profile cards as markdown and JSON, and
a CSV per analysis step.

`charts.md` is generated, not written by hand — `outputs/` is wiped on every run,
and the "what this run shows" paragraphs are built from the same objects the
charts are drawn from, so the prose cannot drift away from the picture.

## The feature dictionary is the contract

`config/feature_dictionary.yaml` is the single source of truth. The dataset schema,
the validator and `docs/feature_dictionary.md` are all derived from it, so they
cannot drift apart. Edit the YAML; never edit the generated markdown.

Each feature declares:

- **extraction** — `automatic` (code, reproducible), `rubric` (human, against a
  written scale), `model_assisted` (LLM/vision, prompt recorded), or `derived`.
  This is what determines how far a value can be trusted.
- **comparability** — `cross_language`, `within_language` (word counts and
  readability cannot cross NL/FR/EN), or `within_capture_window` (rates move).
- **tier** — `core` is the Day 6 MVP minimum (53 features); `extended` is added
  only after the gate passes (14 features).

**Freeze rule:** after the Day 2 freeze, columns may be *added* but never renamed
or removed without all three of us agreeing. The analysis code depends on them.

Two checks enforce it, deliberately:

- `tests/test_schema.py::test_dictionary_matches_frozen_snapshot` — byte equality
  against `feature_dictionary.frozen.yaml`. Catches an *accidental* edit.
- `scripts/check_schema_freeze.py` — the rule itself. Additions pass; renames,
  removals, type changes, narrowed ranges or categories, tier demotions and
  tightened nullability fail, naming the feature.

Byte equality alone is not the rule: it fails on an addition (which the rule
permits) and it *passes* on a rename, because updating both files makes the bytes
match again. A rename is the change that actually breaks analysis code.

## One model labels every bank

DeepSeek `deepseek-chat` is the pinned model ([D6](docs/decisions.md)). Put the
key in `.env` (gitignored); `scripts/_bootstrap.py` loads it, so no `export` is
needed. A real environment variable still wins over the file. Never put a key in
`.env.example` — that file is tracked and public. About a
quarter of the dictionary is model-assisted, and the provider chain falls back
when one is rate-limited — so a run could label ING with one model and Revolut
with another. Every row now records `extraction_model`, and `validate()` warns
when a dataset mixes models and names which banks got which. A difference between
banks has to be a difference between banks, not between two judges (NFR-02).

## Two things a range check cannot catch

**A capture can be honestly measured and still be the wrong page.** The first live
collection returned ING as an unrendered JavaScript shell (16 words — the `<title>`,
twice) and BNP Paribas Fortis as a maintenance notice. Every numeric feature on
those rows was in range. `collection/quality.py` judges whether a capture looks
like a campaign page at all, and the verdict travels with the row in
`capture_quality`. Analysis excludes `unusable` rows and says which.

**13 core features are scored by a person**, so a collected dataset can never pass
strict validation on its own. `scripts/rubric_sheet.py` emits one sheet per rater
with the screenshot path, merges completed sheets back, and reports inter-rater
agreement — which is what NFR-05 actually asks for.

## Limitations are generated, not remembered

`outputs/limitations.md` (D-09) is written from the dataset on every run. If two
captures failed it names them and why; if the focus bank is missing it says which
questions that makes unanswerable; if the rubric is unscored it says so. A
limitation nobody can quietly drop on Day 9 is worth more than a well-written
paragraph.

## Step 5 — campaign generation (stretch)

`scripts/run_generation.py` derives a numeric target from the data (ING's own
levels for the on-brand variant; the challenger group's medians for the
challenger-style one), asks the model for a campaign, renders it to HTML, and
scores it **with the same extractor that reads real bank pages**. The loop only
means something because there is exactly one measuring stick in this repo.

Targets never include a feature the guardrails forbid hitting — you cannot ask a
generator to match a bank's density of figures while forbidding it to invent
figures. Hitting the target means the generator followed instructions; it says
nothing about whether the campaign would perform better (plan risk P-08).

## What the validator refuses

`comparator.schema.validate` is deliberately strict — a silent schema drift on
Day 6 costs more than a loud failure on Day 2. It fails on missing required
columns, columns absent from the dictionary, values outside a declared range or
category, duplicate `page_id`, nulls in a non-nullable feature, and — as a hard
compliance gate — **any row whose `robots_allowed` is false** (LC-01).

It warns, rather than fails, on synthetic or LLM-generated rows and on a bank
missing a core feature entirely (DR-07).

## Layout

```
config/feature_dictionary.yaml   the contract
src/comparator/
  dictionary.py                  loads and self-checks the dictionary
  schema.py                      dataset types, validation, read/write
  fixtures.py                    synthetic rows (everything invented)
  profiles.py                    bank profile cards
  analysis.py                    positioning, group comparison, similarity
  charts.py                      the four charts
  freeze.py                      the Day 2 freeze rule, enforced semantically
  generation.py                  step 5: targets, brief, rendering, scoring
  generation_guardrails.py       step 5 safety checklist (Appendix B.2)
  report.py                      the generated chart companion
  collection/                    compliance, scraper, headless render, LLM, quality gate
  rubric.py                      scoring sheets, merge, inter-rater agreement
  limitations.py                 D-09, generated from the dataset
scripts/
  make_fixture.py                write the synthetic dataset
  run_analysis.py                the end-to-end chain
  run_collection.py              real captures: compliance -> scrape -> extract -> validate
  run_generation.py              CLI for step 5 (generation.py)
  check_schema_freeze.py         CLI for the freeze rule (freeze.py)
  build_feature_docs.py          YAML -> markdown
tests/                           124 tests
data/fixtures/                   synthetic sample (committed)
data/raw/                        snapshots — gitignored, Dan's output
outputs/                         charts and tables — wiped and regenerated on every
                                  run; sieg 16/09: currently COMMITTED to git despite
                                  that (no .gitignore rule for it) - team decision
                                  needed on whether that is intentional
```

## No synthetic data in the repo

`src/comparator/fixtures.py` builds a synthetic dataset **in memory** for the test
suite. Nothing synthetic is committed and nothing synthetic reaches `outputs/`.

That is deliberate. The fixture's per-bank archetypes were written *from* the
claims in the ING kickoff deck, so an analysis run against it always confirms
them — `check_deck_claims` comes back "supported" every time, by construction. A
committed synthetic CSV sitting next to `run_analysis.py` is an invitation to run
it and read the result as a finding.

`scripts/make_fixture.py` still writes one to `data/fixtures/` if you want it for
local development. That path is gitignored.

Everything in `outputs/` comes from `data/processed/campaigns.csv` — real captures.

## What analysis answers

| Question | Function | PRD |
| --- | --- | --- |
| Where does ING stand vs competitors? | `ing_vs_peers` | BO-01, FR-09 |
| Traditional or challenger? | `positioning_axis` | BO-02 |
| Which banks communicate alike? | `similarity_matrix`, `cluster_banks` | BO-03 |
| What recurring patterns cross the whole market? | `recurring_patterns` | BO-04 |
| What separates the two groups? | `category_comparison` | FR-08 |
| Which gaps are worth arguing from, with evidence? | `insight_candidates` | BO-06, FR-10 |
| Do the deck's observations hold? | `check_deck_claims` | FR-14 |

BO-05 (reusable feature framework) isn't a function - it's demonstrated by
adding a bank via config, not code (FR-16). BO-07 (compliant, reproducible
method) lives in `collection/compliance.py` and `schema.py`, not here.

Sample sizes are small by design (PRD risk R-03). Nothing here computes a p-value
or claims significance — Cohen's d is reported as a description of separation, not
as a test.

## Next

1. **Day 2 — freeze the schema** with Dan. Open points in `docs/feature_dictionary.md`.
2. **Day 2 — Dan's five hand-collected rows** in this format, replacing the fixture.
3. **Days 3–5 — rubric definitions** from Siegried for the 14 judgement-based features.
4. **Day 5 — joint scoring session**; inter-rater disagreement gets reported, not hidden.
