# Decision log

Project Plan section 9 lists seven decisions needed in the first two days. This
file records the ones taken, so "we decided it on Tuesday" is checkable rather
than remembered. One entry per decision; append, never rewrite.

---

## D6 — Which LLM for model-assisted features and generation

**Owner** Stephane · **Due** Day 2 (Tue 15 Sep 2026) · **Status** decided

**Decision.** DeepSeek `deepseek-chat` is the pinned model for this project.
Every model-assisted feature and every generated campaign is produced by it.

**Why this one.** It is the model we actually have a working key for today, and
Day 2 is the deadline. The requirement was never "the best model" — it was *one*
model, named and recorded, so that a difference between two banks is a difference
between two banks and not between two judges.

**Why pinning matters (NFR-02).** Roughly a quarter of the dictionary —
24 of 97 features — is model-assisted. `collection/llm_extractor.py` falls back
across providers when one is rate-limited. Before today that fallback was
*silent*: a single collection run could label ING with one model and Revolut with
another, and nothing in the dataset would say so. Any finding on those features
would have been partly an artefact of which provider happened to be up.

**What changed in the code.**

| Change | Where |
| --- | --- |
| DeepSeek added at the head of the provider chain | `collection/llm_extractor.py` |
| `_call_llm` now returns `(text, "provider/model")` | `collection/llm_extractor.py` |
| `extract_model_assisted_with_provenance()` returns the model alongside the fields | `collection/llm_extractor.py` |
| New `extraction_model` column, written on every collected row | `config/feature_dictionary.yaml`, `scripts/run_collection.py` |
| `validate()` warns when one dataset contains more than one model, and names which banks got which | `schema.py` |

**Fallback policy.** The other providers stay configured beneath DeepSeek. Losing
a night of collection to one provider outage is worse than a mixed dataset —
but a mixed dataset must be *visible*, not silent. If a run does fall back, the
options are: re-run the affected banks on the pinned model, or report the mix as
a limitation in D-09. Never ignore it.

**Prompts.** Stored in the repository as required, not in a notebook or a chat:
`SYSTEM_PROMPT` in `collection/llm_extractor.py` (feature extraction) and in
`generation.py` (campaign generation). `temperature=0` throughout.

**Cost and licensing.** Paid API, key held by Stephane, never committed —
`.env.example` documents the variable; `.env` is gitignored.

**Revisit if.** DeepSeek quality proves inadequate on the first real captures
(Day 3–4), or agreement with human labels on the validation sample is poor. Any
change of model invalidates the model-assisted features collected before it —
re-run all banks, do not mix.

---

## D5 — Dataset schema and file format

**Owner** Dan + Stephane · **Due** Day 2 · **Status** decided, frozen

One CSV, one row per campaign page, provenance columns first. List-valued
features (`palette_hex`, `accent_locations`, `persuasion_levers`) are stored
pipe-separated so the dataset stays plain CSV.

The freeze is enforced two ways, deliberately:

- `tests/test_schema.py::test_dictionary_matches_frozen_snapshot` (Siegried) —
  byte equality against `config/feature_dictionary.frozen.yaml`. Catches an
  *accidental* edit.
- `scripts/check_schema_freeze.py` (Stephane) — the rule itself: additions pass;
  renames, removals, type changes, narrowed ranges or categories, tier demotions
  and tightened nullability fail, naming the feature.

Byte equality alone is not the rule — it fails on an addition, which section 3.2
explicitly permits, and it *passes* on a rename, because updating both files
makes the bytes match again. A rename is the change that actually breaks
analysis code, so it is the one worth catching.

**sieg 16/09, follow-up.** `feature_dictionary.frozen.yaml` fell out of sync
with three `notes:` additions made 15/09 (`accent_locations`,
`text_image_layout`, `layout_archetype`) — documentation only, no type, value,
tier or nullability change. `check_schema_freeze.py` confirmed zero breaking
changes; `notes` isn't even part of what that check compares, so this was
never a freeze-rule violation, only the byte-equality drift alarm doing its
job. Synced without waiting on a full re-vote — flagged to Dan and Stephane
for awareness, not as a blocking approval.

**sieg 16/09, data quality check.** The two largest gaps in `ing_vs_peers.csv`
(`urgency_marker_count` +6.35 SD, `image_count` +4.09 SD) were recalculated
by hand from `bank_profiles.md` — a different code path than
`ing_vs_peers.csv`, so this isn't circular. Peer mean, peer std and the
resulting gap all matched exactly for both features. Safe to use in the
business narrative.

**sieg 17/09, parked idea - channels beyond the open web.** Prompted by a CBC
radio ad heard live - do the other banks in scope run radio (or other
non-web) campaigns too, and is that worth comparing? Not pursued: the
feature dictionary is built entirely for web content (layout, palette, page
text) and has nothing to say about a 20-second audio spot - this would need
its own dictionary (tone of voice, spot length, jingle presence, call-to-
action framing) and its own collection method (recording/monitoring, not a
URL fetch), not a small extension of the current pipeline. Same category as
the already-named "extend beyond the open web" next step (social, in-app),
just a channel further out. Parked here rather than in `limitations.md`
because that file's next-steps list is generated from the dataset now (per
the 17/09 audit-followups fix) and can't carry a step the data itself
doesn't suggest. Revisit if: the team has scope/time for a v2, or a bank's
radio campaign becomes directly relevant to a specific finding (e.g. an
image-based feature that a radio spot could contextualise).

**sieg 19/09, personas + AI Score - flagged for Dan and Stephane, not a blocking
approval.** Two additive-only changes, prompted by a wider "AI Marketing
Intelligence Platform" brief - most of that brief's ideas already exist here in
some form (Trends, LLM feature extraction, positioning/clustering,
recommendations); these two did not.

1. `target_personas` (list[string], `banking_domain`, `extended`, `model_assisted`)
   - fixed 8-value taxonomy (student, family, entrepreneur_self_employed, expat,
   investor, retiree, digital_nomad, mass_market), extracted by the SAME single
   structured call `llm_extractor.py` already makes (no new LLM call, no new
   provider). Aggregated to a per-bank distribution in `profiles.py`. Passed
   `check_schema_freeze.py` clean (pure addition); `feature_dictionary.frozen.yaml`
   re-synced the same way as the 16/09 note above.
2. AI Score (`comparator/ai_score.py`, new module) - NOT a dictionary feature,
   same status as `positioning_axis`/`category_comparison`: a derived analysis
   output. Six axes (Digital, Trust, Cross-sell, Personalisation, Innovation,
   Simplicity), each a documented mean of features already in the dictionary -
   deliberately NOT a model-scored index, so nothing here can hallucinate a
   number. `None` (never a fabricated 0) when a bank has no data for an axis.

Taxonomy and formulas are Siegried's first pass - open to Dan/Stephane's read
before either is treated as final, same non-blocking spirit as the 16/09 sync.

**sieg 19/09, cross-sell + three external-data utilities - same brief, same
non-blocking flag to Dan and Stephane.**

3. `cross_sold_products` (list[string], `banking_domain`, `extended`,
   `model_assisted`) - the "cross-sell score/graph" gap. Reuses the SAME
   7-value `product_family` taxonomy already frozen in this dictionary rather
   than inventing a parallel one, extracted by the same structured call as
   `target_personas`. `comparator/cross_sell.py` turns it into a per-bank score
   (products cross-sold / products possible, the brief's own formula, kept as
   a 0-1 ratio) and a product co-occurrence matrix - the "graph", flattened to
   a table since this repo has no graph-drawing library and one wasn't worth
   adding for 7 nodes.
4. `comparator/reputation.py` (NewsAPI, optional via `NEWSAPI_KEY`) - recent
   headlines per bank classified into THEMES (innovation, crisis, results,
   ...), never sentiment (out of scope for this pass, see the module
   docstring for why themes are the honest substitute). Degrades to an
   explicit "not configured" state without a key, same shape as `trends.py`
   when Dan's export is absent - never silently shows every bank as zero.
5. `comparator/market_context.py` (Finnhub, optional via `FINNHUB_API_KEY`) -
   deliberately NOT wired into report.json or the web UI. Only 3 of the 9
   banks in scope are even publicly listed (ING via ING Groep, KBC Group, BNP
   Paribas Fortis via BNP Paribas SA) - Belfius, Argenta, Crelan aren't listed
   and Revolut/N26/bunq are private, so a stock-impact feature here would
   mostly be empty cells. Kept as a single standalone lookup function instead
   of building a pipeline/chart around data most banks don't have. The brief's
   own text already called Finnhub low-value for this project.
6. `comparator/research.py` (Semantic Scholar, keyless at low volume) - not
   wired into the analysis pipeline or report.json. The brief names this
   "Optionnel" and never defines a per-bank metric to compute from academic
   papers, so this stays a `search_papers()` helper rather than invented
   scope with no defined output.

   **sieg 20/09, updated per Siegried's explicit request** ("branche le",
   not "laisse tomber" as I'd recommended): wired into a new Research page
   in `streamlit_app.py` - a manual search box for whoever is writing the
   business narrative, run on demand. Still no per-bank metric, still not
   in `report.json` or the FastAPI/React UI: the risk being avoided was
   never "showing search results," it was auto-generating an unreviewed
   feature-to-paper match and presenting it as evidence. A human typing a
   query and reading the results is a different, lower-risk thing.

Scraping additional channels (LinkedIn/Instagram/YouTube) and sentiment
analysis (Reddit/App Store/FinBERT) from the same brief were explicitly
excluded from this pass by Siegried - not attempted here.

**sieg 19/09, one more feature + two small-N honesty fixes, found while
looking at the real (not fixture) data for the first time this session.**

7. `subscription_style_framing` (boolean, `banking_domain`, `extended`,
   `model_assisted`) - Siegried noticed Revolut/bunq frame their account tiers
   as a phone/streaming-style subscription ("abonnement") rather than a
   traditional banking "pack". Verified in the raw page text before adding the
   feature: Revolut 16 mentions of "abonnement", bunq 9, every traditional
   bank 0. Same structured call as the other two additions above. The model's
   own verdict on the real dataset only came back `True` for Revolut - bunq's
   raw mention count didn't translate into the model calling it the
   *dominant* framing, which is a legitimate judgement call, not a bug.
8. `analysis.py::check_deck_claims()` - H1/H2/H5 used to test raw `word_count`,
   which `language_excluded_features()` drops ENTIRELY the moment >1 language
   is in the compared scope (true since English was added 16/09, worse once
   KBC's Dutch page was added today). Switched to `word_count_band` (fixed
   universal thresholds, `comparability: cross_language`), which survives.
   H1 (Belfius) stays "not testable" for an unrelated reason - Belfius wasn't
   in the `current_account_pack` scope until today's captures.
9. `cross_sell.py::never_paired()` now returns `{"confirmed", "insufficient_data"}`
   instead of one flat list. With most product families still at 1-2 real
   pages, a "0" co-occurrence was almost always "never had the chance to
   observe it", not a real finding - same smallN honesty `ing_vs_peers()`
   already applies via `MIN_PEERS_FOR_SD`. `export_web_report.py` and
   `CrossSell.tsx` updated to read the split from Python rather than
   recomputing a naive version client-side.

Also merged 9 new real captures today (Belfius current-account + savings,
KBC mortgage + savings, ING mortgage + a professional-account page, N26
professional-account + savings) - `data/processed/campaigns.csv` is
gitignored so this doesn't show in the branch diff, only the code that
reads it. The two "professional account" pages (ING, N26) were classified as
`current_account_pack` (no dedicated business-account family exists in the
taxonomy) - flagged for Dan/Stephane's read, not a unilateral call to treat
as final. These 9 pages still need a human rubric-scoring pass
(`scripts/rubric_sheet.py emit`) like any fresh capture - the 13 human-scored
features are blank for them until then.

**sieg 20/09, geographic interest.** The kickoff brief's "intérêt
géographique" axis was never built - the existing Google Trends work reports
Belgium as a whole and never breaks it down by region. Added
`comparator/geo_trends.py` + `scripts/geo_trends.py`: direct pytrends calls
(`interest_by_region`, Brussels/Flanders/Wallonia), output at
`outputs/geo_trends.json`, and a new web UI section ("Search interest by
region", Analysis tab). pytrends pinned in a new `requirements-geo.txt`, same
reasoning as `requirements-streamlit.txt` - kept out of the main
`requirements.txt` and out of CI, tests skip cleanly via
`pytest.importorskip` when it is not installed.

First real run, for the record: KBC and Argenta (traditional, Flemish roots)
peak in Flanders; BNP Paribas Fortis, Crelan and Belfius peak in Wallonia;
Revolut/N26/bunq (the three challengers) all peak in Brussels. **ING is the
one traditional bank that also peaks in Brussels** - the same direction as
every challenger, and the one traditional bank that doesn't match its own
peer group's regional roots. Otherwise matches what's already known about
each bank's footprint - a sanity check, not a finding this project is set up
to claim (same "context, not performance" caveat as the rest of the Trends
work). See D06_business_narrative.md insight 6.

---

**sieg 20/09, `rate_value_pct` scraper bug found and fixed.** While drafting
the D06 narrative, a "traditional banks average ~85% rate" number looked
implausible - `rate_value_pct`=100.00 repeated identically across BNP
Paribas Fortis, KBC (x3) and ING. Root cause: `scraper.py::_rate()` matched
the FIRST "N%" anywhere on the page, so marketing copy ("100% en ligne",
"100% digital") was reported as a rate before any real one. Fixed by
requiring a rate keyword (`taux`/`interet`/`rendement` fr, `rente`/`interest`
nl, `rate`/`interest`/`apr` en) within 40 characters of the match - see
`_RATE_KEYWORDS` next to `_rate()`. This touches Dan's `collection/scraper.py`,
done with Siegried's explicit go-ahead this session (not a unilateral call).

Applied to the real dataset via a new, narrowly-scoped `scripts/fix_rate_fields.py`
- re-reads each page's stored HTML and refreshes only `rate_shown`/
`rate_value_pct`, no LLM call. (A first attempt reused
`reextract_model_fields.py` instead, which makes a fresh LLM call per row -
that measurably re-rolled personas/cross-sell/imagery on several already-
finalized rows through ordinary model non-determinism, an unwanted side
effect for a deterministic bug fix. Reverted before committing; kept as a
documented "don't do this" note in that script's docstring.)

Two rows still show a rate after the fix, both explainable and left as-is
rather than chased further: `kbc_mortgage_fr_01` (100.00) - the page text
reads "...sur votre taux d'intérêt et pouvez emprunter 100% de la valeur de
votre habitation", so the keyword-proximity heuristic still fires on a
loan-to-value percentage sitting right next to a real rate mention; and
`kbc_savings_account_fr_01` (100.00, unchanged) - its snapshot HTML is not
on disk (`data/raw/kbc/savings_account_fr_01.html` missing), so the script
correctly skips it rather than guessing. Both are a known ceiling of a
regex/proximity heuristic, not something worth more code for a 10-day
project - flagged here instead. Full outputs/web report regenerated from the
corrected dataset; `docs/D06_business_narrative.md`'s numbers (ING
positioning score, AI Score digital axis, urgency/persuasion/onboarding gaps)
were re-verified against the regenerated `report.json` and three more stale
figures were caught and corrected in the same pass (unrelated to this bug -
the dataset had moved since those lines were first drafted).

**Correction to the paragraph above, same day.** "Full web report
regenerated" was not actually true. `scripts/export_web_report.py` defaults
to `data/processed/campaigns_scored.csv` (the rubric-merged dataset,
produced by `scripts/rubric_sheet.py merge`), not `campaigns.csv` -
`run_analysis.py` defaults to the latter, so I had been regenerating
`outputs/*.csv` correctly all along, but every `export_web_report.py` run
this session silently kept reading a `campaigns_scored.csv` last merged
19/09 18:26, **before** the rate fix - `web/public/report.json` and the
recommendations built from it still had the old bug the whole time. Found
because Siegried spotted the web UI's footer crediting `campaigns_scored.csv`
and its timestamp didn't line up. Fixed by re-running
`scripts/rubric_sheet.py merge --sheets data/rubric/*_scores.csv` (which
non-obviously has to happen after ANY change to `campaigns.csv`, rubric
scores or not, or the merged file silently drifts from it) and then
`export_web_report.py` again. ING's positioning score moved again as a
result: 0.437 (my previous, still-stale number) -> **0.362** (the real one).
`docs/D06_business_narrative.md` corrected a second time for this -
`persuasion_lever_count`'s numbers and the AI Score `digital` axis also
moved (3.67/2.17/+2.18 -> 3.5/2.08/+1.94; 8.2 -> 8.8 respectively).

Lesson for next time a dataset-affecting fix lands: **both**
`run_analysis.py` **and** `rubric_sheet.py merge` (then
`export_web_report.py`) need a re-run - they read different files, and only
running one silently leaves the other's output behind.

---

**steve 21/09, Trends can inform recommendations - as marked context, never as
evidence.** The Recommendations tab gained an opt-in **Include Google Trends**
checkbox. Ticked, `build_recommendations(report, include_trends=True, trends=...)`
gets a deterministic digest of `trends.json` - the run's captured banks, the
measured product family, the last 24 months, ~8 KB - fenced in the prompt as
*context only*. The model adds 2-4 **timing and focus** recommendations on top of
the analysis ones, tagged `basis: "trends"`, rendered in their own group, and
forbidden from citing a page feature as evidence. This deliberately keeps the line
`trends.py` already drew: a search spike is not proof that a page or campaign
performed, so trends may change *when* something is prioritised, never *what* the
page evidence says. `used_trends` travels with the saved set so the toggle reloads
ticked, and payloads saved before this change still load (`basis` defaults to
`analysis`).

**steve 21/09, explained generation, and the meta-copy trap it exposed.** The
generated site gained an **Explain each section** checkbox: the model tags each
section with the recommendation ids it implements plus a rationale, and the
renderer draws a glowing box on the content column with an **(i)** button whose
balloon opens above it. Opening one switches that section to a slow yellow
flicker, deliberately not ING orange, and a bar above the site turns the whole
layer off (remembered across pages). The first real explained run produced *meta
copy* - sections about the recommendations ("Add alt text to every image", "When
we review this page") - because the page prompt said a recommendation was only
"implemented" if a reader could see it. The prompt now states the copy is customer
product copy, bans references to the page/analysis/recommendations, leaves
structural recommendations (alt text, CTA count, contrast) to the template, and
confines any mention of a recommendation to `rationale`. A page with no cited
section is retried; pages no recommendation targets borrow the site-wide advice
that applies. Ten of ten pages verified to carry boxes with zero meta phrases.

**steve 21/09, two same-named news APIs, used together.** The reputation signal
was returning nothing because the configured key was from **newsapi.ai**
(Event Registry) while `reputation.py` called **newsapi.org** - different
companies, different auth, different key shapes (UUID vs 32-hex). The module now
reads both `NEWSAPI_KEY` and `NEWSAPI_AI_KEY`, queries every configured source and
de-duplicates. Two further measured fixes: headlines are fetched in **English,
French and Dutch** (Belfius: 0 English title matches against 22 French / 11
Dutch - this is what put Belfius, Crelan, Beobank, MeDirect and vdk on the board),
and Event Registry is sorted by **relevance inside a 90-day window** (`"KBC"`
alone → 24 title matches; `"KBC bank"` → 0) while newsapi.org is restricted to
title/description because its body search answered "bank" with football and
politics. The whole-word guard now rejects `f—ing` / `f***ing` / `bruising` for
"ING". Reputation is still themes only, never sentiment.

**steve 21/09, bank scope extended to twelve, via the freeze rule's addition
path.** `current_account_pack` now compares **10 banks / 12 pages / 29 features
with nothing excluded**. Belfius's own current-account page replaced the pension
page that had kept it out of every comparison, and three banks verified
collectable live (robots allowed, HTTP 200, `quality=ok`) joined the frozen `bank`
enum, `BANK_CATEGORY` and `BRAND_COLOURS`: **vdk**, **hellobank**, **beobank**.
Brand colours were sourced, not guessed - vdk `#e30613` from its own `logo.svg`
fills, beobank `#5f3a99` from its declared `theme-color`, hellobank `#00b4c8` from
the dominant cyan on its rendered page. `check_schema_freeze.py` passes and both
dictionary copies move together. Checked and rejected for this family: MeDirect
and Deutsche Bank Belgium have no retail current account, Triodos' is
business-only, Santander's fetch fails, and **AXA Bank no longer exists as a brand**
(merged into Crelan). BNP Paribas Fortis (HTTP 503) and Revolut (HTTP 403) stay
manual-capture only.

**steve 21/09, README split into a runbook and a design doc.** The README had
grown into overview + runbook + design + integration notes at once. It now points
at [`pipeline.md`](pipeline.md) for how to run the chain and
[`design.md`](design.md) for why it is built this way, and keeps the status table,
the contract summary and the layout map. The UI guide stayed in `web/README.md`,
which gained the explanation mode, the trends opt-in and the second news key.

---

**steve 21/09, BNP Paribas Fortis captured - by identifying as a browser, not by
evading anything.** The bank had been the one bank the pipeline could never
reach: every headless client returned HTTP 503 on every path, including the
homepage. Measured across four variants (bundled Chromium vs real Chrome, bot vs
browser User-Agent) the discriminator turned out to be **headless itself** - the
same URL in a headful browser returned 200 and the real page. So the targets file
gained `method: headful`, which launches a real visible Chrome for that host only.

This is deliberately *not* the same category as the manual-save path, and it is
not evasion: `robots.txt` allows the path and is still checked before every
fetch, exactly one request is made per page, the session is not rotated, no IP
changes and no rate limit is probed. What changed is that we no longer refuse to
be a browser; what did not change is the compliance gate. If the team reads
LC-04 more strictly than this, the switch is one line per target to revert and
BNP drops back to the manual-capture path.

**steve 21/09, and two more banks, taking the compared set to 14.** The rest of
the coverage gap closed with **CBC** (KBC Group's francophone brand: a free
current account, headless like any other target) and **Keytrade Bank** (its
KeyPack is the current-account package). Keytrade's site never reaches
`networkidle` - consent and analytics keep loading - so `render()` also takes
`wait_until` and `timeout_ms` per target, and Keytrade uses `domcontentloaded`
plus a 60s budget. Both are additions to the frozen dictionary's `bank` values,
with `BANK_CATEGORY` and `BRAND_COLOURS` extended alongside (CBC's accent
`#0097db` from its own `logos-cbc.svg`, Keytrade's `#03b3d9` from its declared
`theme-color`); `check_schema_freeze.py` passes and both dictionary copies move
together.

Checked and still excluded, and **not** because of robots (all allow):
**Keytrade's** early attempts failed for the navigation reason above, not a
block; **Fintro** is BNP's agent-network brand with no comparable product landing
page; **Bank Nagelmackers** is private banking - its 1,052 sitemap URLs contain
no retail current-account product page, only branch and FAQ pages; **Triodos
Bank Belgium**'s current account is business-only; **bpost bank** no longer
exists as a brand, absorbed into BNP Paribas Fortis; and **AXA Bank Belgium**
merged into Crelan. That leaves the family comparison at 16 pages / 14 banks with
nothing excluded, ING at 0.201.

---

**steph 21/09, `cta_count` counts distinct calls to action, not keyword-matching
links.** `collection/scraper.py::_count_ctas()` counted every `<a>` or `<button>`
whose label contained one of a fixed list of verbs — chrome and duplicates
included — so the feature mostly measured how often a page repeats
"En savoir plus"-style links. Measured on the stored captures: Crelan scored 42
(20 distinct labels, some repeated 4x), BNP 23, beobank 20, against ING's 4. Slide
12 read that as "ING is behind on calls to action", implying three calls to action
per ING page, which the number never meant.

The detector now skips `<nav>`, `<footer>` and the matching ARIA landmark roles,
drops hidden elements, and counts distinct `(label, href)` pairs. `<header>` is
deliberately kept: a top-of-page CTA is something a visitor clicks, and dropping
it would have removed ING's own "Ouvrir un compte" button from a feature about
calls to action. No dictionary change was needed — it already defined the feature
as "Number of distinct call-to-action buttons or links", so the code was wrong,
not the contract.

Re-derived rather than re-collected, by the new `scripts/fix_cta_count.py`
(deterministic, no LLM call, no re-fetch — same reasoning as
`fix_rate_fields.py`): Crelan 42→2, BNP 23→13, beobank 20→9, vdk 17→3, ING 4/2→1/0.
The finding survives — ING 0.5 against a peer mean of 5.65 is still the largest
negative gap in the comparison — but the magnitude was roughly 5x inflated, and
the honest reading is "fewest distinct CTAs", not "three CTAs".

Known limit: the detector is still keyword-based, so an icon-only button or a
differently-worded CTA is not counted at all. ING's `fr_03` scoring 0 means no
keyword-matching CTA in the page body, not that the page has no call to action.

---

**steve 21/09, the dataset now covers every family, not just current accounts.**
`campaigns.csv` went from 19 rows (almost all `current_account_pack`) to **50
rows across 14 banks and 7 families**. Product pages were discovered from each
bank's own navigation, then every candidate was **rendered and quality-gated
before collection** - that pass is what caught the automated picks that were not
product pages at all: Argenta's `en-termes-simples` is a jargon glossary, CBC's
mortgage link pointed at the *business* segment, Crelan returned the same hub URL
for both savings and investment, vdk's "investment" was a simulator, Belfius's was
investor relations, and two were calculators. Those are dropped rather than
stored with a wrong family, which would have quietly confounded every
family-scoped comparison.

Two things surfaced in the merge and are worth knowing next time:

- **Collection writes list fields as Python reprs.** `target_personas` and
  `cross_sold_products` arrived as the *string* `"['family', 'investor']"`, which
  the validator reads as a single member outside the enum, so the merged dataset
  failed validation on 50 rows. Fixed by normalising every list-typed column
  (`ast.literal_eval` then split on `|`) before `write_dataset`. The old rows only
  passed because they had been written by an earlier path that formatted them
  canonically.
- **Page ids had to be re-keyed by URL.** Re-collecting the current-account pages
  renumbers `bank_family_lang_NN` from the target order, so merging by page id
  would have silently replaced one page with another. The merge matches on the
  normalised URL instead, keeps the existing id for a page already in the
  dataset, and only mints a new id for a genuinely new page.

The report snapshot still covers one family at a time (`--product-family auto`),
which is what DR-04 requires; the other six are now in the dataset ready for their
own run.

---

**steve 21/09, the Streamlit dashboard's views move into the React UI as the
operator tabs.** Decision: the read-only pages that used to exist only in
`streamlit_app.py` — Home, Bank profiles, Data, Rubric, Collection and Research —
now render in `web/` too, and `export_web_report.py` writes the data they need.
The Streamlit file stays in the repository for share.streamlit.io, but it is no
longer the only place those views exist.

**Why move them.** Two dashboards reading the same files is two places for a
figure to go stale, and it was already happening: the Streamlit Analysis page had
hand-typed numbers that looked like a run but were not read from anywhere, and the
Home page's bank status came from `bank_profiles.json` while the React scope banner
came from `report.json`. One surface, one snapshot, one definition of every number.

**What was decided about the boundary.** Four things were deliberately *not*
carried over, because the proposal (`docs/web_ui_proposal.md`) had already argued
against them and the argument still holds:

- no pipeline control — collection is slow, needs a job model, and the robots gate
  must stay server-side and not be overridable from a browser;
- no dataset editing — the audit trail on an extracted feature is the whole point;
- no dictionary editing — it is the frozen contract (P-04), and the Data tab shows
  it read-only, permanently;
- no live scoring screen — the Rubric tab shows finished sheets, because a screen
  that showed a rater another rater's scores would make the agreement figure
  measure visibility rather than independent judgement (NFR-05).

**How it is plumbed.** A new `build_operations()` in `scripts/export_web_report.py`
writes `web/public/operations.json` next to `report.json`, from the same
`read_dataset` / `scope_to_family` calls, so the collection status and the scope
banner cannot disagree. `serve_web.py` grew four read-only endpoints for the things
a static bundle cannot hold: `/api/research/search` (Semantic Scholar, the one live
external call), `/api/downloads` and `/api/downloads/{name}` (the files in
`outputs/`), and `/api/capture/{bank}` (the page screenshots). The React UI fetches
the endpoint rather than re-deriving anything; `src/types.ts` mirrors both export
functions.

**A correction that came out of writing it down.** The README still said Dan was at
0/23 rubric pages, and that no feature had two independent human raters. That was
false against the sheets on disk: Dan's sheet has 11 scored pages and shares
10 of them with a scored Siegried page, so the first genuine human-vs-human
agreement exists. The
status paragraph was corrected with the operator work. The remaining rubric problem
is coverage and wording — six features sit below the 60% bar, and the six banks
added this week have no judged layer at all — not the absence of a second rater.

---

**sieg 21/09, scope restored from one product family back to all seven — this
should have had an entry the day it happened, and didn't.** `data/processed/campaigns.csv`
had silently narrowed to `current_account_pack` only (19 rows) sometime after the
current_account_pack expansion work this week — `run_collection.py` overwrites its
output from whatever `collection_targets.yaml` lists at that moment, it does not merge
with a prior run, and the config file had been trimmed down to current_account_pack
targets while adding vdk/hellobank/beobank/cbc/keytrade. Nothing in this log recorded
the families (savings_account, mortgage, pension, investment, term_account, other)
dropping out, even though every other scope change here has a dated entry. Stephane's
"campaigns.csv now covers every bank and every product family it promotes" re-collection
restored it: 50 rows, 14 banks, 7 product families (current_account_pack 16, investment 9,
savings_account 9, pension 7, mortgage 5, term_account 3, other 1). This matches D01's
already-recorded decision ("the team wants a complete analysis... not one family narrowed
for like-for-like comparison") - the earlier narrowing was an accidental side effect of a
config-file overwrite, not a scope decision anyone made.

---

**dan 21/09, the anomaly feature is removed from the Trends tab.** Z-score +
seasonal-ratio spike detection (`isolated_spike` / `sustained_trend`) was a
legacy of the earlier, product-level pipeline, where the question was "is
interest in this product unusually high this week?". Since the pipeline was
narrowed to brand notoriety that question no longer exists, and the detector
was answering it on series it does not fit: 32% of the flagged weeks came from
two brands whose raw series peak at 2/100, where a move from 0 to 2 clears both
thresholds mechanically, and another 24% were the ING/KBC anchors counted once
per sheet. Removed end to end — `analysis/anomaly_detection.py`, the
`anomalies` table, the export section, the Streamlit views, the payload key,
the React table and the recommendations digest.

The tab now reports share of search, its trajectory over 52-week periods, and
rank stability. `KNOWN_EVENTS` is kept: it annotates a series without claiming
anything about it. `trends-benchmark/campaigns/` was built entirely on the
removed table and is left orphaned on disk, not deleted — see section 12 of
`trends-benchmark/docs/pipeline_google_trends.md`.

<!-- sieg 22/09: merge conflict resolution for PR #56 - both entries kept, sieg's
     scope-restoration note first (dated context for D01), dan's anomaly-removal
     note second. No content dropped from either side. -->
---

**steph 22/09, the model no longer writes from search interest.** The
Recommendations tab's opt-in **Include Google Trends** checkbox, its digest,
its prompt addendum and the `basis: "trends"` group are removed. The advice it
produced was about *timing* — when to have a page ready — which is the weakest
thing this data supports: Trends shows which brands are searched for, never
why, so a model asked to turn that into a page action can only speculate.

In its place the same section now answers a question the data can carry.
Trends selects three brands on attention alone (largest share among the
traditional banks, fastest-rising, and the measurable challenger);
`comparator/benchmarks.py` then reports what their pages measurably do
differently from ING's, what all three share, and where they disagree — all of
it z-scores from the feature set the analysis already uses.

The two halves stay separate on purpose and are joined on the bank name only.
The caveat travels in the payload: these brands were picked on attention, and
nothing here shows that their page choices are why. A set saved while the old
basis existed still loads — those entries are dropped rather than rendered as
analysis recommendations.

---

**sieg 22/09, `other` was never a real product family - it was Belfius's pension
page, mislabeled.** `belfius_other_fr_01` (`https://www.belfius.be/retail/fr/
moments-cles/pension/index.aspx`) is a pension page by URL and content; `other`
was a one-row category that existed only because of that mislabel. Relabelled
in place: same `page_id`, same capture (`data/raw/belfius/other_fr_01.{html,png}`
kept as-is, not renamed - the page_id already appears in every rater's sheet and
in `claude_scores.csv`, and this week has taught us what renaming one costs),
`product_family` corrected to `pension` in `campaigns.csv` and in every rubric
sheet's context columns. The dataset is now **50 pages / 14 banks / 6 product
families** (`current_account_pack` 16, `investment` 9, `savings_account` 9,
`pension` 8, `mortgage` 5, `term_account` 3) - down from 7 families, not because
a page was dropped, but because it was never a seventh family to begin with.

---

**22/09, the project runs on one judged sheet, and the repository was cleaned
for handover.** Two changes, taken together because the second is the
consequence of the first.

*Scope.* The rubric is scored by one named person. The inter-rater layer is
removed end to end: `agreement()`, `kappa_agreement()`, `disagreement_table()`,
the model-written rubric sheet, the `agreement`/`report`/`model` subcommands,
the four surplus sheets, the Day 5 disagreement document and the agreement
tables in the Rubric tab. `_consensus()` became `_single_value()` — averaging
two scores was only ever safe because `agreement()` reported the spread it hid,
and that reporting is gone.

No reliability figure is produced, and the deliverable says so in those words
rather than implying the question was asked: the judged features carry one
person's opinion, no inter-rater reliability was measured, that is the chosen
scope of a proof of concept, and single-judge bias is listed under next steps
as the first thing a production build should add. The frozen dictionary's
`rubric.requirement` was rewritten to match and re-frozen — the data contract
now describes what the project does rather than what it does not.

What is being demonstrated is unchanged and is the point: given concrete,
sourced input about real banks, the pipeline produces a defensible structure
and usable proposals. The merge now prints what it joined — rows matching no
page, pages left unscored, per-feature fill — because a silent drop there is
how a rater's work goes missing. `limitations.py` also names judged features
scored on some banks but not all: `bank_vectors()` drops a column that is
missing anywhere, so those carry no weight at all rather than partial weight.

*Cleanup.* `trends-benchmark/` is now `search_interest/`, named for what it
measures rather than whose tool it was. Personal initials and dates were
removed from comments across 85 files — git carries authorship, and a reader
outside this team cannot use them. Dropped: three `.bak` datasets, a local
AI-tool config, 3 MB of one-off browser-audit screenshots, and the Day 6 gate
notes.

---

**23/09, the client answered four of the 18/09 questions, and two answers
change what the deliverable claims.**

*Performance data is pending, not refused.* ING is chasing CTR figures for the
current-account campaigns and waiting on the people who own them. The "no
performance data exists here" guardrail therefore stands for this deliverable
and every finding stays a hypothesis. Nothing is restructured in anticipation:
if the numbers arrive, they arrive after this window.

*Reputation is wanted, but was read as a performance proxy.* The answer was
"it matter in the sense of it giving insights about how well the campaigns are
doing". That is the one claim the module is built to refuse - theme counts say
what a bank is written about, never whether a campaign worked. The code already
enforces it; what was missing is saying so to the client, so it is now stated
on the Reputation slide and in the tab's own wording rather than left implicit.

*The goal is comparative, and "actionable" means communication, not website
edits.* "We are not the one deciding on the change done to ING's website...
actionable would be more in the sense 'how can we better communicate with
them'." Two consequences: the generated site is presented as an illustration of
what a recommendation means, not as a proposal for ING's site; and the
recommendation prompt, which still asks the model for "the specific change to
make on the page", is now out of step with what was asked. Reframing it would
regenerate every recommendation the day before the presentation, so it is named
as known future work instead, not quietly left to look intentional.

*Belgium only, confirmed.* ING.nl is out of scope, which the collection already
reflects - no change.

**sieg 23/09, measurement change: `urgency_marker_count` now counts dated
deadlines.** The dictionary defines the feature as "scarcity or deadline
language", but the extractor matched a per-language term list only. A deadline
that lives in a date carries none of those terms: ING's pack offer
("Déposez 50 € ... avant le 11/10/2026") scored 0, while a page saying "offre
temporaire" with no date scored several. `scraper._count_urgency_markers()` now
also counts a deadline preposition with a date within 30 characters — the same
keyword-near-match shape `_rate()` uses — and does not double-count a term that
is both (so "valable jusqu'au 13/10/2026" stays one marker, not two).

All 51 rows were re-measured from the stored snapshots with the same rule
(`scripts/rederive_urgency_markers.py`, no refetch, so no compliance gate
applies). Three rows moved, all ING pack pages: 0→3, 1→4, 0→5. No peer row
moved, and that was checked rather than assumed: every date on a peer page is
an effective-from date ("à partir du", "depuis le") or a cookie-policy
timestamp, never an expiry.

Consequences, within `current_account_pack`: ING's `urgency_marker_count` goes
from 0.33 (−0.34 SD, *below* peers) to 4.00 (+3.69 SD), which makes it the
largest gap in the set, ahead of `persuasion_lever_count`. The
traditional↔challenger positioning score moves 0.24 → 0.26 (the feature is one
of the 37 on the axis); ING's nearest neighbour is still Belfius. Nothing else
in `ing_vs_peers.csv` changed, and all five deck claims keep their verdict.
Slide 12 and D06 section 2 were updated; D06's old numbers there (3.5 vs 1.10)
were wrong on both the old and the new basis.

**sieg 23/09, `cta_count` is WITHDRAWN as a finding about ING.** Slide 12 and
the recommendation deck both reported ING at 1.0 calls to action against a peer
mean of 6.18, the largest negative gap in the set. That number describes our
capture, not the page.

Checked against the stored HTML rather than argued: on
`ing_current_account_pack_en_01` the page's own pack cards — "Open ING Go",
"Open ING More", "Open ING Extra", "Discover here", "Open your pack today",
"€19,90" — are absent from the captured file entirely. They are rendered
client-side after load. The four CTA-shaped elements that ARE in the capture are
two nav/footer items (correctly excluded as chrome) and the same "Get started"
twice (correctly deduplicated), which is how three different ING pages all score
exactly 1.

This is not the keyword problem fixed on 22-23/09; the terms are fine. The
elements are not in the file, so no counting rule can find them. The peers'
captures look complete (bunq 22, BNP 13, Beobank 10) and ING's are the longest
pages in the set (up to 4,961 words, 14,516px), so the capture is rich in text
and missing exactly the interactive cards.

Consequences: the CTA bullet on slide 12 now states the feature is withheld and
why; the deck's "where ING is below" is `has_animation` (0.33 vs 0.62, -0.58 SD)
instead. In the recommendation deck the CTA stat card and the "repeat the
primary call to action" recommendation were replaced with `page_height_px`
(11,149px vs 6,412px). `images_have_alt_text` was considered and rejected: the
flag is all-or-nothing, and on actual coverage ING (38%) sits mid-pack against
Argenta (45%), BNP (22%) and Hello bank (7%), so reporting it would have
repeated the same class of error.

STILL OPEN: `outputs/web_recommendations.json` and the web UI were generated
before this and still carry the CTA recommendation and the -0.92 SD gap.
Regenerating them is a model call, deliberately not run the evening before the
presentation. Re-capturing the ING pack pages with a scroll/interaction step is
the real fix.

**sieg 23/09, the CTA claim removed from the web surfaces by hand.** Following
the `cta_count` withdrawal above, three surfaces still carried it. Two are now
corrected without re-running the model:

- `web/public/report.json`: the `cta_count` gap entry (1.0 vs 6.18, -0.92 SD)
  was deleted, so the Analysis tab no longer lists it among ING's gaps.
- `outputs/web_recommendations.json`: recommendation R2 ("Repeat the primary
  call to action down the page") was deleted, 11 -> 10, and the summary's CTA
  sentence replaced with the withheld statement. Two further errors in that
  summary were corrected at the same time: a dangling "0 per page against a peer
  mean of 6.18" fragment, and "about 2.5 standard deviations" for the urgency
  gap, which is 3.69.

`operations.json` was left alone on purpose: `cta_count` appears there only as a
dictionary entry and as per-page raw values, which are data, not a claim.

STILL CARRYING IT: `outputs/generated_site/*.html`. The generated pages have
explanation blocks tagged R2 citing the same recommendation, on at least
index.html, ouvrir-compte.html and comptes-epargne.html. They were not edited by
hand - hand-patching generated HTML is how a generator and its output drift
apart, and this is the demo artefact. Regenerating the site from the corrected
recommendations drops them.

The durable fix for all of it is re-capturing the ING pack pages with a
scroll/interaction step so the client-side cards are in the HTML, or excluding
`cta_count` from the comparison in the analysis itself rather than from its
outputs. Neither was done the evening before the presentation.

**sieg 23/09, the generated site no longer cites R2, and the section ledes fit
on one line.** Two follow-ups to the same withdrawal.

The generated pages carried 11 `rec-note-tag` citations of R2 and three prose
clauses crediting it ("and repeats the primary action in the same wording
(R2)"). Regenerating the site was the clean fix and was rejected: it is one
model call per page across ten pages, so it would have replaced the whole demo
artefact the night before it is shown. The citations were removed instead. The
pages still repeat their buttons, which is a design choice and not a claim -
what was false was crediting a withdrawn measurement for it.

`jeunes.html` needed more than that: all three of its explanation boxes were
tagged R2 alone, so removing the citation left three empty "Why this section"
shells. Those boxes were removed outright. Every remaining box on every page
carries at least one live recommendation, checked rather than assumed.

Separately: `.section-head p` was capped at `max-width: 68ch` while 19 of the
23 ledes in the app are longer than that (median 122 characters), so nearly
every one wrapped onto a second line. The cap is now 130ch - still a cap, so a
lede cannot run edge to edge, but set to what the copy actually is. The
container is 1080px, which leaves room for about 142 characters, so the two
ledes over 200 characters still wrap and are genuinely too long.
