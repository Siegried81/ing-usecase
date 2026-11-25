# Decision log

One entry per decision that still holds: date, what, why. Oldest first. The
history of each change is in git.

## 2026-09-15: Dataset schema and file format

One CSV, one row per campaign page, provenance columns first; list features
(`palette_hex`, `accent_locations`, `persuasion_levers`) are pipe-separated.
`config/feature_dictionary.yaml` is frozen: additions pass, renames, removals,
type changes, narrowed ranges, tier demotions and tighter nullability fail.
Two guards: `tests/test_schema.py` (byte equality with the frozen copy) and
`scripts/check_schema_freeze.py` (the rule itself, which names the feature).

## 2026-09-15: One pinned model for model-assisted features

About a quarter of the dictionary is model-assisted, and a silent provider
fallback could label two banks with two judges. DeepSeek `deepseek-flash`
(`llm_extractor.DEEPSEEK_DEFAULT_MODEL`, `DEEPSEEK_MODEL` to override),
`temperature=0`, prompts in the repository. The request names thinking mode
(`"thinking": {"type": "enabled"}`) so a change of DeepSeek's default cannot
relabel new rows. Each row records its model in `extraction_model`, and
`schema.validate()` warns on a mixed dataset. A model change means re-running all
banks. Open: the 49 DeepSeek rows were labelled before the explicit parameter;
re-run a sample and compare before mixing old and new rows.

## 2026-09-19: Personas, AI Score, cross-sell, subscription framing

Additive features `target_personas` (8 values), `cross_sold_products` and
`subscription_style_framing`, from the same structured call (no new LLM call).
The AI Score (`ai_score.py`) has six axes, each a documented mean of existing
features, `None` and never a fabricated 0 when data is missing. Nothing in it is
model-scored. `innovation` is withdrawn (both inputs fail).

## 2026-09-20: `rate_value_pct` needs a rate keyword

The number must have a rate keyword within 40 characters ("100% en ligne" is not a
rate). Rate keywords match whole words. Rates move over time, so the feature is
valid for one capture date and is excluded when pages span several.

## 2026-09-20: Regional search interest

`geo_trends.py` reads Google Trends by region (pytrends, `requirements-geo.txt`,
outside CI). It shows where people look for a brand, not what a page says.

## 2026-09-21: Scope is 14 banks and 6 product families

New banks enter through the freeze rule's addition path (`bank` enum,
`BANK_CATEGORY`, `BRAND_COLOURS`, colours taken from each bank's own assets,
because a guessed hex makes `brand_colour_share` confidently wrong). Product
pages come from each bank's navigation and are quality-gated before collection.
`other` was a mislabelled Belfius pension page and became `pension`.
`run_collection.py` overwrites its output from the targets file: trimming
`collection_targets.yaml` silently narrows the dataset. A comparison is only valid
within one `product_family` (DR-04).

## 2026-09-21: Collection stays inside robots.txt

One bank returned HTTP 503 to every headless client. `method: headful` per target
opens a visible browser for that host only, and robots.txt is still checked before
every fetch, on every redirect hop (since 2026-11-22). `wait_until` and
`timeout_ms` per target handle sites that never reach `networkidle`. Manual saves
go through `scripts/import_captures.py`. No evasion beyond a normal browser (LC-04).

## 2026-09-21: Anomaly detection removed from the Trends tab

The z-score detector answered a product-level question on brand-level series:
32% of flagged weeks came from two brands peaking at 2/100. The tab reports share
of search, 52-week trajectory and rank stability instead. The campaign matching
built on it (`search_interest/campaigns/`) was removed on 2026-11-22.

## 2026-09-21: React is the main UI, Streamlit stays as the key-free dashboard

Two dashboards on the same files let figures go stale. Read-only views (Home,
Profiles, Data, Rubric, Collection, Research) are in `web/`, fed by
`scripts/export_web_report.py`. `streamlit_app.py` needs no key and is the Docker
default. New views go to React first.

## 2026-09-21: Recommendations and generated site

Recommendations are written from `report.json` only, and Trends is marked context,
never a cause. The model never writes from search interest (2026-09-22). The site
is built from the chosen recommendations, in parallel, by `scripts/serve_web.py`;
an "explain" layer tags each section with the recommendations it implements.
Regenerating the site needs an LLM key.

## 2026-09-21: External signals: news

Reputation reads newsapi.org (`NEWSAPI_KEY`) and newsapi.ai (`NEWSAPI_AI_KEY`) in
English, French and Dutch. A failed fetch is `null`, never `headline_count: 0`,
and a partial outage is not cached. Since 2026-11-22 only titles that were
fetched count, and a headline counts once, under the first theme in `THEMES`.

## 2026-09-22: One judged rubric sheet

The rubric is scored by one person, so the agreement and kappa tooling was removed
(`_consensus()` became `_single_value()`). Every judged column comes from that
sheet and a scored zero is explicit. No inter-rater claim is made anywhere.

## 2026-09-23: `background_luminance` is measured on the first screen

It averaged the whole page strip, so on a long page it reported how much white
body text there is. It now reads the first viewport (`first_screen_px`), for live
captures and manual imports alike. The earlier "ING is darker than its peers"
reading was wrong: ING is brighter (0.55 against 0.34). Colour features come from
one light-scheme rendering; a visitor in dark mode sees something else.

## 2026-09-23: `urgency_marker_count` counts dated deadlines

A deadline written as a date ("avant le 11/10/2026") carries no keyword and scored
0, while "offre temporaire" scored several. Dates count now, and deadline and rate
keywords match whole words. All 14 banks were re-measured from the stored
snapshots; only ING's pages moved (0.33 to 4.00).

## 2026-09-23: `cta_count` is withdrawn as a finding about ING

ING scored 1.0 against a peer mean of 6.18. The stored capture holds the page's
cards, so the gap came from the measure, and no counting rule held across 14 banks.
`analysis.CAPTURE_INVALID_FEATURES` excludes it inside the analysis (editing
`report.json` by hand is undone by the next run). It is still collected, never
compared.

## 2026-09-24: Measures that describe our method are withdrawn

`has_animation` and `animated_asset_count` read "this stylesheet declares an
animation", not "this page moves". `has_comparison_table` reads "uses an HTML
table": N26 and Revolut build the same comparison in CSS. Both are withdrawn from
comparisons. `cross_sold_products` collapses insurance, cards and perks into
`other`, so ING (8 to 14 add-ons) scores below bunq (3); widening the frozen
taxonomy is a team decision, and `limitations.py` says so.

## 2026-09-25: A measure that cannot rank is not a refutation

`word_count_band` reads `long` for all 14 banks. `check_deck_claims()` returns
"not testable" when the ranking column has one distinct value. "Not applicable" is
masked out of the AI Score trust axis instead of counted as a no. A slide row that
rests on one data point is dropped.

## 2026-10-05: The `none` persuasion lever is removed

A `none` sentinel, never valid in the dictionary, stood in for "no lever". An empty
list says it. Persuasion figures were re-measured without it.

## 2026-11-05: Name and gate the data-quality dimensions

`comparator/dq.py` scores completeness, validity, uniqueness, consistency and
timeliness; `scripts/check_data_quality.py` gates CI on the first three, the others
warn. Accuracy is not scored: it needs a trusted reference. Thresholds live in
`dq.py`. Output: `outputs/dq_scorecard.csv`, `outputs/dq_report.md`, the Data
quality tab. The `schema.validate()` rules are reused, so "valid" has one definition.

## 2026-11-08: A model-extracted empty list is a zero

A blank CSV cell meant both "none" and "not judged". For model-extracted lists
blank is `[]` (the call returns every field or raises); for rubric lists blank
stays "not judged". Cross-sell scores exist again for Argenta, Beobank, CBC and VDK.

## 2026-11-16: Tied effect sizes are ranked by feature name

`category_comparison` sorted ties unstably, so the published top 10 depended on
sort internals. Ties now break alphabetically. The cut still falls inside a tie.

## 2026-11-20: Simplicity axis on a tie, search_interest views from the config

`ai_score.score_simplicity` averages tied readability modes instead of taking the
alphabetical first (Beobank over all families: 1.25). The search_interest app lists
every bank of `BANK_DISPLAY_LABELS` (7 of 8 views were empty) and its export counts
banks and sheets from the config. Manual imports and `rederive_*` scripts read the
snapshot like a fresh capture.

## 2026-11-22: Scraper and render fixes from the line-by-line review

Re-measured offline from the 51 stored snapshots into `data/processed/`: a word
needs a letter or digit (40 pages lose up to 0.73% of words; readability and
sentence length follow); nested disclaimer blocks count once; `section_count` is 0
and not missing on a page without `<section>` (ING mean 1.0 to 0.57); capture-quality
error phrases count only under 120 words; an empty page has no readability score.
`render.py` counts only the visible part of a hero image and skips `<picture>`; the
stored image-area ratios keep the old rule until the next collection. Every redirect
hop is checked against robots.txt.

## 2026-11-22: Generation and search_interest follow-ups

`site_generator.generate_page` uses one fixed prompt with a bounded retry (the
pattern of `llm_extractor.py`), then the deterministic page. `term_resolver.py`
lost its product phase (any call raised `KeyError`) and no longer fails when five
or more topics match. `store_long_format` drops the unfinished last Trends week.
`PRODUCT_NOTES`, `PRODUCT_LABEL_BASE` and `BANK_SEGMENTS` are removed (nothing read
them), and with `search_interest/campaigns/` the campaign tables of `schema.sql`.

## 2026-11-22: Captures and demo site not versioned, ruff widened, compose without bind mounts

`data/raw/` (210 captures, third-party material), `outputs/generated_site/` and
`outputs/generated/*.html` are git-ignored; derived JSON and CSV stay tracked.
Re-deriving features from raw pages needs a re-capture, and the UI says so when
the demo site is absent. History is not rewritten: a `git filter-repo` pass is a
separate decision. Ruff runs on the whole repository with `ruff.toml` (one config
for local and CI). The main compose file has no bind mounts; `docker/docker-compose.dev.yml`
adds them, and the health dashboard starts only with `--profile monitoring`.
Ports are 8506, 8006 and 8606.

## 2026-11-25: Hero images decoded only as web raster formats

`visual_features.extract_colours` opens a fetched image with
`formats=WEB_IMAGE_FORMATS` (JPEG, PNG, WEBP, GIF, AVIF). Pillow reads EPS by
calling Ghostscript when one is installed, and Upload2Shell (CVE-2026-125396)
makes a crafted file a code-execution path. No machine or image here has
Ghostscript today; the allowlist keeps it that way if one ever does. A hero image
in any other format now gets null colours, as an undecodable one already did.
Screenshot measurements are not affected: they open our own PNG captures.
Revisit if a bank serves its hero image in a format outside the list.
