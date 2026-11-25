# Banking Campaigns Comparator

Compares the public campaign pages of 14 Belgian banks across 6 product families
against one frozen feature dictionary, and turns the gaps into recommendations and
a generated demo site. A proof of concept for ING DACI / Customer AI.

**Guardrail:** no campaign performance data (CTR) exists here, so every finding is
"ING does X differently", never "X works better".

```
targets.yaml → robots gate → capture → scoring → analysis → report.json → recommendations → demo site
```

## Run

Prerequisites: Python 3.11, Node 22 (web UI only).

```bash
pip install -r requirements.txt
playwright install chromium            # collection only
cp .env.example .env                   # then fill in the keys you need (LLM, news)

python3 scripts/make_fixture.py        # synthetic dataset, wiring only, never evidence
python3 scripts/run_analysis.py        # profiles, positioning, charts into outputs/
python3 scripts/export_web_report.py   # web/public/*.json for the UI
python3 scripts/serve_web.py           # API + generated site, http://localhost:8000
python3 -m pytest tests/ -q            # no network: sockets are blocked in conftest.py
```

The demo site (`outputs/generated_site/`) is not versioned. Regenerate it with
`python3 scripts/serve_web.py`, then Recommendations, tick, Generate (needs an LLM key in `.env`).

Real-data order (collect, rubric merge, analyse): [docs/pipeline.md](docs/pipeline.md).
UI in development: `cd web && npm ci && npm run dev` (port 5173).

Docker (details in [docs/DOCKER.md](docs/DOCKER.md)):

```bash
docker compose up --build              # Streamlit UI 8506, API + React UI 8006
docker compose --profile monitoring up # adds the health dashboard on 8606
```

Render: `render.yaml` deploys the Streamlit UI from the `Dockerfile` (free plan,
Frankfurt). In the Render dashboard, New, Blueprint, then pick this repository.
No key is set there, so pages that need one say they are unavailable.

## Structure

```
config/feature_dictionary.yaml   the contract (+ .frozen.yaml snapshot)
src/comparator/                  library: dictionary, schema, collection/, analysis,
                                 scores, rubric, generation, recommendations, dq
scripts/                         run_collection, run_analysis, export_web_report,
                                 serve_web, rubric_sheet, check_* gates
web/                             React business UI (Vite)
streamlit_app.py                 key-free dashboard, the Docker default (8506)
services/                        health dashboard (monitoring profile)
search_interest/                 standalone Google Trends share-of-search pipeline
data/processed/, data/rubric/    collected dataset and the judged sheet
outputs/                         generated charts, tables, limitations
tests/                           pytest suite
docs/                            see below
```

`search_interest/` has its own `requirements.txt` and Streamlit app. It exports
brand search interest to `search_interest/export/`, which the main pipeline reads
as context for the Trends tab (`--trends-dir` in `run_analysis.py`). It never
feeds a performance claim. Details:
[search_interest/docs/pipeline_google_trends.md](search_interest/docs/pipeline_google_trends.md).

## Configuration

- `.env`: API keys (`DEEPSEEK_API_KEY`, optional `NEWSAPI_KEY`, `NEWSAPI_AI_KEY`,
  `SEMANTIC_SCHOLAR_API_KEY`); see `.env.example`. Never committed.
- `config/feature_dictionary.yaml`: every feature, how it is produced and compared.
  After an edit run `python3 scripts/check_schema_freeze.py`.
- `scripts/collection_targets.yaml`: banks, URLs and capture method per target.

## Limits and compliance

- One judged rubric sheet, one rater: single-judge bias is not measured.
- One pinned LLM (DeepSeek); a fallback is recorded in `extraction_model`.
- `assert_can_fetch()` checks live `robots.txt` before every fetch and fails closed;
  public pages only, no login, no CAPTCHA solving, no rate-limit or bot-detection
  evasion (LC-04). `method: headful` is a normal visible browser, not evasion.
- Repository and deliverables are internal: public release was never confirmed with ING.
- `data/raw/` page captures (third-party material) and generated HTML are not
  versioned; re-deriving features from raw pages needs a re-capture.
- `outputs/limitations.md` is generated from the data on every run.

## Docs

[pipeline](docs/pipeline.md) (runbook) · [ARCHITECTURE](docs/ARCHITECTURE.md) ·
[decisions](docs/decisions.md) · [technical deep dive](docs/technical_deep_dive.md) ·
[feature dictionary](docs/feature_dictionary.md) (generated) · [DOCKER](docs/DOCKER.md) ·
[web UI](web/README.md) · [scoring guide](data/rubric/SCORING_GUIDE.md) ·
[D-01 scope and compliance](docs/D01_scope_and_compliance_note.md) ·
[D-06 business narrative](docs/D06_business_narrative.md)
