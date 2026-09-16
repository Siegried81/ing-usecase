# D-01 — Scope and compliance note

sieg 15/09, first draft. Deliverable D-01 per PRD section 13 ("Scope and
compliance note" — banks/product/pages/language selected with justification,
what was excluded and why, robots.txt/sitemap findings, and the "what we
considered acceptable, and why" statement). Audience: both decks.

Status: draft, based on what is actually in the repo today (15/09).

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

**As of today, actually configured/collected** (`scripts/collection_targets.yaml`,
`data/processed/real_captures.csv`):

| Bank | Category | Real HTML captured | In `real_captures.csv` | Model-assisted fields |
| --- | --- | --- | --- | --- |
| KBC | traditional | yes | yes | yes (16/09) |
| N26 | challenger | yes | yes | yes (16/09) |
| Belfius | traditional | yes | yes | yes (16/09) |
| ING | traditional | yes (Dan, 16/09) | pending — Dan extending the dataset | - |
| BNP Paribas Fortis | traditional | configured, not yet captured | no | - |
| Revolut | challenger | configured, not yet captured | no | - |
| Argenta | traditional | not yet configured | no | - |
| Crelan | traditional | not yet configured | no | - |
| bunq | challenger | not yet configured | no | - |

sieg 16/09: re-ran `scripts/run_collection.py` today — KBC/N26/Belfius now
have both automatic and model-assisted fields filled. Dan captured ING
separately and is extending to the rest of the list.

- **Headless rendering** — not available yet; geometry fields
  (`page_height_px` and three others) stay empty on every real row.

**`scripts/collection_targets.yaml`** — Dan confirmed 16/09 he is taking
ownership of this today (was previously `[TO CONFIRM]`, still says "not the
final team scope" in its own header as of this writing). D-02 can be called
advanced once the file itself is updated to say so.

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
this: `current_account_pack` (KBC, N26, configured for Revolut),
`savings_account` (ING), `mortgage` (BNP Paribas Fortis), `other`/pension
(Belfius). `category_comparison`/`check_deck_claims` and any
like-for-like read (DR-04) should compare within the same `product_family`
value, not across the full dataset.

## 3. Compliance / robots.txt findings

`collection/compliance.py::assert_can_fetch()` checks `robots.txt` live
before every fetch (page HTML and, since today's fix, the hero image too —
see the compliance-gate fix on `feat/sync_main`) and fails closed: if
`robots.txt` can't be read at all, the URL is treated as not allowed. Every
row in `real_captures.csv` has `robots_allowed=True`.

Per-domain reasoning (sieg 15/09, read each domain's live `robots.txt`
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

- **Argenta, Crelan, bunq** — not yet configured for collection. Not excluded
  on principle, just not reached yet (`[TO CONFIRM]` with Dan: still planned,
  or dropped for capacity per the PRD's "narrowing is permitted, provided it's
  stated and argued"?).
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
