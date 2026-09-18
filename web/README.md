# Business web UI

The findings surface for one analysis run, for the business audience (D-06),
plus two model-backed actions: writing recommendations and building a website.

```bash
python3 scripts/export_web_report.py --product-family auto   # writes web/public/report.json

python3 scripts/serve_web.py --port 8010                      # recommendations + site backend
cd web && npm install && npm run dev                          # http://localhost:5173

npm run build                                                 # static bundle in web/dist/
```

Vite proxies `/api` and `/site` to the backend, so the UI can generate
recommendations and open the generated website without a second origin. `npm run
build` still produces a folder that opens anywhere; the Analysis tab works from
that build alone.

## Two tabs

**Analysis** is the read-only snapshot described below. It reads a single
`report.json` and talks to nothing. A snapshot is the honest shape for a finding:
it is true for one dataset, at one capture date, under one scope. `npm run build`
produces a folder that opens anywhere.

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
