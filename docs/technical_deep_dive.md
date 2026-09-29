# Technical deep dive

Everything the [README](../README.md) leaves out: what each module does, why the
measurement decisions are what they are, and the defects that shaped them.

Line references point at the code as it stands on `main` at the end of the project
window (25 September 2026). Figures come from the committed dataset and from a
real run of the test suite, not from memory.

---

## 1. The shape of the system

Two pipelines, joined only by files on disk.

```
                    scripts/collection_targets.yaml
                                  │
                   ┌──────────────▼──────────────┐
                   │  compliance.assert_can_fetch │  live robots.txt, fails closed
                   └──────────────┬──────────────┘
                                  │
           static_fetch ──── headless_render ──── headful_render
                                  │
                    ┌─────────────▼─────────────┐
                    │ scraper.extract()         │  deterministic features
                    │ visual_features           │  colour from the screenshot
                    │ llm_extractor             │  ONE structured call, 27 fields
                    │ quality.assess_capture()  │  is this even the right page?
                    └─────────────┬─────────────┘
                                  │
                   data/raw/<bank>/*.html + *.png   ← the reproducibility guarantee
                   data/processed/campaigns.csv
                                  │
                    rubric_sheet.py emit → human scores → merge
                                  │
                   data/processed/campaigns_scored.csv
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
   run_analysis.py        export_web_report.py        run_generation.py
   outputs/*.png,         web/public/report.json      outputs/generated/
   charts.md,             operations.json                   │
   bank_profiles,                  │                        │
   limitations.md            serve_web.py ──► recommendations.py
                                   │                  │
                             web/ (React)      site_generator.py
                                                outputs/generated_site/
```

Alongside it, `search_interest/` is a **separate** Google Trends share-of-search
pipeline with its own config, its own SQLite database and its own Streamlit app.
It imports nothing from `src/comparator`. The main pipeline reads two committed
CSVs from `search_interest/export/` through `src/comparator/trends.py` and nothing
else — the coupling is deliberately file-shaped so neither side can break the other
at import time.

---

## 2. The contract: `config/feature_dictionary.yaml`

One YAML file, 104 features, is the single source of truth. The dataset schema,
the validator, the generated documentation, the rubric sheet and the rater's guide
are all derived from it.

Each feature declares:

| Key | Meaning |
| --- | --- |
| `type` | `categorical` 31 · `boolean` 27 · `integer` 20 · `float` 11 · `string` 9 · `list[string]` 5 |
| `extraction` | `automatic` 53 · `model_assisted` 27 · `rubric` 13 · `derived` 11 — i.e. how far the value can be trusted |
| `comparability` | `cross_language` 93 · `within_language` 9 · `within_capture_window` 2 |
| `tier` | `core` 66 (required for the MVP) · `extended` 38 (never blocking) |
| `values` / `range` | the allowed set, for categoricals and numerics |

### How the contract is enforced

Not by convention — by twenty distinct checkpoints. The load-bearing ones:

- **Load time** (`dictionary.py`). An unknown YAML key, an unknown dimension or
  tier, a categorical with no declared values, a `required` feature outside
  `core`, or anything other than exactly one non-nullable primary key, all raise
  before anything else runs. The docstring is explicit about why: *"Fail loudly on
  a malformed dictionary — it is the contract for three people."*
- **Validation time** (`schema.py`). A column absent from the dictionary is a hard
  **error**, not a warning: *"Add them to config/feature_dictionary.yaml or drop
  them — the dictionary is the contract."* Values outside a declared enum or
  range, nulls in a non-nullable column, and any row with `robots_allowed = false`
  are all errors too.
- **Comparison time** (`analysis.py:318-337`). The set of comparable features is
  computed from `f.is_numeric or f.is_boolean` plus dimension and comparability —
  never from a hand-written column list.
- **Two freeze checks.** A byte-equality test between `feature_dictionary.yaml`
  and `.frozen.yaml` says *"you changed it on purpose"*; `freeze.py` says *"what
  you changed is allowed"*. The distinction is the point: byte equality fails on
  an addition, which the rule permits, and **passes on a rename**, which is the
  change that actually breaks analysis code.

`freeze.py` classifies a change as breaking if a feature is removed or renamed, a
type changes, an allowed value disappears, a range is added or narrowed, a tier is
demoted from core to extended, or a nullable column becomes non-nullable. Adding
features or widening an enum is explicitly allowed — that is how the bank list
grew to fourteen on 21/09 without breaking the freeze.

### What `comparability` actually does

`within_language` is fully gated. `analysis.language_excluded_features()` returns
nothing when the dataset holds one language, and every numeric or boolean
`within_language` feature when it holds more. On the current 18-page scope that is
exactly 8 features — `word_count`, `sentence_count`, `avg_sentence_length`,
`readability_score`, `second_person_ratio`, `first_person_plural_count`,
`disclaimer_word_share`, `text_to_image_ratio`. The dictionary declares nine; the
ninth, `meta_title`, is a string and never entered a numeric comparison anyway.

The exclusion is *reported*, never silent: `feature_accounting()` prints it and
`limitations.py` writes it into the generated limitations.

`bands.py` is the escape hatch — it converts a within-language number into a
cross-language ordinal band using fixed cutoffs, with an honesty note in its own
docstring: those cutoffs *reduce* the cross-language problem, they do not
eliminate it. A French sentence saying the same thing as an English one runs
15–20% longer. Good enough for "which bank leans long", not for a ranking.

**Gap worth naming:** `within_capture_window` is declared on two rate features and
enforced nowhere. A grep for the string across `src/` finds it only in the
dictionary loader's list of *valid* values. There is no analogue of
`language_excluded_features()` for capture dates.

---

## 3. Module reference

### Core data model

| Module | What it does |
| --- | --- |
| `dictionary.py` (195 l.) | Parses the YAML into frozen `Feature` dataclasses and refuses to return an inconsistent one. Owns `NUMERIC_TYPES`, `LIST_TYPES`, `LIST_SEPARATOR`. The root of the dependency graph — imports nothing from the project. |
| `schema.py` (285 l.) | Types a CSV against the dictionary, validates it, writes it back in dictionary order with list columns pipe-separated. Explicitly passes `format="ISO8601"` to `to_datetime` because the live path wrote microseconds and the manual importer did not, and a mixed column silently coerced the odd rows to `NaT`. |
| `bands.py` (107 l.) | Eight pure threshold functions. Centralised so the synthetic fixture and the real scraper use identical cutoffs — *"duplicating thresholds in two files is how they silently drift apart."* `readability_band` deliberately inverts the ascending convention, because a higher readability score means easier text. |
| `banks.py` (58 l.) | Bank → `traditional`/`challenger`, and bank → display name. Exists because the category was living implicitly in a config file and a row from elsewhere would have had none. Judgement calls are annotated inline (CBC is KBC's francophone brand; hellobank is BNP's digital brand; Keytrade is branchless since 1998, so it sits with the challengers). |
| `derive.py` (90 l.) | Recomputes all 11 `derived` features from their sources. Never invents: missing inputs stay missing. AIDA coverage requires all four booleans — *"2 of the 4 we bothered to score is not a score."* |

### Collection

| Module | What it does |
| --- | --- |
| `collection/compliance.py` (105 l.) | The gate. `check_robots()` fetches `robots.txt` **with `requests`, not `urllib`** — see bug 18 — caches it per domain per process, mirrors `RobotFileParser` status semantics (401/403 → disallow all, other 4xx → allow all), and fails closed on any read error. `assert_can_fetch()` raises `ScrapingNotAllowed`. |
| `collection/scraper.py` (636 l.) | Every deterministic feature: word counts, readability per language, CTA counting, rate detection, urgency markers, footnotes, shadow-DOM flattening. This is where most of the measurement bugs lived. |
| `collection/render.py` (411 l.) | Playwright at a **fixed** 1440×900 viewport for the five geometry features a static fetch cannot produce. Flattens shadow roots into the light DOM *after* the screenshot and geometry pass, because the flatten rewrites the DOM. Re-tracks `page_origin` on `framenavigated` so a host-changing redirect cannot turn the same-origin sub-resource gate into a no-op. |
| `collection/visual_features.py` (195 l.) | Colour. Measures `background_luminance` on the first screen *before* the 150×150 squash, and `brand_colour_share` over every pixel of the full-page screenshot rather than a quantised top-5 palette. Returns `None` for an unknown bank rather than a number that means something else. |
| `collection/llm_extractor.py` (382 l.) | 27 model-assisted fields in **one** structured call per page. Fixed system prompt, pydantic validation, then a cross-check against the dictionary's allowed values, then a bounded retry (default 1, so at most 2 identical calls). Its docstring states the design outright: *"Every page gets the same fixed prompt and schema, applied identically — consistency across banks is the point, not autonomous tool use."* |
| `collection/quality.py` (140 l.) | The gate a range check cannot be: is this a campaign page, or a JS shell, a maintenance notice, or a consent wall? Thresholds `MIN_PLAUSIBLE_WORDS = 120`, `UNUSABLE_WORDS = 40`, plus non-2xx status and NL/FR/EN error-phrase matching. |

**The compliance gate is called from four places** — `scraper.py:151` before the
HTML fetch, `render.py:303` before Playwright is even imported,
`visual_features.py:112` before the hero-image fetch, and `import_captures.py:91`
when re-importing a manually saved page. A sweep of every network call inside
`collection/` accounts for all of them.

Two honest caveats: cross-origin sub-resources during a render are deliberately
**not** robots-checked (blocking third-party fonts and CDNs would corrupt the very
geometry the module measures, and it is documented as such), and
`site_generator.py` fetches ING's own published SVGs from `assets.ing.com` outside
the gate — ING's own assets for ING's own demo, not a competitor scrape.

**Provider chain.** DeepSeek is pinned; Groq, OpenRouter, Cerebras, SambaNova and
a local Ollama sit underneath as outage fallbacks, all through the same
OpenAI-compatible `/chat/completions` shape. Groq alone rotates keys, and
`_groq_keys()` reads exactly three slots — this is the declared surface in
`.env.example`, not an oversight. A fallback is written into `extraction_model` on
the row, and `schema.validate()` warns, naming which banks got which model.

`PAGE_TEXT_LIMIT = 3000` characters means the model sees the top of a page only;
real pages carry 950–5,000 words. Small print and footer cross-sell usually sit
below the cut. Kept as-is so existing rows stay comparable — raising it means
re-extracting every page.

### Analysis

`analysis.py` (976 l.) is the comparison engine. The parts worth knowing:

- **`comparable_features()`** subtracts language-excluded features, withdrawn
  features and provenance columns from the dictionary's numeric/boolean set.
- **`comparison_matrix()`** exists as one function specifically because
  `positioning_axis()` and `similarity_matrix()` each built the standardised
  matrix inline — *"which is how a bug could live in one and not the other."*
  One-hot blocks are scaled by `1/√k` **after** standardisation, because z-scoring
  erases any constant applied before it.
- **`ing_vs_peers()`** attaches a `reportable` flag with four guards: fewer than 3
  peers, zero spread, peers at or near zero ("likely a failed extraction, not a
  real gap"), and `|gap| > 8 SD`. Unreportable gaps are ranked last but **never
  dropped** — "colour extraction failed for four banks" is itself worth seeing.
- **`check_deck_claims()`** has three verdicts, not two. A tie is never
  "supported", and a ranking column with one distinct value returns **not
  testable**.
- **`CAPTURE_INVALID_FEATURES`** holds the five withdrawn features with the reason
  for each, and is honoured by `comparable_features()` so a re-run cannot undo a
  withdrawal.

Nothing in this module computes a p-value. Cohen's d is reported as an effect
size; `recurring_patterns()` reports correlation with an explicit no-causation
docstring. With 14 banks, most carrying one page per family, a group mean is an
anecdote and the code says so.

### Scoring

| Module | What it measures | The caveat it carries |
| --- | --- | --- |
| `ai_score.py` | Six 0–10 axes per bank, all arithmetic, no LLM call | *"six independent means, not a validated psychometric scale — a bank can score high on trust by citing its branch network alone."* `innovation` returns `None` permanently and is kept on the radar so the gap is visible. |
| `cross_sell.py` | Distinct add-on product types per page ÷ 9 | Counts **breadth, not effort**. A page pushing one product ten times and a page mentioning it once score identically. `never_paired()` splits confirmed from insufficient-data, because with 1–2 pages a zero means "never had the chance to see it". |
| `rubric.py` | Nothing — it emits the sheet and merges it back | Computes no score. First non-empty value wins; nothing is averaged, because averaging was only safe while `agreement()` reported the spread it hid. |
| `benchmarks.py` | What three attention-selected brands measurably do differently | Ships its refusal *inside the payload*: "selected on search attention alone… not a demonstration that those choices are why they are searched for", and a test fails the build if that sentence is dropped. |
| `reputation.py` | Counts of Belgian headlines per theme, 90-day window | Themes, never sentiment. Belgian-source filtering by `.be` domain plus an allowlist, deduplication across languages and providers, and a same-day cache that **only ever caches a success**. |
| `market_context.py`, `research.py` | Share prices; paper search | Both deliberately standalone, not wired into the report, so nobody can put a share price next to a page feature. |

### Generation and reporting

- **`generation.py`** closes a loop: derive a numeric target from the data, brief
  a model, render HTML, then measure it with **the same extractor used on real
  bank pages**. Scoring generated output with a friendlier measuring stick would
  make the evaluation meaningless, so there is exactly one extractor in the repo.
  `GUARDRAIL_BLOCKED_FEATURES` excludes rate and numeric-claim targets, because
  you cannot ask a generator to match a bank's density of figures while forbidding
  it to invent figures.
- **`site_generator.py`** (1052 l.) builds the 10-page demo site. The **skeleton
  is fixed in code** — ten page keys, shared nav, shared stylesheet — and only the
  **content** is generated, one call per page, because a model asked to invent a
  site invents a different one every time and a different site cannot be compared
  with the last one. Three distinct retry reasons: wrong language, explain mode
  with no cited section, and a briefed recommendation not expressed in the copy.
- **`recommendations.py`** turns `report.json` into ranked changes, each tied to a
  measured feature. Invented feature ids are dropped; reputation-based
  recommendations are structurally forbidden from citing page features at all.
- **`report.py` / `charts.py`** generate the chart companion and the four PNGs.
  Every section carries a small table as the accessibility fallback, the
  non-overlap sentence is printed only when it is true, and a chart drawn without
  the focus bank retitles itself *"The market, without ING"* and stamps a warning
  on the figure — because the PNG is what ends up in a deck.
- **`limitations.py`** generates D-09 from the dataset. Its docstring names the
  failure it exists to prevent: D-09 is *"the deliverable most likely to be
  written from memory at 11pm on Day 9 — which is exactly when the inconvenient
  limitations get forgotten."*

### Surfaces

`streamlit_app.py` (554 l.) is the earlier operator dashboard, nine pages, all
data loaders cached and every missing file degrading to a visible warning rather
than a `KeyError`. `web/` is the React business UI (React 18 + Vite 6, no router,
no state library), fed by a single `report.json` snapshot plus live calls to
`scripts/serve_web.py` (FastAPI) for recommendations, site generation and the one
live external call, Semantic Scholar research search. `serve_web.py` states its
own constraint: *"Nothing here re-derives a number. Recommendations read
report.json; the site reads the recommendations. One direction only."*

`scripts/one_off/` holds single-use re-collection YAMLs, each one documenting the
specific wrong capture it fixes.

---

## 4. Testing and CI

**449 tests, 449 passing, no network.** Proven rather than asserted: the suite was
re-run with `socket.connect`, `connect_ex` and `getaddrinfo` all raising, and still
returned 449 passed. Expect `445 passed, 4 skipped` in CI, because `pytrends` lives
in `requirements-geo.txt` and CI installs only `requirements.txt`.

There is no mocking library and no `conftest.py`. Mocking is stdlib only —
`unittest.mock.patch` against the module-local `requests` attribute, plus
`monkeypatch` — which is consistent with the project's "no extra abstraction
layers" rule. Every test file bootstraps `src/` onto `sys.path` itself, so
`python -m pytest` works with no install step.

The most valuable assertions in the suite:

1. `tests/test_render.py` — `gate.assert_called_once()` then
   `browser.assert_not_called()`: the robots gate must fire **before** Playwright
   starts. A headless render is still a fetch, and that is easy to forget.
2. `tests/test_collection.py` — an unreadable `robots.txt` must fail **closed**.
3. `tests/test_schema.py` — the working dictionary against the frozen snapshot.
4. `tests/test_serve_web.py` — path traversal on the download endpoint.
5. `tests/test_rubric.py` — asserts the strings "Cohen", "kappa" and "disagreement
   is measured" are **absent**. The deliverable is test-forbidden from implying a
   reliability measure it does not have.

That last pattern is the one worth stealing: **a withdrawn claim gets a regression
test**, so a corrected mistake cannot come back.

CI runs on every push and every PR: `ruff check --select F` (pyflakes only,
deliberately narrow), `pytest`, `check_schema_freeze.py`, and a parallel job that
type-checks and builds the React UI — added late, because *"a broken `web/` could
merge green."*

Coverage gap worth naming: `banks.py` has no test at all, and it owns the
traditional-vs-challenger split every group comparison depends on.

---

## 5. Bugs encountered and fixed

The instructive thing about this list is its shape. **Almost none of these are
crashes.** The dominant failure mode is a measurement that runs cleanly, passes
every range check, and reports the wrong thing — and in several cases the wrong
number had already reached a slide.

### 5.1 The extractor was blind to shadow DOM

ING's page recorded **16 words and 0 images** — the `<title>`, twice — and was
marked unusable. It looked like a failed render.

ing.be is built from web components, and page content lives in shadow roots.
`page.content()` serialises the light DOM only. The commit documents what was
ruled out first: not timing (polled to 30s), not the user agent, not the URL.

Fixed by inlining every shadow root into the light DOM after the screenshot and
geometry pass, plus a `deep()` walker in the geometry JS. ING went from *16 words,
0 images, unusable* to *1,576 words, 49 images, ok*. Belfius had been silently
under-extracted the same way, with 206 shadow hosts.

> It looked like a failed render. It was a blind extractor.

### 5.2 An HTTP 503 maintenance page stored as a normal capture

BNP Paribas Fortis served 503 across its whole site. A 503 still renders a page,
so a maintenance notice was ingested as a legitimate capture. Nothing in the
pipeline looked at the status code. `render.py` now returns `http_status` and
`quality.assess_capture()` marks any non-2xx unusable.

A successful HTTP transaction is not a successful capture.

### 5.3 `brand_colour_share` put ING at +33.8 SD

ING topped the headline chart. The peer values were `[0.0, 0.014, nan, 0.0]` — a
peer standard deviation of about 0.007. The real story was that colour extraction
had **failed** for the other banks; the z-score simply divided by almost nothing.

This produced the `MIN_PEERS_FOR_SD` / `DEGENERATE_SPREAD` / `MAX_PLAUSIBLE_SD`
guards, and the design choice that an unreportable gap is kept and annotated
rather than dropped.

### 5.4 Colour measured on the wrong part of the page, twice

`brand_colour_share` read 0.0 for KBC and Revolut and null for Belfius. Two
stacked causes: it measured the **hero image**, while the dictionary declares
these features `source: screenshot` — a brand colour lives in buttons and headers,
not the lifestyle photo — and after switching to the screenshot it still read
0.000 for *every* bank, because it only inspected the quantised top-5 palette, and
a brand accent is a few percent of a mostly-white page.

> Both were properties of the method reported as properties of the banks.

### 5.5 `background_luminance` averaged the whole page strip

ING's expat page scored **0.916 (near white)** on a capture whose first screen is
black. The mean is pixel-weighted and the hero is about 6% of a 14,516px capture,
so the feature measured *"how much white body copy does this page have"*. The
first screen of the same page reads 0.521.

A D06 claim — "ING is measurably darker than its peers" — had already been
published on this. After re-deriving from the top crop, the ranking **inverted**:
ING became the brightest bank. The claim was withdrawn with the correction written
next to it.

The fix was deliberately scoped so it did not undo 5.4: `brand_colour_share` keeps
its full-page basis, with a comment saying why cropping would re-break it.

### 5.6 `_rate()` reported "100% en ligne" as an interest rate

`rate_value_pct = 100.00`, identically, for BNP Paribas Fortis, KBC (×3) and ING.
The function matched the **first "N%" anywhere on the page**, so marketing copy
beat any real rate. Caught because a "traditional banks average ~85% rate" line in
a draft looked implausible.

Fixed with a rate-keyword proximity rule (fr/nl/en, within 40 characters), applied
by a new deterministic re-derivation script. Two rows still read 100.00 and are
recorded as a known ceiling of a proximity heuristic rather than chased.

**The more valuable half of this entry:** the first fix attempt re-used
`reextract_model_fields.py`, which makes a fresh LLM call per row, and *measurably
re-rolled* personas, cross-sell and imagery on already-finalised rows through
ordinary model non-determinism. Reverted, and kept as a "don't do this" note in
that script's docstring.

> Never use a non-deterministic path to apply a deterministic fix.

### 5.7 `<picture><source>` counted as animation

`has_animation` was true for pages that merely serve modern image formats:
**217 of 219 `<source>` tags across 16 real captures sat inside `<picture>`**.

Deck claim H3 — "ING is the only traditional bank using animation" — flipped: ING
went 0.40 → **0.00**, the inverse of the deck. The commit is explicit that it does
**not** fix already-collected rows, since `has_animation` is stored at collection
time.

### 5.8 A brand colour constant that had gone stale

Every Argenta row scored ≈0. `BRAND_COLOURS["argenta"]` held the **pre-rebrand**
red-orange; the live site is green. `brand_colour_share` counts pixels within a
tolerance of that hex, so it was matching a hue the bank no longer uses.

A hardcoded reference constant is a silent, dateless dependency on the outside
world.

### 5.9 The model scored 8 of 9 rubric features from the wrong evidence

The best bug in the repo. Caught by computing Cohen's kappa against the human
sheet: `value_prop_clarity` kappa **−0.12, Spearman −0.77** — the model ranked
pages almost exactly *opposite* to the human. `aida_interest` and `aida_action`
scored 0.00.

`TEXT_SCORABLE` was **hand-written**, and 8 of its 9 entries are declared
`source: screenshot` in the dictionary. The module's own docstring claimed it
refused to score from the wrong evidence, and then did exactly that.

Impact already on screen: `value_prop_clarity` moved from −2.47 SD (*less* clear)
to +1.41 SD (*more* clear) — sign flipped. `aida_coverage_score` was a headline web
finding, "ING fails at campaign structure", at 0.00 vs 2.42; it evaporated at 3.00
under human scoring.

Fixed by deriving the text/vision split from the dictionary's `source` field, with
a test so no future edit can quietly re-add one.

> A quality metric turned out to be a bug detector. And a docstring promise is not
> an enforcement mechanism — derive the constraint from the source of truth.

### 5.10 Averaging two integer rubric scores broke the dataset load

`"cannot safely cast non-equivalent float64 to int64"`. `merge_scores` averaged two
integer rubric scores into 2.5, and the dictionary declares those features as
integers. Only reachable once a second rater existed — which happened that day.

Now rounded to the scale the feature is declared on, with the reasoning that an
ordinal 1–5 rubric has no half-step.

### 5.11 A one-hot weighting fix that did nothing

Self-caught by measuring. The first version scaled each one-hot block by `1/√k`
**before** standardising — and `standardise()` z-scores every column, which erases
any constant applied beforehand. Every dummy came back at unit variance, so 19
categoricals became 55 columns and collectively outvoted all 50 numeric features:
the exact opposite of what the docstring claimed.

Fixed by moving the weighting after standardisation, and by collapsing two inline
copies of the matrix construction into one shared function.

> "I wrote a normalisation" is not "the normalisation has an effect" until you
> measure it. And duplicated computation is where asymmetric bugs hide.

### 5.12 `cta_count` — three bugs, a regression, and a withdrawal

The most instructive *thread*, because it ends in refusing to publish a number.

1. The original rule counted every `<a>`/`<button>` whose label matched a keyword
   list, **chrome and duplicates included**, so it measured how often a page
   repeats "En savoir plus". Crelan scored **42** against ING's 4, and slide 12
   read that as "ING is behind on calls to action". Fixed to skip chrome and count
   distinct `(label, href)` pairs — which is what the dictionary already said the
   feature was. Crelan 42 → 2.
2. That fix was **silently overwritten by a later re-collection**. Crelan was back
   to 42, and the same re-collection destroyed English-language coverage.
3. The stated cause of the eventual withdrawal — client-side rendering — was
   **wrong**. `render.py` stores the post-JS DOM and the saved ING HTML holds all
   144 clickable elements. An hour went into prototyping OCR for a problem that
   did not exist. The real second bug: `_in_chrome()` tested only `<nav>`/`<footer>`
   tags and ARIA roles, but hellobank's menu is a `<div class="navbar-container">`
   — so 2 of 14 banks had their entire mega-menu eligible to be counted.
4. Fixing *that* caused a self-inflicted regression within the hour: adding
   `header` to the chrome match hit `class="product-header"` and excluded ING's own
   main CTA. Chrome names are now matched on whole hyphen-separated parts.
5. The withdrawal itself had been done by **hand-deleting the gap from
   `report.json`** — which `export_web_report.py` rebuilds from the analysis, so
   the first re-run put it straight back.

> A correction a re-run undoes is not a correction.

Final disposition: withdrawn, no direction claimed. A structural replacement rule
was tried, measured and rejected, because *"whether a clickable product card is a
call to action is a marketing judgement, not a property of the markup."*

### 5.13 `has_comparison_table` measured HTML authoring style

A 0.57-vs-0.00 traditional/challenger split at **d = −1.23** — a big, publishable
effect. The rule was `soup.find("table") is not None`. Traditional banks mark
tariff grids up as `<table>`; N26 and Revolut build the same plan comparison in
CSS and scored False, **though their captured text carries the plan names and
monthly prices**.

The cleanest example in the repo of *a difference in markup convention reported as
a difference in business strategy.*

### 5.14 Reputation: three separate silent-failure bugs

- **Language matching leaked non-Belgian sources.** A Dutch accountancy trade site
  writing about "ING" counted as Belgian ING coverage, because Dutch and French
  are spoken well beyond Belgium. Fixed with a `.be`-or-allowlist filter — and the
  regression test caught an **over-correction** before it shipped, when a real
  Belgian regional paper on a `.net` domain was being wrongly dropped.
- **Quota exhaustion read as "no news".** The free tier is 100 requests/24h; a
  handful of export runs in one afternoon exhausted it, and every bank's signal
  "silently thinned out". Fixed with a same-day cache that caches **only a
  success**, because a `None` cannot be told apart from an outage and caching it
  would freeze that outage into a permanent "nothing found" for the day.
- **HTTP failures indistinguishable from genuine zero results.** Both returned
  `[]`. Adding a warning with the status code immediately surfaced that the API was
  returning **401 (rejected key), not 429 (quota)**, for seven banks the UI had been
  showing as "no recent headlines found".

> An empty result and a failed request must never share a return value.

A fourth, related one: the key was being sent to newsapi.**org** when it belonged
to newsapi.**ai** — two different companies that share a name, with
non-interchangeable keys.

### 5.15 `check_deck_claims()` awarded "supported" on a tie, by index order

On identical all-tied data, one claim read "supported" and another "not supported".
`idxmax()`/`idxmin()` return whichever label comes first in the Series, so the
verdict was decided by index order alone.

The deeper version followed: three of five kickoff-deck observations were reported
"not supported" off `word_count_band`, **a column that reads "long" for all
fourteen banks** — real pages carry 950–5,000 words and the band's top edge stops
at 600, so it saturates and cannot rank anyone. Verdict logic gained a third state.

> A claim a measure cannot rank is not a claim the measure refuted.

### 5.16 Blank cells doing the work of zeros

`persuasion_lever_count` was computed over 9 peer banks instead of 13. Argenta,
Crelan, VDK and hellobank were sitting out, because `persuasion_levers` was empty
on 21 pages and a blank reads as "not judged" → NA → the whole bank drops.

But the judge had confirmed those pages genuinely have **no lever** — a zero, not
an absence. Adding `none` as an allowed value (a pure addition the freeze rule
permits) let `derive.py` count it as zero while a blank still returns NA.

ING's gap moved from +2.46 over 9 peers to **+3.32 over 13**; positioning 0.28 →
0.39. The same pass found 47 of 642 judged cells that were not the rater's, because
her morning corrections had never been re-merged — while a slide claimed every
judged feature came from one sheet.

> Missing-vs-zero is the most under-appreciated data-quality bug there is.

### 5.17 The stale derived file

`web/public/report.json` and every recommendation built from it served pre-fix data
all session. `export_web_report.py` defaults to `campaigns_scored.csv` (the
rubric-merged file) while `run_analysis.py` defaults to `campaigns.csv`, so
re-running only the latter leaves the merged file silently behind. ING's positioning
moved 0.437 → 0.362 once corrected.

The fix in that commit was **procedural** — re-run both, plus documentation. The
actual guard landed two days later as `tests/test_dataset_sync.py`, asserting every
`page_id` in one file has a row in the other.

> Two entry points reading two different derived files is a hazard no amount of
> care fixes. Only a test does.

### 5.18 The compliance gate bypassed on the hero-image fetch

No observable symptom — a silent policy violation. `extract_colours()` fetched the
hero image with a plain `requests.get()`, skipping the gate that the HTML fetch
runs. `robots.txt` can allow a page while disallowing its `/images/` path.

> Any code path that touches the network is a fetch.

A sibling of this one, in the opposite direction: the gate itself was once
**refusing permission it could in fact obtain**. `_fetch_robots` used
`RobotFileParser.read()`, which goes through urllib; a stock macOS Python has no CA
bundle, so every HTTPS `robots.txt` raised `CERTIFICATE_VERIFY_FAILED`, the gate
failed closed, and **every target was skipped** — while the pages themselves were
perfectly fetchable through `requests`. One HTTP stack for both means "we can read
the rules" and "we can fetch the page" cannot disagree.

### 5.19 A relative hero-image URL, swallowed by a broad `except`

Rows got null colours with nothing to notice. `_hero_image_url()` fell back to the
raw `<img src>` when no `og:image` existed, returning a relative path, which raised
`MissingSchema` — caught by a deliberately broad `except` that exists so a
best-effort feature never kills a row.

The textbook interaction: a broad `except` designed for resilience turned a real
bug into invisible data loss. Both decisions were individually defensible.

### 5.20 A full read of the repository, six more defects

A deliberate line-by-line pass found a different *class* of bug than testing did —
mostly wrong-identifier and wrong-default errors that produce plausible-looking
empty results:

- `recommendations.py`: `[...known...] or list(r.features)` — when the model named
  **no** real feature id, the empty list fell through the `or` and put **every
  invented id back**, so phantom evidence reached the UI.
- `ai_score.py`: the trust axis counted `regulatory_disclosure_prominence ==
  "not_applicable"` as a *failed* condition, and that value is on 17 of 18
  current-account pages — no TAEG is expected on a current account. *"Not
  applicable" is not "no."*
- `llm_extractor.py`: a provider returning **HTTP 200 with a malformed body**
  raised `KeyError` straight out of the fallback loop, skipping every remaining
  provider.
- `run_analysis.py`: asked reputation for the key `bnp_paribas_fortis` instead of
  the display name, so that bank could never return a headline; and "Hello bank!"
  was searched as the bare word "Hello".
- `render.py`: a background transparent all the way to the root was read as black
  — the wrong contrast reference.
- `rubric_sheet.py emit` overwrote a scored sheet without warning.

Tests went 423 → 444, and CI gained the lint and the web build.

### Also fixed, lower instructional value

A dev-proxy port mismatch that was the real cause of a reported "Error 500"; list
fields written as Python reprs (`"['family', 'investor']"`) failing validation on
all 50 rows; a merge keyed on `page_id` that would have silently replaced pages,
since re-collection renumbers ids; features with a NaN in any bank dropped
silently from the comparison; three pages fetched from the **wrong URL**;
`urgency_marker_count` scoring a dated deadline as zero, which moved ING from
−0.34 SD to **+3.69 SD**, the largest gap in the set; and a cross-sell taxonomy
that collapsed insurance, credit cards and partner perks into one `other` token
counted once, so the score said the opposite of what the pages showed (ING 17% →
25.9%, last to sixth of fourteen).

---

## 6. The lessons, extracted

1. **The dominant bug class is a measurement that runs cleanly and measures the
   wrong thing.** Not one of the headline bugs above raised an error.
2. **An empty result and a failed request must never share a return value.**
3. **A fix applied to an artefact is not a fix.** Fix the generator.
4. **Derive constraints from the source of truth; do not restate them.** A
   hand-written copy of a list that lives in a config file will drift.
5. **Quality metrics make excellent bug detectors.** Inter-rater kappa was
   introduced to measure agreement and found a wrong-evidence bug instead.
6. **Several fixes moved a number that was already on a slide.** The habit of
   writing `THIS CHANGES WHAT A NUMBER MEANS` into the commit body, plus an
   append-only decision log, is what makes the trail reconstructable at all.
7. **"We cannot measure this defensibly" is a legitimate engineering outcome.**
   Three features were withdrawn rather than published, with the reason recorded
   and the exclusion made visible.
8. **A withdrawn claim deserves a regression test.**

---

## 7. Reproducibility, honestly

The analysis stage onward is reproducible from the committed data with pinned pip
packages and no API key, provided you accept an empty `reputation.json` and no
fresh `geo_trends.json`.

Full end-to-end reproduction from an empty `data/` is **not** achievable without:

- at least one working LLM key (the chain is DeepSeek → Groq ×3 keys → OpenRouter
  → Cerebras → SambaNova → local Ollama);
- a Playwright Chromium install, which is a separate download not covered by
  `pip install`;
- a human rater re-doing the judged sheet — no command can produce that.

Every dependency is pinned with the reason stated in `requirements.txt`: *"Pinned
so the pipeline is reproducible by a third party (NFR-01)."* `pytrends` and
`streamlit` are deliberately split into their own files, to keep an unofficial,
rate-limited library and a UI-only dependency out of the pipeline's core list.

Generated campaigns are described as *"mostly, not perfectly, reproducible"* — a
measured statement, not a hedge. The repo's own code is deterministic; the model
is not entirely, because temperature controls sampling and not routing, and an MoE
model served in batches can still vary. Every generated artefact records the
SHA-256 fingerprint of the prompt that produced it.

---

## 8. Open issues at the end of the window

| Issue | Why it matters |
| --- | --- |
| `report.json`'s `generated` block still publishes a `cta_count` scorecard **"hit"** | The same file's limitations say the feature is never compared. `export_web_report.py` reads step-5 artefacts dated 22/09 from disk instead of recomputing. Same class as 5.12, one artefact further out. |
| `decisions.md` D6 names `deepseek-chat` | A model on zero rows. The log is append-only and was never amended; `design.md` records the switch. |
| `within_capture_window` enforced nowhere | Two rate features declare it; no code acts on it. |
| `banks.py` untested | 58 lines owning the traditional/challenger split. |
| `cross_sell.py` docstring ≠ code | The docstring describes a per-page family exclusion; the code subtracts a constant 1. The numerator can also include `other`, so a page could exceed the nominal 1.0 ceiling. |
| `search_interest/` export prose hardcodes "9 banques / 3 fiches" | The data is correct at 14 banks / 5 sheets; only the generated narrative is stale, and it will regenerate stale. |
| `search_interest/campaigns/` cannot be imported | It references a config constant that no longer exists. Documented as orphaned; it is worse than the doc says. |
| `generation_guardrails` never runs on the site path | The demo site's "no invented rate" rests on the prompt rule plus a hardcoded footer, not a mechanical check. Consistent with the module's own stated scope, but worth knowing. |
