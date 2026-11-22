# Business web UI

React 18 + Vite front end for one analysis run, plus two model-backed actions:
writing recommendations and building a demo website.

```bash
python3 scripts/export_web_report.py --product-family auto   # report.json, trends.json, operations.json
python3 scripts/serve_web.py --port 8000                      # backend: recommendations, site, research, downloads, captures
cd web && npm ci && npm run dev                               # http://localhost:5173 (Vite proxies /api and /site)
npm run build                                                 # type-check + static bundle in web/dist/
```

`serve_web.py` also serves `web/dist` at `/`, so the built UI and the API share one
port (Docker: 8006).

## Data it reads

| File | Written by | Used by |
| --- | --- | --- |
| `public/report.json` | `export_web_report.py` | Analysis, Reputation, Recommendations |
| `public/operations.json` | same run | Home, Bank profiles, Data, Rubric, Collection |
| `public/trends.json` | same run, if `search_interest/export/` exists | Trends |

The Analysis, Trends and Reputation tabs work from a static build alone. Research,
downloads, page captures, recommendations and the site need the backend.

## Tabs

- **Home**: what was collected, per-bank status, downloads of `outputs/`.
- **Analysis**: scope banner, focus verdict, peer gaps, group separation,
  similarity, personas, AI Score, cross-sell, regional interest, deck-claim
  verdicts, limitations.
- **Bank profiles**: one bank at a time (palette, tone, layout, personas, AI Score);
  the capture comes from `/api/capture/{bank}`.
- **Data**: dataset explorer and the read-only feature dictionary. Filters choose
  stored rows; nothing is recomputed in the browser.
- **Rubric**: the finished judged sheet and the scoring guide, read-only. There is
  one rater, so no agreement figure is shown.
- **Collection**: status and pipeline commands. No run button: collection is slow
  and the robots.txt gate stays server-side.
- **Research**: Semantic Scholar search through the backend.
- **Trends**: weekly search interest per brand, share of brand search, and the
  brands worth studying. Search interest is context, never an outcome; it chooses
  who to look at, the dataset says what they do.
- **Reputation**: news themes per bank (never sentiment), from `NEWSAPI_KEY` and/or
  `NEWSAPI_AI_KEY`, merged and de-duplicated, queried in English, French and Dutch.
  Unconfigured, it shows an empty state.
- **Recommendations**: the one place the model opines, argued from this run's
  numbers, each next to its features. Ticked recommendations feed the site builder;
  invented feature ids are dropped.

## Site generation

The **Generate ING website** button builds ten pages in ING's house style from the
ticked recommendations, one model call per page, in the chosen language. It runs in
the background and the UI polls; a failed page is rendered from a fallback and
marked `fallback` in the manifest. Output: `outputs/generated_site/`, served at
`/site/` (not versioned, regenerated on demand, needs an LLM key). Rates, fees and
product terms are placeholders such as `[TAUX]`. **Explain each section** adds a
box and an (i) balloon per section naming the recommendations it implements; a bar
above the site turns it off.

## Principles

- Leads with the answer and carries its scope (family, banks, capture date,
  language, banks left out) above the first number.
- Judgement is marked: `judged` (a person), `model-judged` (a model, unchecked);
  everything unmarked was counted or measured.
- Generated copy is never shown alone: the synthetic label, scorecard and the
  "says nothing about performance" line travel with it.
- No pipeline control, scoring or dataset editing. The UI does no arithmetic;
  `src/types.ts` mirrors `export_web_report.py` (`build_report`, `build_operations`)
  and the shapes of `recommendations.py` and `site_generator.py`. Change one, change
  the other.

## Tests and audit

`tests/test_recommendations_and_site.py` monkeypatches the model entry points, so
the suite stays offline. `scripts/browser_audit.py` is a manual harness: with both
servers running it drives the UI with Playwright, generates sites and audits all
ten pages (single `h1`, CTA, nav, contrast, images, overflow at 1440 and 375 px,
console errors). It makes real model calls; results go to `outputs/browser_audit/`.
