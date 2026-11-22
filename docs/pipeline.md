# Pipeline runbook: collect, score, analyse, export

What to type, in what order, and where it lands. Design:
[ARCHITECTURE.md](ARCHITECTURE.md). Decisions: [decisions.md](decisions.md).

## Wiring check (no real data)

```bash
pip install -r requirements.txt
cp .env.example .env                           # fill DEEPSEEK_API_KEY; .env is gitignored
python3 scripts/make_fixture.py                # synthetic dataset, never evidence
python3 scripts/run_analysis.py                # profiles, positioning, charts
python3 scripts/run_generation.py --dry-run    # generation without calling a model
python3 scripts/check_schema_freeze.py         # freeze rule
```

## Real data, in order

```bash
# 1. collect, extract, validate (compliance, scrape, extract, quality gate)
python3 scripts/run_collection.py --config scripts/collection_targets.yaml --method headless

# 2. only if a model-assisted extraction timed out: refill from the HTML on disk
python3 scripts/reextract_model_fields.py --dataset data/processed/campaigns.csv

# 3. rubric: blank sheet out, scored by hand, merged back
python3 scripts/rubric_sheet.py emit
python3 scripts/rubric_sheet.py merge --sheet data/rubric/siegried_scores.csv

# 4. analyse, document, export
python3 scripts/run_analysis.py --dataset data/processed/campaigns_scored.csv \
        --product-family auto --no-strict
python3 scripts/build_feature_docs.py          # docs/feature_dictionary.md
python3 scripts/export_web_report.py           # web/public/report.json, operations.json, trends.json
python3 scripts/serve_web.py                   # optional backend (recommendations, site, research)
python3 -m pytest tests/ -q
python3 scripts/check_data_quality.py          # CI gate
```

Re-merge after every change to `campaigns.csv` (rate fix, CTA fix, new captures,
re-extraction): `rubric_sheet.py merge` joins on `page_id` and produces
`campaigns_scored.csv`, which analysis and the exporter read. Skipping it leaves
them on stale data. `tests/test_dataset_sync.py` checks this. `page_id` is
`{bank}_{family}_{language}_{index:02d}`: a re-collection that adds or removes a
page renumbers the ones after it, and `merge_scores()` silently drops scores whose
`page_id` no longer exists (the merge prints unmatched rows and unscored pages).

## Outputs

| Path | What |
| --- | --- |
| `outputs/` | charts, `charts.md`, profiles (md/json), one CSV per analysis step, `limitations.md`, `reputation.json`, optional `geo_trends.json` |
| `web/public/report.json` | business snapshot read by the Analysis tabs |
| `web/public/operations.json` | operator snapshot (dictionary, dataset, collection, rubric) |
| `web/public/trends.json` | Trends series, written when `search_interest/export/` is present |
| `data/processed/campaigns*.csv` | collected and scored datasets (tracked) |
| `data/raw/` | page captures: not versioned, see README |

`outputs/*.md` are generated; do not edit them by hand.

## Re-deriving columns

`reextract_model_fields.py` refreshes every model-assisted field on each row and
the model is not deterministic, so run it only to fix a gap. The deterministic
scripts re-read `snapshot_html_path` from `data/raw/` and touch one detector's
columns, with no LLM call and no fetch:

- `fix_rate_fields.py`: `rate_shown`, `rate_value_pct`.
- `fix_cta_count.py`: `cta_count`, `cta_above_fold` (the feature is withdrawn from
  comparison but still stored).
- `rederive_urgency_markers.py`, `rederive_cross_sold_products.py`,
  `fix_background_luminance.py`.

They need the captures in `data/raw/`, which are not versioned: re-run collection
first on a fresh clone.

## Hosts that will not serve the pipeline

Per target in `scripts/collection_targets.yaml`; robots.txt is still checked first.

- `method: headful`: a real visible Chrome (BNP Paribas Fortis refuses every headless client).
- `wait_until: domcontentloaded` and `timeout_ms`: pages that never go idle (Keytrade).
- Manual saves: `python3 scripts/import_captures.py --dir <folder> --merge-with data/processed/campaigns.csv`.
  Robots.txt is re-checked per recovered URL; the row has `collection_method = manual_capture`
  and no `http_status` or `page_height_px`.

## What a range check cannot catch

- **Wrong page.** A capture can be an unrendered JS shell or a maintenance notice
  with every number in range. `collection/quality.py` writes a verdict to
  `capture_quality`; analysis excludes `unusable` rows and says which.
- **Overlay on the page.** Cookie modals distorted screenshot-derived features
  (`background_luminance`, `hero_image_area_ratio`, `accent_colour_count`,
  `brand_colour_share`, `above_fold_element_count`) on some pages; text-derived and
  judged features are unaffected.
- **Judged features.** 13 features are scored by one person, so a collected dataset
  never passes strict validation alone (hence `--no-strict` before the merge).

## Optional signals

Both degrade instead of failing. Trends needs `search_interest/export/`, otherwise
the tab shows an empty state. Reputation needs `NEWSAPI_KEY` and/or
`NEWSAPI_AI_KEY`; `available: true` means a key is configured, `headline_count: 0`
means every request was answered and nothing matched, `null` means the fetch failed
(reason in `failures`). A partial outage is listed in `fetch_errors` and not cached.
