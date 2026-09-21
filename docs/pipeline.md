# The pipeline: collect → score → analyse → export

Split out of `README.md` (steve 21/09) because the README had grown into a
runbook plus a design document plus a UI guide. This file is the runbook: what
to type, in what order, and what lands where. The *why* lives in
[`design.md`](design.md), the UI in [`../web/README.md`](../web/README.md), and
the decision log in [`decisions.md`](decisions.md).

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in DEEPSEEK_API_KEY - .env is gitignored

# wiring only, no real data
python3 scripts/make_fixture.py                # synthetic dataset, in memory/only
python3 scripts/run_analysis.py                # the full chain: profiles, positioning, charts
python3 scripts/run_generation.py --dry-run    # step 5 without calling a model
python3 scripts/check_schema_freeze.py         # enforce the Day 2 freeze rule
```

## Real data, in order

```bash
# 1. collect + extract + validate (compliance -> scrape -> extract -> quality gate)
python3 scripts/run_collection.py --config scripts/collection_targets.yaml --method headless

# 2. if a model-assisted extraction timed out mid-collection, refill those fields
#    from the HTML already on disk (no re-fetch, but it is a fresh LLM call)
python3 scripts/reextract_model_fields.py --dataset data/processed/campaigns.csv

# 3. rubric: sheets out, model as a third rater, merge
python3 scripts/rubric_sheet.py emit                        # one sheet per human rater
python3 scripts/rubric_sheet.py model                       # pinned model -> its OWN sheet
python3 scripts/rubric_sheet.py merge --sheets data/rubric/*_scores.csv
python3 scripts/rubric_sheet.py agreement --sheets data/rubric/*_scores.csv
python3 scripts/rubric_sheet.py report --sheets data/rubric/*_scores.csv   # docs/day5_scoring_disagreement.md

# 4. analyse, document, export for the business UI
python3 scripts/run_analysis.py --dataset data/processed/campaigns_scored.csv \
        --product-family auto --no-strict
python3 scripts/build_feature_docs.py      # regenerate docs/feature_dictionary.md
python3 scripts/export_web_report.py       # web/public/report.json + trends.json
python3 -m pytest tests/ -q
```

Outputs land in `outputs/`: four charts, `charts.md` explaining what each one
measures and what it cannot support, the profile cards as markdown and JSON, a
CSV per analysis step, `limitations.md`, `reputation.json` and (optionally)
`geo_trends.json`.

`charts.md` is generated, not written by hand. The "what this run shows"
paragraphs are built from the same objects the charts are drawn from, so the
prose cannot drift away from the picture.

## Where data lives

| Path | Tracked? | What |
| --- | --- | --- |
| `data/raw/<bank>/` | no (gitignored) | HTML snapshots + screenshots, one pair per page |
| `data/processed/campaigns.csv` | no | the collected dataset (auto features + model-assisted) |
| `data/processed/campaigns_scored.csv` | no | the same rows with rubric scores merged in — what analysis reads |
| `data/rubric/*_scores.csv` | yes | the human and model scoring sheets |
| `outputs/` | yes (team decision, see below) | charts, tables, profiles, limitations, reputation |
| `web/public/report.json` | yes | the one JSON snapshot the business UI reads |

`scripts/reextract_model_fields.py` is not a no-op: it refreshes **every**
model-assisted field on every row it touches, and the model is not deterministic,
so re-running it changes personas/cross-sell/imagery values. Only run it to fix a
specific gap (a timed-out extraction), and prefer note-taking over repeated runs.
`scripts/fix_rate_fields.py` is the deterministic alternative for the two rate
columns specifically — no LLM call.

## Two things a range check cannot catch

**A capture can be honestly measured and still be the wrong page.** The first
live collection returned ING as an unrendered JavaScript shell (16 words — the
`<title>`, twice) and BNP Paribas Fortis as a maintenance notice. Every numeric
feature on those rows was in range. `collection/quality.py` judges whether a
capture looks like a campaign page at all, and the verdict travels with the row
in `capture_quality`. Analysis excludes `unusable` rows and says which.

**13 core features are scored by a person**, so a collected dataset can never
pass strict validation on its own. `scripts/rubric_sheet.py` emits one sheet per
rater with the screenshot path, merges completed sheets back, and reports
inter-rater agreement — which is what NFR-05 actually asks for.

## When a site will not serve the pipeline

Some pages cannot be fetched by us at all — BNP Paribas Fortis' edge declines
automated traffic outright (HTTP 503, diagnosed in `scripts/run_collection.py`,
and not worked around: getting past it would need IP rotation, which LC-04
forbids), and Revolut returns HTTP 403.

`scripts/import_captures.py` imports pages a person saved from a normal browser:

```bash
python3 scripts/import_captures.py --dir <folder> --merge-with data/processed/campaigns.csv
```

A human opening a public page and saving it is ordinary use of a public website,
not automation getting past a control. The importer still **re-checks robots.txt**
for every recovered URL rather than trusting that someone checked earlier, and it
recovers the URL from the browser's own "saved from url" comment so there is no
hand-written manifest to drift.

A manual capture carries `collection_method = manual_capture`, **no
`http_status`** (we made no request — writing 200 would claim a response nobody
received) and **no `page_height_px`** (a browser save is a *viewport* screenshot,
not a full-page one, so the height genuinely cannot be measured). A live capture
that worked is always preferred over a manual one for the same page.

Chrome writes shadow DOM out as `<template shadowrootmode>`, which BeautifulSoup
does not walk into — one saved ING page parsed as 14 words while carrying 4,858
inside templates. `extract()` flattens those, so a manual capture and a live
capture are measured the same way.

## Limitations are generated, not remembered

`outputs/limitations.md` (D-09) is written from the dataset on every run. If two
captures failed it names them and why; if the focus bank is missing it says which
questions that makes unanswerable; if the rubric is unscored it says so. A
limitation nobody can quietly drop on Day 9 is worth more than a well-written
paragraph.

## Search interest and reputation, when their inputs are missing

Both optional signals degrade instead of failing:

- **Trends** (`web/public/trends.json`) needs Dan's `kbc-ing-benchmark/export/`.
  Absent, the exporter writes no `trends.json` and the tab shows an empty state.
- **Reputation** (`outputs/reputation.json`, and the `reputation` block in
  `report.json`) needs `NEWSAPI_KEY` and/or `NEWSAPI_AI_KEY`. With neither set,
  `available: false` and the tab says so.

`available: true` on the reputation block means *a key is configured*, not that
articles were returned — a working key with a thin 90-day window yields an empty
bank snapshot rather than a false "not configured".

## Housekeeping

`outputs/` is committed to git even though it is regenerated on every run (and
`.gitignore` lists it; the files stay tracked, which is why they keep showing up
as modified). That is a standing team decision to revisit: committing regenerated
charts means every analysis run produces a large binary diff.

`data/raw/` and `data/processed/` are gitignored, so a fresh clone has no
captures and analysis cannot run until collection does.
