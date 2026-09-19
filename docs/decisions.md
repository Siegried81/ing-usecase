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
6. `comparator/research.py` (Semantic Scholar, keyless at low volume) - also
   not wired into the pipeline. The brief names this "Optionnel" and never
   defines a per-bank metric to compute from academic papers, so this stays a
   standalone `search_papers()` helper for whoever is writing the business
   narrative, rather than invented scope with no defined output.

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
