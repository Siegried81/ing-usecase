# Design: how the comparator is built, and what it refuses to claim

Split out of `README.md` (steve 21/09). The runbook is
[`pipeline.md`](pipeline.md); the decision log is [`decisions.md`](decisions.md).
The short version of this file is the project's central bet: **every number on
screen comes from one definition, and anything judgement-based says so.**

## The feature dictionary is the contract

`config/feature_dictionary.yaml` is the single source of truth. The dataset
schema, the validator and `docs/feature_dictionary.md` are all derived from it,
so they cannot drift apart. Edit the YAML; never edit the generated markdown.

Each feature declares:

- **extraction** — `automatic` (code, reproducible), `rubric` (human, against a
  written scale), `model_assisted` (LLM/vision, prompt recorded), or `derived`.
  This is what determines how far a value can be trusted.
- **comparability** — `cross_language`, `within_language` (word counts and
  readability cannot cross NL/FR/EN), or `within_capture_window` (rates move).
- **tier** — `core` is the MVP minimum; `extended` is added only after the gate
  passes. 104 features today.

**Freeze rule:** after the Day 2 freeze, columns may be *added* but never renamed
or removed without all three of us agreeing. The analysis code depends on them.
New *values* inside an existing enumeration count as an addition — that is how
the bank list grew to twelve on 21/09 (see `D01_scope_and_compliance_note.md`).

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

The pinned model is **`deepseek-flash`** ([D6](decisions.md); it replaced
`deepseek-chat` when DeepSeek retired that alias). Put the key in `.env`
(gitignored); `scripts/_bootstrap.py` loads it, so no `export` is needed. A real
environment variable still wins over the file. Never put a key in `.env.example`
— that file is tracked and public.

About a quarter of the dictionary is model-assisted, and the provider chain falls
back when one is rate-limited — so a run could label ING with one model and
Revolut with another. Every row records `extraction_model`, and `validate()` warns
when a dataset mixes models and names which banks got which. A difference between
banks has to be a difference between banks, not between two judges (NFR-02).

The same check applies to the rubric: `rubric_sheet.py model` writes to its **own**
sheet and never pre-fills a human one. A pre-filled sheet gets rubber-stamped, and
the NFR-05 agreement figure would then measure how persuasive the model's guess was
rather than how well two people agree.

## Compare like for like, not everything at once

`--product-family current_account_pack` (or `auto`) restricts the comparison to
one product family. Pooling families confounds every cross-bank difference with
the product — a mortgage page and a current-account page differ because the
*products* differ (DR-04). The runner prints which families are comparable, and
refuses to continue if one side of the traditional/challenger split is empty.

Language works the same way: the dataset is collected in Belgian French for
comparability, and the eight `within_language` features are excluded from every
cross-bank comparison when a page in another language sneaks in.

## What the validator refuses

`comparator.schema.validate` is deliberately strict — a silent schema drift costs
more than a loud failure. It fails on missing required columns, columns absent
from the dictionary, values outside a declared range or category, duplicate
`page_id`, nulls in a non-nullable feature, and — as a hard compliance gate —
**any row whose `robots_allowed` is false** (LC-01).

It warns, rather than fails, on synthetic or LLM-generated rows and on a bank
missing a core feature entirely (DR-07).

## No synthetic data in the repo

`src/comparator/fixtures.py` builds a synthetic dataset **in memory** for the test
suite. Nothing synthetic is committed and nothing synthetic reaches `outputs/`.

That is deliberate. The fixture's per-bank archetypes were written *from* the
claims in the ING kickoff deck, so an analysis run against it always confirms
them — `check_deck_claims` comes back "supported" every time, by construction. A
committed synthetic CSV sitting next to `run_analysis.py` is an invitation to run
it and read the result as a finding.

`scripts/make_fixture.py` still writes one to `data/fixtures/` if you want it for
local development. That path is gitignored. Everything in `outputs/` comes from
`data/processed/campaigns.csv` — real captures.

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

BO-05 (reusable feature framework) isn't a function — it's demonstrated by adding
a bank via config, not code (FR-16). BO-07 (compliant, reproducible method) lives
in `collection/compliance.py` and `schema.py`.

Sample sizes are small by design (PRD risk R-03). Nothing here computes a p-value
or claims significance — Cohen's d is reported as a description of separation, not
as a test. With ten banks, one of which is a single page per family, a group mean
is an anecdote (FR-13/F-14 scale).

## The three signals that are not page measurements

Two optional signals sit beside the page analysis, and both are fenced off from
the performance claim:

- **Search interest** (`trends.py`, the Trends tab) is context, never an outcome.
  It measures what people searched for, not what a campaign achieved, and it is
  not regressed onto any page feature — the module refuses to emit a per-page
  number for exactly that reason. The Recommendations tab can optionally use a
  slice of it to suggest *timing and focus*, and those recommendations are marked
  `basis="trends"`, kept in their own group, and forbidden from citing a page
  feature as evidence.
- **News themes** (`reputation.py`, the Reputation tab) count what each bank is in
  the news *about* — never sentiment. Sentiment scoring was explicitly out of
  scope; themes turn the brief's own "réputation, innovations, crises" framing
  into a closed, countable list.

Neither makes this a performance study. **No performance data exists in this
project**: nothing links a design choice to a click, a conversion or a sale. Every
recommendation is a hypothesis ING could test, never a cause (PRD 5.2).
