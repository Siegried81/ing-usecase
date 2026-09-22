# Business web UI

The findings surface for one analysis run, for the business audience (D-06),
plus two model-backed actions: writing recommendations and building a website.

```bash
python3 scripts/export_web_report.py --product-family auto   # writes report.json, trends.json + operations.json

python3 scripts/serve_web.py --port 8000                      # recommendations, site, research, downloads, captures
cd web && npm install && npm run dev                          # http://localhost:5173

npm run build                                                 # static bundle in web/dist/
```

`report.json` is the business snapshot; `operations.json` is the operator
surface (feature dictionary, dataset explorer, collection status, rubric
sheets). The exporter writes both in one run, from the same library calls, so
the scope banner and the collection status cannot disagree. The Analysis,
Trends, Reputation and Recommendations tabs work from a static build of
`report.json` alone; the operator tabs need `operations.json`, and Research,
downloads and page captures additionally need the backend.

Vite proxies `/api` and `/site` to the backend, so the UI can generate
recommendations, open the generated website, search papers and download the
deliverables without a second origin. `npm run build` still produces a folder
that opens anywhere; the Analysis tab works from that build alone.

## The tabs

**Home** is what was collected and which banks are in the comparison: four
metrics, the validation verdict, per-bank collection status, and a download for
every deliverable in `outputs/`. The file list is the one live call here,
because those files are not part of the bundle.

**Analysis** is the read-only snapshot described below. It reads a single
`report.json` and talks to nothing. A snapshot is the honest shape for a finding:
it is true for one dataset, at one capture date, under one scope.

**Bank profiles** expands the profile cards: one bank at a time, with its
palette, the tone/imagery/layout/value-proposition/marketing fields, its
z-score signature, its personas and its six-axis AI Score. The page capture is
served by the backend at `/api/capture/{bank}` and degrades to a note when the
backend is not running.

**Data** is the dataset explorer and the feature dictionary. The filters only
choose which stored rows to show, and the CSV export serialises exactly those
rows — no value is recomputed in the browser. The dictionary is read-only
forever: it is the frozen contract (P-04), and editing it from a form would undo
the freeze rule.

**Rubric** is the read-only view of `data/rubric/*_scores.csv` after the fact:
every sheet, raw per-feature agreement, chance-corrected Cohen's kappa, and the
scoring guide generated from the dictionary. It deliberately never merges the
sheets into a single score and never marks agreement as settled — the
disagreement is the finding until the wording is tightened. A live scoring
screen must not exist in this shape: it must not show another rater's numbers,
or the agreement becomes an artefact of who looked at what.

**Collection** is the collection status and the pipeline commands. Read-only on
purpose: collection is slow and needs a job model, and the robots.txt gate must
stay server-side and non-overridable, so there is no "run collection" button.

**Research** searches Semantic Scholar for papers to source a claim in the
narrative. It is the one live external call in the operator surface, and it is
deliberately a search box and nothing more — no per-bank metric is invented to
justify it.

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
crisis, results, ...), classified by one structured model call - counts only,
deliberately never sentiment (see `comparator/reputation.py`'s docstring for
why). Two differently named companies are supported at once: `NEWSAPI_KEY`
(newsapi.org) and `NEWSAPI_AI_KEY` (newsapi.ai / Event Registry). Headlines from
every configured key are **merged and de-duplicated**, and each is queried in
**English, French and Dutch** - Belgian bank news is mostly not in English
("Belfius" returned 0 English title matches against 22 French and 11 Dutch).
Event Registry is sorted by relevance inside a 90-day window and newsapi.org is
restricted to title/description, because its body search answered a query for
"bank" with football and politics.

With neither key set it renders an honest "not configured" state, same pattern as
Trends when Dan's export is missing. Note that `available: true` means *a key is
configured*, not that articles were returned: a working key with a thin 90-day
window yields an empty bank snapshot rather than claiming the tab is unconfigured.

**Recommendations** is the one place a model is allowed to opine. It asks the
pinned model to turn this run's own numbers into advice, shows each
recommendation next to the features it was argued from, and lets a reader **tick
the ones worth implementing**. Only the ticked subset is passed to the site
builder. A feature id the model invented is dropped before the list is shown, so
nothing links to evidence that does not exist.

**From search-interest context** is the one section on this tab the model does
not write. The Trends tab picks the competitor brands worth studying - the
traditional bank with the largest share of brand search, the one whose share
rose fastest, and the measurable challenger - and `comparator/benchmarks.py`
reports what each of their pages measurably does differently from ING's, then
what all of them share and where they part company. Every figure is a z-score
from the same feature set as the analysis above.

The two halves are joined on the bank name and nothing else. Search interest
chooses WHO to look at; the dataset says WHAT they do. Saying they are searched
for BECAUSE their pages do this is the claim the project has no data for, so the
caveat travels in the payload rather than sitting in a footnote.

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

**Explain each section** is the second checkbox on the build row. With it on, the
model also tags each section with the recommendations it implements and a
one-sentence rationale in the page language, and the renderer puts a glowing box
around every section that acts on a recommendation - drawn on the content column,
not the full-bleed band. A round **(i)** button sits at the end of that section;
clicking it opens a balloon *above* it naming the recommendation ids and titles
with the rationale. While a balloon is open that section's glow switches from a
quiet ING-orange outline to a **slow yellow flicker** (3.2s), yellow on purpose
so the "explanation open" state cannot be mistaken for the brand treatment.

A slim bar above the site ("Show recommendation explanations") turns the whole
layer off so the site can be shown as a normal site, and the choice is remembered
across the ten pages via `localStorage`. Pages that no recommendation targets are
told to borrow the site-wide advice that genuinely applies, and a page that comes
back with no cited section at all is retried - every page gets at least one box.

Explanation mode is also what forced the copy rules into the page prompt: the
first explained run produced meta copy ("Add alt text to every image", "When we
review this page"), so the prompt now states that all copy is customer product
copy, bans references to the page, the analysis or the recommendations, leaves
structural recommendations (alt text, CTA count, contrast) to the template, and
confines any mention of a recommendation to the rationale.

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
re-runs collection or analysis. The operator tabs are read-only views over the
same files the CLI uses; the rubric page shows finished sheets, it does not score
them, and there is no endpoint that writes a rubric cell. Run orchestration and a
live scoring screen remain a separate question (see `docs/web_ui_proposal.md`).

## Keeping it honest

`src/types.ts` mirrors `scripts/export_web_report.py` — both `build_report` and
`build_operations`; the recommendation and site shapes mirror
`src/comparator/recommendations.py` and `src/comparator/site_generator.py`.
Change one, change the other. Every figure comes from the library through the
exporter — the UI does no arithmetic of its own, so there is no second
definition of any number on screen.

The backend (`scripts/serve_web.py`) only orchestrates the model calls, serves
the generated site, searches Semantic Scholar, and streams the deliverables and
page captures. It re-derives nothing: recommendations read `report.json`, the
site reads the recommendations, downloads read `outputs/` verbatim. One
direction only.

## Tested without a model

`tests/test_recommendations_and_site.py` monkeypatches the model entry points, so
the suite still makes no network calls. It covers the local logic: dropping an
invented feature id, retrying a bad response, selecting a subset in order, and
rendering ten pages with a marked fallback when a page fails.

## Browser audit

`scripts/browser_audit.py` drives the real UI with Playwright — tick
recommendations down and up, pick a language, press Generate, open the result
through the actual Browse link — then audits all ten pages in the browser:
recommendation expression per selected recommendation (by feature, multilingual
cues), a single `h1`, an above-fold CTA, the full ten-link nav, rendered-text
WCAG contrast, broken or alt-less images, horizontal overflow at 1440px and
375px, console errors and failed requests, and single-language copy.

It is a harness rather than a unit test: both servers must be running and it
makes real model calls. Ten iterations (1–8 recommendations selected, alternating
"start from all" and "start from none", across fr/nl/en) is what found the empty
hero `alt=""`, the fallback page's English summary under Dutch chrome, and the
selected recommendation that could be silently absent — which `generate_page`'s
coverage check now retries. Results land in `outputs/browser_audit/`
(`summary.md`, `results.json`, per-iteration screenshots).
