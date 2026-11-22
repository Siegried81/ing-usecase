# Decision log

One entry per decision: context, choice, consequence. The history of each change
is in git.

## D5 - Dataset schema and file format

**Context.** Analysis code, the rubric and the UI all depend on one column set.
**Choice.** One CSV, one row per campaign page, provenance columns first;
list-valued features (`palette_hex`, `accent_locations`, `persuasion_levers`) are
pipe-separated. The dictionary (`config/feature_dictionary.yaml`) is frozen:
additions pass; renames, removals, type changes, narrowed ranges or categories,
tier demotions and tightened nullability fail.
**Consequence.** Two guards: `tests/test_schema.py` (byte equality with
`config/feature_dictionary.frozen.yaml`, catches accidental edits) and
`scripts/check_schema_freeze.py` (the rule itself, names the feature). Byte
equality alone is not the rule: it rejects an allowed addition and accepts a
rename once both files are updated.

## D6 - One pinned model for model-assisted features and generation

**Context.** About a quarter of the dictionary is model-assisted, and a silent
provider fallback could label two banks with two different judges.
**Choice.** DeepSeek `deepseek-flash` (`llm_extractor.DEEPSEEK_DEFAULT_MODEL`,
overridable with `DEEPSEEK_MODEL`) is the pinned model, `temperature=0`, prompts
in the repository. The request names thinking mode explicitly
(`"thinking": {"type": "enabled"}`, DeepSeek only), so a change of DeepSeek's
default cannot relabel new rows silently.
**Consequence.** Other providers stay as a fallback, but each row records its model
in `extraction_model` and `schema.validate()` warns on a mixed dataset. A model
change means re-running all banks, not mixing. In thinking mode DeepSeek ignores
`temperature`.
**Open (user decision).** The 49 rows labelled before the explicit parameter may
have been labelled without thinking. Re-run a sample of banks and compare the
model-assisted features before mixing old and new rows.

## D7 - Name and gate the data-quality dimensions

**Context.** Validation signals were a flat error/warning list.
**Choice.** `comparator/dq.py` scores completeness, validity, uniqueness,
consistency and timeliness; `scripts/check_data_quality.py` gates CI on the first
three (the others warn). Accuracy is not scored: it needs a trusted reference.
Thresholds live in `dq.py`.
**Consequence.** Output in `outputs/dq_scorecard.csv`, `outputs/dq_report.md` and
the Data quality tab. The `schema.validate()` rules are reused, so "valid" has one
definition.

## D8 - Scope: 14 banks, 6 product families, additions only

**Context.** The set grew from a few banks to the Belgian retail market.
**Choice.** 14 banks and 6 families (`other` was a mislabelled Belfius pension page
and became `pension`). New banks enter through the freeze rule's addition path
(`bank` enum, `BANK_CATEGORY`, `BRAND_COLOURS`, colours taken from each bank's own
assets). Product pages are discovered from each bank's navigation and
quality-gated before collection; non-product pages are dropped.
**Consequence.** `run_collection.py` overwrites its output from the targets file
as it stands: trimming `collection_targets.yaml` silently narrows the dataset.

## D9 - Collection stays inside robots.txt

**Context.** One bank returned HTTP 503 to every headless client.
**Choice.** `method: headful` per target launches a visible browser for that host
only; `robots.txt` is still checked before every fetch. Per-target `wait_until` and
`timeout_ms` handle sites that never reach `networkidle`.
**Consequence.** No evasion beyond using a normal browser. Manual saves go through
`scripts/import_captures.py`.

## D10 - Single judged rubric sheet

**Context.** An inter-rater layer existed, but the rubric is scored by one person.
**Choice.** Remove the agreement/kappa tooling; `_consensus()` became
`_single_value()`. Every judged column comes from that one sheet and a scored zero
is explicit.
**Consequence.** No inter-rater claim is made anywhere.

## D11 - Findings are hypotheses until CTR data arrives

**Context.** No campaign performance data exists here; ING is chasing CTR figures.
**Choice.** The guardrail stands: no claim of effect. Reputation and Trends are
context (attention, not performance); the model never writes from search interest,
and the Trends anomaly detector was removed because it answered a product-level
question on brand-level series.
**Consequence.** If CTR arrives, it is a new input, not a restructuring.

## D12 - A measure that cannot rank is not a refutation

**Context.** `word_count_band` reads `long` for all 14 banks.
**Choice.** `check_deck_claims()` returns **not testable** when the ranking column
has a single distinct value. "Not applicable" is masked out of the AI Score trust
axis instead of counted as a no. A slide row resting on one data point is dropped.
**Consequence.** Three kickoff observations moved from "not supported" to "not testable".

## D13 - `cta_count` is withdrawn as a finding about ING

**Context.** ING scored 1.0 against a peer mean of 6.18, the largest negative gap.
**Choice.** The detector now counts distinct calls to action (skips `<nav>`,
`<footer>` and landmarks). The stored capture was shown to hold the page's cards,
so the gap came from the measure. `analysis.CAPTURE_INVALID_FEATURES` excludes the
feature inside the analysis; hand-editing `report.json` is undone by the next run.
**Consequence.** The run prints the withdrawal in its feature accounting. The
feature is still collected but never compared.

## D14 - Scraper measures fixed at the source

**Context.** Some features measured our method, not the pages.
**Choice.** `rate_value_pct` requires a rate keyword within 40 characters of the
number ("100% en ligne" is not a rate). `urgency_marker_count` also counts dated
deadlines. `cross_sold_products` gained `insurance`, `credit_card`, `partner_perk`
(pure addition) and that one column was re-derived from stored HTML with
`scripts/rederive_cross_sold_products.py`.
**Consequence.** The `fix_*`, `rederive_*` and `reextract_*` scripts read
`data/raw/` snapshots, which are not versioned (see README).

## D15 - Personas, AI Score, cross-sell, subscription framing

**Context.** A wider "AI Marketing Intelligence" brief; most ideas already existed.
**Choice.** Additive features `target_personas` (8 values), `cross_sold_products`
and `subscription_style_framing`, extracted by the same structured call (no new LLM
call). The AI Score (`ai_score.py`) is a derived output with six axes, each a
documented mean of existing features; `None`, never a fabricated 0, without data.
**Consequence.** Nothing in the score is model-scored.

## D16 - External signals: geography and news

**Choice.** Regional interest (`geo_trends.py`, pytrends in `requirements-geo.txt`,
outside CI). Reputation reads newsapi.org (`NEWSAPI_KEY`) and newsapi.ai
(`NEWSAPI_AI_KEY`) in English, French and Dutch. A failed fetch is `null`, never
`headline_count: 0`, and a partial outage is not cached.
**Consequence.** `headline_count: 0` means every request was answered and nothing
matched.

## D17 - A model-extracted empty list is a zero

**Context.** A blank CSV cell meant both "none" and "not judged".
**Choice.** For model-extracted lists blank is a zero (the call returns every field
or raises); for rubric lists blank stays "not judged".
**Consequence.** Cross-sell scores exist again for Argenta, Beobank, CBC and VDK.

## D18 - Reproducible rankings

**Choice.** `category_comparison` breaks tied effect sizes by feature name. The
`none` lever sentinel, never valid in the dictionary, was removed.
**Consequence.** The exported top 10 is stable; it still cuts through a tie.

## D19 - React is the main UI, Streamlit stays as the key-free dashboard

**Context.** Two dashboards reading the same files let figures go stale.
**Choice.** The read-only views (Home, Profiles, Data, Rubric, Collection,
Research) are in `web/`, fed by `scripts/export_web_report.py`. `streamlit_app.py`
remains the dashboard that needs no key and is the Docker default (port 8506).
**Consequence.** New views go to React first.

## D20 - Recommendations and generated site

**Choice.** Recommendations are written from `report.json` only. The site is built
from chosen recommendations, in parallel, by `scripts/serve_web.py`. An "explain"
layer tags each section with the recommendations it implements, and prompts forbid
copy about the recommendations themselves.
**Consequence.** Regenerating the site needs an LLM key; its HTML is not versioned.

## D21 - Captured and generated HTML is not versioned

**Context.** 76 HTML files (bank page captures, generated site) weighed on the
repository, and the captures are third-party material.
**Choice.** `data/raw/` and `outputs/generated*/*.html` are git-ignored; derived
JSON/CSV stay tracked.
**Consequence.** Re-deriving features from raw pages needs a re-capture. Git
history is not rewritten; a `git filter-repo` pass is a separate user decision.
