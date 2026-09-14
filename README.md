# Banking Campaigns Comparator

How Belgian banks communicate similar products differently, and what ING can learn
from it. A two-week proof of concept for ING DACI / Customer AI.

| | |
| --- | --- |
| **Requirements** | [`docs/ing_requirements.docx`](docs/ing_requirements.docx) — what must be built (PRD) |
| **Plan** | [`docs/ing_approach_and_project_plan.docx`](docs/ing_approach_and_project_plan.docx) — how, by whom, by when |
| **Feature dictionary** | [`config/feature_dictionary.yaml`](config/feature_dictionary.yaml) — the contract |
| **Team** | Siegried (lead, marketing framework) · Dan (collection, extraction) · Stephane (analysis, GenAI) |
| **Window** | Mon 14 – Fri 25 September 2026 |

## Status

Day 1–2 of 10. The analysis chain runs end to end **on synthetic fixture data**.
Nothing has been scraped yet — collection is Dan's workstream and starts once the
robots.txt review clears each domain.

| Deliverable | State |
| --- | --- |
| Feature dictionary v0.1 (D-03) | drafted, 67 features — **awaiting the Day 2 freeze** |
| Dataset schema + validator (D-04) | built and tested |
| Analysis skeleton (D-05) | runs end to end on fixture data |
| Bank profile cards | generated, 9 banks |
| Real captures (D-02) | not started — Dan, Days 1–4 |

## Quick start

```bash
pip install -r requirements.txt

python3 scripts/make_fixture.py        # synthetic dataset, for wiring only
python3 scripts/run_analysis.py        # the full chain: profiles, positioning, charts
python3 scripts/build_feature_docs.py  # regenerate docs/feature_dictionary.md
python3 -m pytest tests/ -q            # 35 tests
```

Outputs land in `outputs/`: four charts, the profile cards as markdown and JSON,
and a CSV per analysis step.

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
scripts/
  make_fixture.py                write the synthetic dataset
  run_analysis.py                the end-to-end chain
  build_feature_docs.py          YAML -> markdown
tests/                           35 tests over the contract and the analysis
data/fixtures/                   synthetic sample (committed)
data/raw/                        snapshots — gitignored, Dan's output
outputs/                         charts and tables — gitignored
```

## The synthetic fixture

`data/fixtures/synthetic_sample.csv` exists so analysis code could be written
before the scraper does. **Every value in it is invented.** Its per-bank archetypes
were built *from the claims in the ING kickoff deck*, which means:

> Running `check_deck_claims` against the fixture will always return "supported".
> That is circular by construction. It only means something against real captures.

Every fixture row is stamped `data_source = synthetic_fixture`; the validator
warns, and `run_analysis.py` prints a banner on every run.

## What analysis answers

| Question | Function | PRD |
| --- | --- | --- |
| Where does ING stand vs competitors? | `ing_vs_peers` | BO-01, FR-09 |
| Traditional or challenger? | `positioning_axis` | BO-02 |
| Which banks communicate alike? | `similarity_matrix`, `cluster_banks` | BO-03 |
| What separates the two groups? | `category_comparison` | FR-08 |
| Do the deck's observations hold? | `check_deck_claims` | FR-14 |

Sample sizes are small by design (PRD risk R-03). Nothing here computes a p-value
or claims significance — Cohen's d is reported as a description of separation, not
as a test.

## Next

1. **Day 2 — freeze the schema** with Dan. Open points in `docs/feature_dictionary.md`.
2. **Day 2 — Dan's five hand-collected rows** in this format, replacing the fixture.
3. **Days 3–5 — rubric definitions** from Siegried for the 14 judgement-based features.
4. **Day 5 — joint scoring session**; inter-rater disagreement gets reported, not hidden.
