# D-01 — Scope and compliance note

first draft. Deliverable D-01 per PRD section 13 ("Scope and
compliance note" — banks/product/pages/language selected with justification,
what was excluded and why, robots.txt/sitemap findings, and the "what we
considered acceptable, and why" statement). Audience: both decks.

Status: draft, based on what is actually in the repo as of 18/09 (19/09 weekend, before Day 6 gate).

**** table below and the Argenta/Crelan/bunq bullet in section 4
were still describing 15/09 while collection moved past them - all 9 banks
now have a real capture. See `docs/decisions.md` for the dated record of
what changed and when.

**open questions status (PRD Appendix, Q-01 to Q-07).** Every one
of these was closed with a **working assumption**, not an ING-confirmed
answer - the PRD's own wording. Ahead of any ING meeting, here is which ones
still need a real answer vs. which are fine as internal calls:

TO VALIDATE TOGETHER

**14h meeting plan (10 min + 5 min Q&A).** Q-01, Q-02 and Q-04
closed by the team today, dropped from the table below - no need to raise
them with ING. **The one question for the 5 minutes of Q&A is Q-05** (repo
public or not).

Also flagging, not from the PRD list: **is this afternoon's 10+5 min slot
the actual Day 10 delivery, or a shorter interim check-in?** The brief is
explicit that business (D-06) and data/technical (D-07) are two separate
mandatory presentations - "one set of slides serving both does not meet the
requirement." Ten minutes total cannot cover both properly, and Day 10
(confirmed next Friday, 25/09) is where the plan actually schedules "deliver
business session, deliver technical section" as two things. Worth a quick
confirm so today's content matches what ING expects from this slot.

| Q# | Question (PRD) | Where in this file | Status |
| --- | --- | --- | --- |
| Q-05 | Can deliverables/repo be public? | §4, line ~134 | **the one question for this afternoon's Q&A** - decided "internal only" ourselves, never confirmed by ING |
| Q-06 | ING-preferred/approved tooling or compliance process for web collection? | not covered here | never asked - we applied our own reading of §9 (LC-04, "no bot-detection evasion") instead |
| Q-07 | Which language is the reference? | §2, line ~69 | resolved, French chosen and documented - nothing to ask |

**correction on Q-06/LC-04.** "IP rotation" does not appear
anywhere in the PRD - checked the source text directly. LC-04's actual
wording is "no bot-detection evasion" (among no login, no CAPTCHA solving,
no rate-limit evasion). "Getting past BNP's CDN block would need IP
rotation, which LC-04 forbids" (README, "When a site will not serve the
pipeline") is the team's own reasonable reading of that clause applied to
BNP's specific block - not a PRD quote. Worth citing LC-04's real wording if
this comes up with ING this afternoon, and a good moment to get their read
on whether that interpretation matches what they meant (ties into Q-06).

## 1. Banks in scope

Working from the PRD's own candidate list (section 2 / Appendix A):
traditional — ING, KBC, BNP Paribas Fortis, Argenta, Crelan; challenger —
Revolut, N26, bunq. The PRD leaves Belfius ambiguous (Q-02: "appears in the
deck comparison but not in the written bank list") with the working
assumption "include only if capacity allows."

**Decision:** Belfius is included — it already has a real captured page
(`data/raw/belfius/`) and appears throughout `config/feature_dictionary.yaml`
(e.g. the 100%-state-owned trust-signal example). Capacity allowed it, per
the PRD's own condition.

**refreshed from `data/processed/campaigns.csv` (the real
dataset that's actually in use today):**

| Bank | Category | Real capture | Robots allowed | Screenshot | Model-assisted fields |
| --- | --- | --- | --- | --- | --- |
| ING | traditional | yes (3 pages) | yes | yes | yes |
| KBC | traditional | yes (2 pages) | yes | **no** — file exists in `data/raw/kbc/` but not wired to a `screenshot_path` | yes |
| Belfius | traditional | yes | yes | **no** | yes |
| Revolut | challenger | yes | yes | yes | yes |
| N26 | challenger | yes | yes | **no** | **no** — LLM extraction missing entirely |
| BNP Paribas Fortis | traditional | yes | yes | yes | yes |
| Argenta | traditional | yes | yes | yes | yes |
| Crelan | traditional | yes | yes | yes | yes |
| bunq | challenger | yes | yes | yes | yes |

All 9 banks now have a real, usable capture (`capture_quality=ok` for all
12 pages) — the "not yet configured" state below is stale, superseded by
collection actually finishing. Every row's `collection_method` is
`manual_capture` (the browser-save path in the README's "when a site will
not serve the pipeline" section), not the live headless scrape — that
includes BNP Paribas Fortis, whose CDN-blocking issue (see
`docs/decisions.md`) is resolved this way, not by getting past
the block.

Two real gaps, not "not yet configured":

- **No screenshot for Belfius, KBC and N26.** Blocks the 4 vision-only rubric
  features for those banks (`accent_locations`, `text_image_layout`,
  `layout_archetype`, `mobile_first_design_signal`) — a rater has nothing to
  score them against. KBC's case looks recoverable (a screenshot file exists
  on disk, just not linked); Belfius and N26 need an actual capture.
- **No LLM extraction for N26.** Automatic non-model features are still
  present, but every model-assisted feature is empty for this bank.

- **Headless rendering** — still not available; geometry fields
  (`page_height_px` and three others) stay empty on every real row,
  unchanged since 16/09.

### Scope update — 10 banks / 12 pages, nothing excluded

Two things changed since the table above. **Headless rendering works in this
environment now** — every live capture carries `page_height_px` and the other
geometry fields (Belfius's current-account page, for example, reports 11,110 px),
so the "still not available, unchanged since 16/09" note above is superseded.
And the bank list grew, through the freeze rule's *addition* path rather than a
rename: new values inside the `bank` enumeration are additions, so
`check_schema_freeze.py` passes and both dictionary copies move together.

| Bank | Category | Live capture | Notes |
| --- | --- | --- | --- |
| ING | traditional | yes | 2 current-account pages + a savings page |
| KBC | traditional | yes | fr + nl |
| Belfius | traditional | yes | **new**: its own current-account page. Its only earlier capture was a pension page (`other`), which is what kept it out of every comparison |
| Argenta | traditional | yes | |
| Crelan | traditional | yes | |
| **vdk** | traditional | yes | **new**: `compte-vue-you-count`, robots allowed, 1222 words |
| **hellobank** | traditional | yes | **new**: BNP Paribas Fortis's digital brand, `compte-all-in-gratuit`, 861 words. Classified traditional for the same reason `cbc` is: the institution behind it is an incumbent |
| **beobank** | traditional | yes | **new**: `compte-go`, 2184 words |
| N26 | challenger | yes | |
| bunq | challenger | yes | |
| BNP Paribas Fortis | traditional | **no** | HTTP 503 from its edge; manual-capture path only |
| Revolut | challenger | **no** | HTTP 403; manual-capture path only |

The three new banks were added to `config/feature_dictionary.yaml` **and**
`.frozen.yaml`, `src/comparator/banks.py::BANK_CATEGORY` and
`src/comparator/collection/visual_features.py::BRAND_COLOURS`. Brand colours were
sourced rather than guessed: vdk `#e30613` from its own `logo.svg` fills, beobank
`#5f3a99` from its declared `theme-color`, hellobank `#00b4c8` from the dominant
cyan on its rendered page (consistent with the `#11BAD5`/`#4EC1D3` in its CSS).
`brand_colour_share` is meaningless without the right hex, so a guess would have
produced a confident wrong number.

**Checked and rejected for this family** (documented so nobody re-checks them):
MeDirect and Deutsche Bank Belgium offer savings/term only; Triodos' current
account is business-only; CPH is savings/term/mortgage; Santander Consumer Bank's
TLS handshake fails; and **AXA Bank no longer exists as a brand** — it merged into
Crelan, and axa.be now redirects to insurance. Keytrade Bank remains unresolved:
JS-rendered, and its 3,171-URL sitemap surfaces no retail current-account page.

### The dataset now spans every family each bank promotes

The comparison had been one family (`current_account_pack`) because that is what
the targets file listed. It now holds **50 pages across 14 banks and 6 families**:
`current_account_pack` 16, `investment` 9, `savings_account` 9, `pension` 8,
`mortgage` 5, `term_account` 3. (`other` 1 folded into `pension` -
`belfius_other_fr_01` was Belfius's pension page, mislabeled; see the note
below.) Product pages were discovered from each
bank's own navigation and every one was verified by rendering it before
collection — the automated picks included investor-relations pages, calculators
and a jargon glossary, all dropped (the list is in the 21/09 decisions entry).

`product_family` is still the comparison key (DR-04): the families are *stored*
together, and a comparison is only valid within one of them. Banks whose sites
publish fewer comparable landing pages contribute fewer rows — Revolut and bunq
have one each (app-first sites), Keytrade, N26 and Hellobank three.

### The three remaining gaps above are closed

The table at line 125-126 and the "two real gaps" list above it are now
stale, both superseded by later re-collection (dated between the "steve
21/09" sections above and today):

- **BNP Paribas Fortis and Revolut are both live-captured, not
  manual-capture.** BNP via `method: headful` (decisions.md, "BNP Paribas Fortis captured"); Revolut via the current
  `collection_targets.yaml` URL, a plain headless fetch. Every one of the 50
  current rows has `collection_method` in `{headless_render, headful_render}`
  — checked directly against `data/processed/campaigns.csv`, zero
  `manual_capture` rows remain.
- **Screenshots exist and are correctly linked for Belfius, KBC and N26.**
  Checked directly: every `screenshot_path` in the current dataset resolves
  to a real file on disk for all three banks.
- **N26 has full model-assisted extraction.** All 27 model_assisted features
  are populated for its 3 rows (`extraction_model=deepseek/deepseek-flash`);
  the only null is one legitimately-absent `cross_sold_products` value, not a
  missing extraction.

## 2. Product family and language

**Language:** French, consistently, across every page collected so far —
satisfies PRD Q-07 ("use one language consistently, state the choice"; word
counts, readability etc. are `within_language` per the dictionary and cannot
be compared across NL/FR/EN, see `bands.py`).

**Product family:** the PRD's working assumption (Q-03) was "term accounts
first, current-account packs second if capacity allows." **Decision:**
superseded — the team wants a complete analysis, so every product family a
bank actually promotes on its campaign pages is in scope, not one family
narrowed for like-for-like comparison. What is actually collected reflects
this: `current_account_pack` (ING, KBC, Belfius, Argenta, Crelan, vdk,
hellobank, beobank, N26 and bunq — the family the analysis compares),
`savings_account` (ING), `mortgage` (BNP Paribas Fortis) and `pension`
(Belfius's second page — its current-account page is the one that counts for
`current_account_pack`; this was labelled `other` until tonight,
corrected in place, same capture).
`category_comparison`/`check_deck_claims` and any like-for-like read (DR-04)
should compare within the same `product_family` value, not across the full
dataset.

## 3. Compliance / robots.txt findings

`collection/compliance.py::assert_can_fetch()` checks `robots.txt` live
before every fetch (page HTML and, since today's fix, the hero image too —
see the compliance-gate fix on `feat/sync_main`) and fails closed: if
`robots.txt` can't be read at all, the URL is treated as not allowed. Every
row in `real_captures.csv` has `robots_allowed=True`.

Per-domain reasoning (read each domain's live `robots.txt`
directly and checked it with the same parser `compliance.py` uses):

- **Revolut** (`fr-BE/bank-account/`) — no `Disallow` rule covers that path
  (no query string, not under `/api/`, not one of the blocked
  send-money/currency-converter paths). Documented in
  `scripts/collection_targets.yaml`.
- **KBC** (`.../ouvrir-un-compte-de-base.html`) — `Disallow` rules cover
  `/*/$`, `/site/*`, `/PBL/CC028/*`, `*/aemform.iframe.html`; none match our
  `.html` page.
- **N26** (`/fr-fr/compte-bancaire-gratuit`) — the `robots.txt` has a
  `Disallow: /` block, but it is scoped to a long list of named "bad bot"
  user agents (Wget, HTTrack, etc.), not to `User-agent: *`. Our identified
  user agent isn't in that list, so it's allowed.
- **Belfius** (`/retail/fr/moments-cles/pension/index.aspx`) — roughly 60
  specific `Disallow` rules (contest pages, PDFs, credit simulators, "my
  Belfius" login area); none match our page.
- **ING** (`/fr/particuliers/epargner`) — only `Disallow: /video`.
- **BNP Paribas Fortis** (`.../pret-hypothecaire`) — `Disallow` covers
  `/site/`, `/images/`, `/local/`, `/PAPL-*/`, `/pas/`, `/promo/`, `/de/*`,
  `/*.pdf`; none match our page. Note the `/images/` rule specifically — it's
  why the hero-image compliance fix (assert_can_fetch on the image URL too,
  not just the page) matters for this bank in particular.

No domain has been excluded on compliance grounds so far.

## 4. What was excluded, and why

- **superseded.** Argenta, Crelan and bunq are now captured and
  in scope like every other bank — nothing was excluded here after all, they
  were just collected later than the rest.
- **Social media sentiment** (candidate analysis dimension, PRD 11 bis) —
  deliberately deferred to a documented D-09 next step, not in v1 scope, to
  avoid the scope-creep risk R-07.
- **ING campaign performance data** (CTR, accept rates) — assumed unavailable
  per Q-04; comparison stays descriptive, no performance modelling.
- **A mobile viewport capture** — out of scope; every page is captured at one
  fixed 1440×900 desktop viewport (see `config/feature_dictionary.yaml`,
  `mobile_first_design_signal` and `page_height_px` notes). This is a known
  limitation, not a silent gap: features that would need a real mobile render
  are documented as such rather than guessed from the desktop screenshot.
- **Public repository / public competitor assets** — treated as internal
  only per Q-05; no public redistribution of competitor screenshots, HTML or
  brand assets outside the team.
- **English, alongside French and Dutch** — revisited and added
  (Stephane agreed). Checked first: ING's English site is a genuine full
  mirror of the French one (same packs, same pricing, same promos), not an
  expat-only subset, so this is the same audience in a third language, not a
  different one — no DR-04 comparability issue. The known cost, stated
  plainly: three languages roughly triples the manual rubric scoring
  workload (13 features × bank × language) against the original one-language
  plan, right before Friday's session. Team decision to take that on rather
  than narrow scope.

## 5. What we considered acceptable, and why

- A page is fetched only after its own `robots.txt` allows it for our
  identified user agent (`BeCode-ING-CampaignComparator/0.2`, see
  `compliance.py`) — never assumed, always re-checked live at fetch time, and
  the check fails closed on any read error.
- We only capture and analyse a bank's own public marketing page — no login,
  no scraping behind authentication, no personal or customer data (public
  campaign pages only, consistent with DR-01/DR-09).
- Competitor brand assets (logos, photos) are stored locally for feature
  extraction only, never redistributed or reused in the generated campaigns
  (step 5 guardrails) or in the public-facing decks beyond citation.
- One language, one measuring stick (one pinned LLM, D6) and one fixed
  viewport are all recorded as explicit, named limitations rather than left
  implicit — a reviewer can see exactly what the numbers can and cannot
  support.
