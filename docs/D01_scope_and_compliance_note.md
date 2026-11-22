# D-01: Scope and compliance note

Deliverable D-01 of the brief: which banks, products, pages and language are in
scope, what was left out and why, the robots.txt findings, and what we
considered acceptable. Figures below come from `data/processed/campaigns_scored.csv`.

## 1. Scope

- **Banks (14).** Traditional: ING, KBC, CBC, Belfius, BNP Paribas Fortis,
  Argenta, Crelan, VDK, Beobank, Hello bank!. Challengers: Revolut, N26, bunq,
  Keytrade Bank. The split lives in `src/comparator/banks.py::BANK_CATEGORY`.
  Hello bank! counts as traditional (BNP Paribas Fortis's digital brand), and
  Keytrade as a challenger (branchless since 1998). Belfius is in because
  capacity allowed it (open question Q-02).
- **Pages (51).** Every product family a bank promotes: `current_account_pack` 18,
  `investment` 9, `savings_account` 9, `pension` 8, `mortgage` 5, `term_account` 2.
  The comparison runs on `current_account_pack` only, because a comparison is
  valid within one `product_family` (DR-04). Revolut and bunq have one page each
  (app-first sites).
- **Language.** French is the reference language (Q-07). The dataset holds 48
  French pages, 2 English and 1 Dutch. Numeric `within_language` features are
  not compared across languages (see `config/feature_dictionary.yaml`).
- **Capture.** 45 pages by headless render, 6 by headful render
  (`method: headful` in `scripts/collection_targets.yaml`, for BNP Paribas Fortis
  and Keytrade). All 51 have `robots_allowed=True` and `capture_quality=ok`.
  Raw HTML and screenshots stay in `data/raw/` on the machine that collected them
  (not versioned).

## 2. Left out, and why

- Checked and rejected for the current-account family: MeDirect and Deutsche
  Bank Belgium (savings and term only), Triodos (business accounts only), CPH
  (savings, term, mortgage), Santander Consumer Bank (TLS handshake fails). AXA
  Bank no longer exists as a brand: it merged into Crelan.
- Social media sentiment: deferred, to avoid scope creep (R-07).
- ING campaign performance data (clicks, acceptance): assumed unavailable (Q-04).
  The comparison is descriptive and claims no effect.
- Mobile viewport: every page is captured once at 1440x900 desktop. Features
  that would need a mobile render say so in the dictionary.
- No domain was excluded on compliance grounds.

## 3. robots.txt findings

`collection/compliance.py::assert_can_fetch()` reads robots.txt live before every
fetch, the hero image included, and fails closed: if robots.txt cannot be read,
the URL is not fetched. The user agent is
`BeCode-ING-CampaignComparator/0.2 (student POC, contact: team)`.

Rules read per domain when the targets were chosen (September 2026):

- **Revolut**: no `Disallow` covers `/fr-BE/bank-account/`.
- **KBC**: `Disallow` on `/*/$`, `/site/*`, `/PBL/CC028/*`, `*/aemform.iframe.html`; none match our page.
- **N26**: `Disallow: /` applies only to a list of named bad-bot user agents, not to `*`.
- **Belfius**: about 60 `Disallow` rules (contests, PDFs, simulators, login area); none match.
- **ING**: only `Disallow: /video`.
- **BNP Paribas Fortis**: `Disallow` on `/site/`, `/images/`, `/local/`, `/PAPL-*/`, `/pas/`, `/promo/`, `/de/*`, `/*.pdf`. The `/images/` rule is why the image URL is checked as well as the page.

## 4. What we considered acceptable

- Fetch a page only after its robots.txt allows it, checked at fetch time.
- Capture a bank's own public marketing page only: no login, no customer or personal data.
- Keep competitor logos and photos locally for feature extraction. Do not
  redistribute them or reuse them in generated campaigns.
- Name the limits instead of leaving them implicit: one language per comparison,
  one pinned model per extraction, one fixed viewport.

## 5. Open questions

The brief's questions were closed with working assumptions, not ING answers.
Two still need a real answer:

- **Q-05**: can the repository be public? Decided "internal only" by the team,
  never confirmed by ING.
- **Q-06**: does ING prefer a tool or process for web collection? Never asked. We
  applied our own reading of LC-04 ("no bot-detection evasion"). The README's
  remark that getting past a CDN block "would need IP rotation" is that
  reading, not a quote from the brief.
