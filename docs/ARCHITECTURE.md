# Architecture

Central bet: every number on screen comes from one definition, and anything
judgement-based says so. Runbook: [pipeline.md](pipeline.md). Decisions:
[decisions.md](decisions.md).

## Runtime

```
Docker Compose
  streamlit  :8501 (host 8506)  key-free dashboard, reads data baked into the image
  api        :8000 (host 8006)  FastAPI: React bundle at /, /api/*, generated site at /site/
  dashboard  :8080 (host 8606)  health monitor, profile "monitoring"
.env  ->  LLM keys (DeepSeek, fallbacks), NewsAPI, Semantic Scholar
```

CI: `tests.yml` (ruff, pytest, schema freeze, data-quality gate, web build) and
`publish.yml` (build, smoke test, push to GHCR and Docker Hub). See
[DOCKER.md](DOCKER.md).

## Data flow

`scripts/collection_targets.yaml` → `collection/compliance.py` (robots gate) →
`scraper.py` / `render.py` (static, headless, headful) → deterministic features +
one LLM call per page → `data/processed/campaigns.csv` → judged rubric sheet merged
into `campaigns_scored.csv` → `analysis.py` → `outputs/` and `web/public/report.json`
→ `recommendations.py` → `site_generator.py`.

## The feature dictionary is the contract

`config/feature_dictionary.yaml` is the source of truth; the schema, the validator
and `docs/feature_dictionary.md` derive from it. Each feature declares:

- **extraction**: `automatic`, `rubric` (human, written scale), `model_assisted`
  (LLM, prompt recorded) or `derived`. It decides how far a value can be trusted.
- **comparability**: `cross_language`, `within_language` (word counts and
  readability cannot cross NL/FR/EN) or `within_capture_window` (declared, not enforced).
- **tier**: `core` or `extended`.

Freeze rule: columns may be added, never renamed or removed. A new value in an
existing enumeration counts as an addition. Enforced by `tests/test_schema.py`
(byte equality) and `scripts/check_schema_freeze.py` (the rule). See D5.

## Principles

- **One model labels every bank.** `extraction_model` is recorded per row and
  `validate()` warns on a mixed dataset (D6). Nothing pre-fills the rubric sheet.
- **Compare like for like.** `--product-family` restricts a run to one family;
  `within_language` features are excluded when languages mix.
- **The validator is strict.** It fails on missing columns, unknown columns,
  out-of-range values, duplicate `page_id`, nulls in required features, and any row
  with `robots_allowed = false`. It warns on synthetic rows and on a bank missing a
  core feature.
- **Data quality is scored.** `dq.py` grades completeness, validity, uniqueness,
  consistency and timeliness; the first three gate CI (D7).
- **Withdrawal is an outcome.** Features that describe the capture rather than
  the bank are listed in `analysis.CAPTURE_INVALID_FEATURES` and printed in the
  feature accounting (D13).
- **No synthetic data in outputs.** `fixtures.py` builds a dataset in memory for
  tests; its archetypes encode the kickoff claims, so a fixture run always
  confirms them and is never evidence. Do not commit `data/fixtures/`.
- **Small samples.** No p-value is computed; Cohen's d describes separation only.

## What analysis answers

| Question | Function |
| --- | --- |
| Where does ING stand vs peers? | `ing_vs_peers` |
| Traditional or challenger? | `positioning_axis` |
| Which banks communicate alike? | `similarity_matrix`, `cluster_banks` |
| Recurring market patterns? | `recurring_patterns` |
| What separates the two groups? | `category_comparison` |
| Which gaps merit an argument? | `insight_candidates` |
| Do the kickoff observations hold? | `check_deck_claims` |

## Signals that are not page measurements

- **Search interest** (`trends.py`, `search_interest/`): context only, never
  regressed onto a page feature. It selects which competitor brands to study;
  `benchmarks.py` then reports what their pages measurably do.
- **News themes** (`reputation.py`): what each bank is in the news about, never
  sentiment. A failed fetch is `null`, not zero.
- No performance data exists: every recommendation is a hypothesis.

## Web UI

`web/` (React, Vite) has findings tabs (Analysis, Trends, Reputation,
Recommendations) and read-only operator tabs (Home, Bank profiles, Data, Rubric,
Collection, Research). `scripts/export_web_report.py` writes `report.json`,
`operations.json` and `trends.json` from the same library calls, so the UI does no
arithmetic. There is no endpoint that edits a dataset row, a rubric cell or the
dictionary, and no live scoring screen. Research queries Semantic Scholar through
`serve_web.py`. Details: [../web/README.md](../web/README.md).
