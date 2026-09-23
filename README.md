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

The comparison covers **51 pages across 14 banks and 6 product families**
(`current_account_pack`, `investment`, `savings_account`, `pension`,
`mortgage`, `term_account`), with nothing excluded; the positioning view
compares one family at a time (DR-04), currently 18 current-account pages.
Mostly Belgian French, plus two English pages and one Dutch — so the eight
`within_language` features are excluded from the comparison rather than
compared across languages. BNP Paribas Fortis is in via `method: headful`
(its edge returns HTTP 503 to every headless client but serves a real headful
browser); there is no manual-capture-only bank left.

**The rubric runs on one judged sheet**: Siegried scores the 13
judgement-based features against the written scales in
`data/rubric/SCORING_GUIDE.md`, and that sheet is the only human input the
comparator reads. There is no second rater and no inter-rater reliability
figure. That is the chosen scope of this proof of concept, not an oversight —
the point being demonstrated is that the pipeline turns concrete inputs about
real banks into a defensible structure and usable proposals. Single-judge
bias is real, it is named in `outputs/limitations.md`, and it is listed there
as the first thing to add for a production build.

| Deliverable | State |
| --- | --- |
| Feature dictionary v0.1 (D-03) | frozen (Day 2), additions since allowed by the freeze rule — **104 features**, both dictionary copies in sync |
| Dataset schema + validator (D-04) | built and tested; `campaigns_scored.csv` passes |
| Analysis skeleton (D-05) | runs end to end on real captures |
| Bank profile cards | generated for every compared bank (real data) |
| Real captures (D-02) | **51 pages / 14 banks / 6 product families** collected; every bank in the PRD list that publishes a comparable page has one, including BNP Paribas Fortis (`headful`) and Keytrade (`headful` + a lighter navigation wait) |
| Rubric scoring | **one judged sheet**, merged into the dataset by `rubric_sheet.py merge`. No second rater and no reliability measure — the chosen scope, stated in `outputs/limitations.md` and listed there as future work |
| Operator surface in the web UI | Home, Bank profiles, Data, Rubric, Collection and Research tabs read the run's own files through `operations.json` — read-only, no pipeline control, no scoring, no dataset editing |

Test suite: **401 passing, 1 skipped** (sieg 22/09). Pinned model per D6: `deepseek-chat` in decisions.md,
but every `extraction_model` value actually on disk reads `deepseek/deepseek-flash` (and now, after
tonight's re-fetches, occasionally `groq/openai/gpt-oss-120b` on fallback) — flagged for
Stephane (D6 owner), not resolved here.

## Start here

| I want to… | Read |
| --- | --- |
| run collection, scoring, analysis and the export | [`docs/pipeline.md`](docs/pipeline.md) |
| understand why it is built this way, and what it refuses to claim | [`docs/design.md`](docs/design.md) |
| use the web UI (Analysis, Trends, Reputation, Recommendations, plus the operator tabs: profiles, data, rubric, collection, research) | [`web/README.md`](web/README.md) |
| know what was decided and when | [`docs/decisions.md`](docs/decisions.md) |
| see the bank scope and compliance position | [`docs/D01_scope_and_compliance_note.md`](docs/D01_scope_and_compliance_note.md) |

### Every document in the repo

| File | What it is |
| --- | --- |
| [`docs/pipeline.md`](docs/pipeline.md) | **runbook** — commands in order, where data lands, the quality gate, manual capture, optional signals |
| [`docs/design.md`](docs/design.md) | **design** — the feature-dictionary contract, the freeze rule, one pinned model, what the validator refuses, what analysis answers |
| [`docs/decisions.md`](docs/decisions.md) | **decision log** — what was decided, when, and why (dated entries) |
| [`docs/D01_scope_and_compliance_note.md`](docs/D01_scope_and_compliance_note.md) | **scope + compliance** — banks in scope, product family and language choices, per-domain robots.txt findings |
| [`docs/D06_business_narrative.md`](docs/D06_business_narrative.md) | **business narrative (D-06)** — draft insights for the ING audience; figures pending re-verification after the 21/09 scope change |
| [`docs/feature_dictionary.md`](docs/feature_dictionary.md) | **generated** from `config/feature_dictionary.yaml` by `scripts/build_feature_docs.py` — never edit by hand |
| [`data/rubric/SCORING_GUIDE.md`](data/rubric/SCORING_GUIDE.md) | how a human rater fills the 13 judgement-based features |
| [`docs/stakeholder_questions_18-09.md`](docs/stakeholder_questions_18-09.md) | the ten questions put to Diego and Victor |
| [`docs/web_ui_proposal.md`](docs/web_ui_proposal.md) | the accepted UI proposal — superseded by `web/README.md` |
| [`web/README.md`](web/README.md) | the business web UI: four tabs, recommendations, generated site + explanation mode |
| [`outputs/charts.md`](outputs/charts.md) | **generated** by `scripts/run_analysis.py` — what each chart measures and cannot support |
| [`outputs/bank_profiles.md`](outputs/bank_profiles.md) | **generated** — one profile card per compared bank |
| [`outputs/limitations.md`](outputs/limitations.md) | **generated (D-09)** — what this run cannot support, from the dataset itself |
| [`outputs/search_interest_context.md`](outputs/search_interest_context.md) | **generated** — the search-interest context paragraph the Trends work produces |

```bash
pip install -r requirements.txt
cp .env.example .env        # DEEPSEEK_API_KEY; optionally NEWSAPI_KEY / NEWSAPI_AI_KEY
python3 scripts/run_analysis.py                 # end-to-end on real captures
python3 -m pytest tests/ -q                     # 368 passing, no network
```

## The short version of the design

- **One measuring stick.** Every number comes from `config/feature_dictionary.yaml`;
  the schema, validator and docs are derived from it, and each feature declares
  how far it can be trusted (`automatic`, `rubric`, `model_assisted`, `derived`)
  and how it may be compared (`cross_language`, `within_language`,
  `within_capture_window`).
- **One pinned model.** `deepseek-flash` labels every bank, so a difference
  between banks is a difference between banks, not between two judges (NFR-02).
- **Judgement is labelled.** Human-scored and measured values look different on
  screen. The project runs on one judged sheet by one named person, so no
  reliability figure is claimed - that is stated, not left to be inferred.
- **No performance data exists here.** Nothing links a design choice to a click, a
  conversion or a sale. Every recommendation is a hypothesis ING could test.
- **Three signals beside the page data, all fenced off from that claim:** search
  interest (Trends tab, context only), news themes (Reputation tab, never
  sentiment), and generated campaigns (scored with the same extractor as real
  pages, and marked as generated).

Details, including the freeze rule and the validator's refusals, are in
[`docs/design.md`](docs/design.md).

## Layout

```
config/feature_dictionary.yaml   the contract
docs/                            scope, decisions, design, runbook, UI proposal
web/                             React UI: the findings snapshot + the read-only operator views (+ its own README)
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
  recommendations.py             LLM advice grounded in one report (web UI tab)
  site_generator.py              10-page ING-styled site from selected recommendations
  report.py                      the generated chart companion
  collection/                    compliance, scraper, headless render, LLM, quality gate
  rubric.py                      the judged sheet: emit, and merge into the dataset
  limitations.py                 D-09, generated from the dataset
  trends.py                      bridge to the Google Trends benchmark (Trends tab)
  derive.py                      recompute derived features after any change
  banks.py                       canonical bank -> category facts
  ai_score.py                    6-axis composite score per bank, deterministic, no LLM call
  cross_sell.py                  cross-sell score + product co-occurrence matrix
  reputation.py                  optional news headline themes, newsapi.org and/or newsapi.ai
  market_context.py              thin standalone Finnhub lookup, not wired into the pipeline
  research.py                    thin standalone Semantic Scholar lookup, not wired into the pipeline
  geo_trends.py                  Google Trends by Belgian region (own pytrends calls)
scripts/
  make_fixture.py                write the synthetic dataset
  run_analysis.py                the end-to-end chain
  run_collection.py              real captures: compliance -> scrape -> extract -> validate
  run_generation.py              CLI for step 5 (generation.py)
  export_web_report.py           one JSON snapshot + trends payload + the operator snapshot (dictionary/dataset/collection/rubric)
  serve_web.py                   backend for the UI: recommendations, generated site, research search, downloads, captures
  check_schema_freeze.py         CLI for the freeze rule (freeze.py)
  build_feature_docs.py          YAML -> markdown
  rubric_sheet.py                emit / merge (one judged sheet, no inter-rater layer)
  reextract_model_fields.py      backfill model_assisted fields from saved HTML, no re-fetch
  fix_rate_fields.py             re-derive rate_shown/rate_value_pct from saved HTML, no LLM call
  fix_cta_count.py               re-derive cta_count/cta_above_fold from saved HTML, no LLM call
  import_captures.py             import pages a person saved from a normal browser
  browser_audit.py               Playwright audit of the UI + generated site
streamlit_app.py                 earlier dashboard for share.streamlit.io; its views now live in the React UI's operator tabs
tests/                           387 tests, no network calls
data/rubric/                     human + model scoring sheets (tracked)
data/raw/                        snapshots (tracked since 21/09 — see Next)
data/processed/                  datasets (tracked since 21/09)
outputs/                         charts and tables — tracked, regenerated every run
```

## Next

1. **Complete the judged sheet.** Siegried is scoring every page against the
   written scales. The gap to close is coverage, not reliability: a page with no
   score leaves its judged features blank, and a judged feature missing on even
   one bank is dropped from the comparison entirely.
2. **Import the captures the sheet already points at** — several scored page ids
   match captures that sit in `data/raw/` but were never added to the dataset, so
   those rows join nothing and are silently ignored by the merge.
3. **Measure single-judge bias** — out of scope here, and the first thing a
   production build should add: a second independent rater on a sample, with
   agreement reported.
4. **Re-run the analysis after scoring**, then the web export, so the profile
   cards carry judged features rather than model-judged ones.
5. **Keep the tracked-data decision under review** — `data/raw/`, `data/processed/`
   and `outputs/` are committed by team decision (21/09), so a collection or
   analysis run now produces a large diff, including binary charts and screenshots.
   Revisit if the diffs stop being reviewable; the `.gitignore` rules are one
   revert away.
