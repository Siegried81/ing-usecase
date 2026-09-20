# Business web UI

The findings surface for one analysis run, for the business audience (D-06),
plus two model-backed actions: writing recommendations and building a website.

```bash
python3 scripts/export_web_report.py --product-family auto   # writes report.json + trends.json

python3 scripts/serve_web.py --port 8000                      # recommendations + site backend
cd web && npm install && npm run dev                          # http://localhost:5173

npm run build                                                 # static bundle in web/dist/
```

Vite proxies `/api` and `/site` to the backend, so the UI can generate
recommendations and open the generated website without a second origin. `npm run
build` still produces a folder that opens anywhere; the Analysis tab works from
that build alone.

## Four tabs

**Analysis** is the read-only snapshot described below. It reads a single
`report.json` and talks to nothing. A snapshot is the honest shape for a finding:
it is true for one dataset, at one capture date, under one scope. `npm run build`
produces a folder that opens anywhere.

**Trends** is Dan's Google Trends benchmark given a home of its own. The exporter
writes the series separately to `trends.json` (it is ~800 KB of weekly points, too
large to inline in `report.json`, which carries only a small summary and the
`data_url` the tab fetches). The tab shows the five-year weekly search interest per
bank and product sheet, the spikes Dan's detector flags, the known structural
events, and the campaign catalogue matched to those spikes. Anomaly detection is a
port of `kbc-ing-benchmark/analysis/anomaly_detection.py`, tested against the same
inputs, so the tab and Dan's Streamlit app cannot report different spikes.

The guardrail is not a footnote here: **search interest is context, never an
outcome.** The tab leads with it, and the payload carries the sentence so no view
can drop it. Nothing in `trends.py` regresses a search value onto a page feature,
and the tab deliberately offers no per-page number to regress.

If `kbc-ing-benchmark/export/` is absent, `trends.json` is not written and the tab
renders an empty state; nothing else is affected. The pipeline only reads Dan's CSV
export — it does not need `pytrends`, `streamlit` or `plotly`.

**Reputation** shows recent news headline *themes* per bank (innovation,
crisis, results, ...) from NewsAPI, classified by one structured model call -
counts only, deliberately never sentiment (see
`comparator/reputation.py`'s docstring for why). Renders an honest "not
configured" state when `NEWSAPI_KEY` is unset, same pattern as Trends when
Dan's export is missing - nothing else is affected either way.

**Recommendations** is the one place a model is allowed to opine. It asks the
pinned model to turn this run's own numbers into advice, shows each
recommendation next to the features it was argued from, and lets a reader **tick
the ones worth implementing**. Only the ticked subset is passed to the site
builder. A feature id the model invented is dropped before the list is shown, so
nothing links to evidence that does not exist.

The **Generate ING website** button turns the selected recommendations into ten
HTML pages in ING's house style - orange `#FF6200`, ING blue `#000066`, black and
white, and ING's own logo and illustration SVGs, downloaded once and served with
the site. Copy is written by the same pinned model, one call per page, in a
language you pick (defaults to Belgian French). Ten parallel calls means the site
builds in the background and the UI polls; a page that fails is rendered from a
deterministic fallback and marked `fallback` in the manifest rather than passed
off as generated. When it is ready, **Browse generated website** opens it.

The site is written to `outputs/generated_site/` and served at `/site/`. Nothing
in the generated copy invents a rate, fee or product term: placeholders like
`[TAUX]` mark every figure a compliance team would have to supply.

## What it deliberately does

- **Leads with the answer**, not the method. Positioning first, features second.
- **Carries its own scope.** Product family, banks, capture date, language and
  the banks that are *not* in the comparison sit above the first number, not in
  a footnote.
- **Marks judgements as judgements.** `judged` means a person scored it against a
  rubric; `model-judged` means a language model did and no human has checked it.
  Everything unmarked was counted or measured. A business reader cannot otherwise
  tell that "clarity of the offer" is an opinion and "words on the page" is not.
  Derived features inherit the trust of their sources, so AIDA coverage is marked
  even though it is computed.
- **Never shows generated copy alone.** The synthetic label, the scorecard and
  the "says nothing about performance" line are in the same block a stakeholder
  would screenshot (plan risk P-08).
- **Ends on what it cannot support**, rendered from `limitations.md`'s own source
  rather than retyped.

## What it deliberately is not

No pipeline control, no scoring, no dataset editing. Recommendations are written
from an existing report, and the site from selected recommendations, but neither
re-runs collection or analysis. The operator tooling is a separate question (see
`docs/web_ui_proposal.md`).

## Keeping it honest

`src/types.ts` mirrors `scripts/export_web_report.py`; the recommendation and
site shapes mirror `src/comparator/recommendations.py` and
`src/comparator/site_generator.py`. Change one, change the other. Every figure
comes from the library through the exporter — the UI does no arithmetic of its
own, so there is no second definition of any number on screen.

The backend (`scripts/serve_web.py`) only orchestrates the two model calls and
serves the result. It re-derives nothing: recommendations read `report.json`,
the site reads the recommendations. One direction only.

## Tested without a model

`tests/test_recommendations_and_site.py` monkeypatches the model entry points, so
the suite still makes no network calls. It covers the local logic: dropping an
invented feature id, retrying a bad response, selecting a subset in order, and
rendering ten pages with a marked fallback when a page fails.
