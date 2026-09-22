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

<!-- sieg 22/09: refreshed again - the 21/09 paragraph described the
current_account_pack-only scope (14 banks/16 pages) and a 387-test suite,
both superseded the same day by the scope restoration (decisions.md, "sieg
21/09, scope restored..."), by tests added since, and by the belfius_other_fr_01
relabel below. Rubric progress now moves fast enough within a day that this
paragraph is not the place to chase exact counts - see data/rubric/*_scores.csv. -->
**22/09.** The comparison covers **50 pages across 14 banks and 6 product
families** (`current_account_pack`, `investment`, `savings_account`,
`pension`, `mortgage`, `term_account`), with nothing excluded. `other` is
gone as a category: `belfius_other_fr_01` was Belfius's pension page,
mislabeled - relabelled in place (same page_id, same capture, `product_family`
corrected), not re-collected. BNP Paribas Fortis is in via `method: headful`
(its edge returns HTTP 503 to every headless client but serves a real headful
browser); there is no manual-capture-only bank left. **Rubric scoring is
split 2-raters-per-bank across Dan, Siegried and Stephane** rather than all
three scoring all 50 pages - see `docs/pipeline.md` for the current split
and the open question on rubric rows whose `page_id` predates a re-collection.

| Deliverable | State |
| --- | --- |
| Feature dictionary v0.1 (D-03) | frozen (Day 2), additions since allowed by the freeze rule — **104 features**, both dictionary copies in sync |
| Dataset schema + validator (D-04) | built and tested; `campaigns_scored.csv` passes |
| Analysis skeleton (D-05) | runs end to end on real captures |
| Bank profile cards | generated for every compared bank (real data) |
| Real captures (D-02) | **50 pages / 14 banks / 6 product families** collected; every bank in the PRD list that publishes a comparable page has one, including BNP Paribas Fortis (`headful`) and Keytrade (`headful` + a lighter navigation wait) |
| Rubric scoring (Day 5) | **three independent human raters** (sieg 22/09: Stephane's scores are no longer machine-proposed/adopted - verified 0 of 13 overlapping pages identical to the model). Split 2-raters-per-bank across Dan/Siegried/Stephane (see `docs/pipeline.md`); exact per-rater counts move within the day, see `data/rubric/*_scores.csv`. The model's own sheet is never a pre-fill |
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
| [`docs/day5_scoring_disagreement.md`](docs/day5_scoring_disagreement.md) | **generated** from the scoring sheets by `scripts/rubric_sheet.py report` |
| [`docs/day5_scoring_disagreement_template.md`](docs/day5_scoring_disagreement_template.md) | the template that generated file renders |
| [`docs/day6_gate_discussion_notes.md`](docs/day6_gate_discussion_notes.md) | Day 6 gate notes and the per-bank pipeline status |
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
- **Judgement is labelled.** Human-scored, model-scored and measured values look
  different on screen, and the rubric model writes to its own sheet so the
  agreement figure keeps measuring agreement.
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
  rubric.py                      scoring sheets, merge, inter-rater agreement
  limitations.py                 D-09, generated from the dataset
  trends.py                      bridge to Dan's Google Trends benchmark (Trends tab)
  rubric_model.py                model as a third rater (text-inferable only)
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
  rubric_sheet.py                emit / model / merge / agreement / report
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

1. **Finish the rubric properly.** Two independent humans now overlap on 10 pages
   (Siegried, Dan), so the first real agreement number exists; the work left is
   coverage — Dan's remaining pages, the 14 rows whose screenshots are not on this
   machine, and tightening the wording for the six features below the 60% bar.
2. **Extend collection coverage** — the manual-capture path is no longer needed for
   BNP Paribas Fortis or Revolut (both captured), but the rubric still has to reach
   the six banks added this week, whose judged features are blank rather than guessed.
3. **Re-run the analysis after scoring**, then the web export, so the profile
   cards carry judged features rather than model-judged ones.
4. **Keep the tracked-data decision under review** — `data/raw/`, `data/processed/`
   and `outputs/` are committed by team decision (21/09), so a collection or
   analysis run now produces a large diff, including binary charts and screenshots.
   Revisit if the diffs stop being reviewable; the `.gitignore` rules are one
   revert away.
