# D-06 — Business narrative, draft insights

> **CURRENT NUMBERS — 24/09 (evening), supersedes every figure and every update banner
> below.** Scope: 51 pages / 14 banks / 6 product families collected and
> scored; the comparison runs on the 18 `current_account_pack` pages, 14 banks,
> 33 comparable features (DR-04).
>
> | | ING | peers | gap |
> | --- | --- | --- | --- |
> | traditional↔challenger positioning | **0.41** | — | nearest neighbour Belfius |
> | `urgency_marker_count` | 4.00 | 0.64 | **+3.69 SD** — largest in the set |
> | `persuasion_lever_count` (rubric) | 5.00 | 1.67 | +3.68 SD |
> | `value_prop_clarity` (rubric) | 5.00 | 3.97 | +1.36 SD |
> | `fast_digital_onboarding_claim` | 0.67 | 0.15 | +1.42 SD |
> | `page_height_px` | 11,149 | 6,412 | +1.42 SD |
>
> `cta_count`, `cta_contrast_ratio`, `has_animation`, `animated_asset_count`
> and `has_comparison_table` are WITHDRAWN and must not be quoted, in either
> direction.
>
> `cta_count`: the stored HTML is the post-JavaScript DOM (`render.py` returns
> `page.content()`), so the cards ARE in the file — ING's pack page holds 144
> clickable elements. No counting rule proved defensible across the 14 banks:
> navigation, several links pointing at one target, and clickable product
> cards are marked up differently by each bank. See `decisions.md`, 23-24/09.
>
> `has_animation`/`animated_asset_count`: the rule is `"@keyframes" in html or
> "animation:" in html`, so it reports "this stylesheet declares an
> animation", not "this page moves". Across the 18 compared pages exactly one
> carries real motion — Revolut's, via a `<video>` element. Every other bank
> flagged animated has no video and no GIF, only CSS rules that may drive a
> spinner or a cookie-banner fade.
>
> `has_comparison_table`: the rule is `soup.find("table") is not None`, so it
> reports whether the page uses an HTML `<table>`, not whether it compares
> anything. Traditional banks mark their tariff grids up as tables; N26 and
> Revolut build the same plan comparison in CSS and score False, though their
> captured text carries the plan names and monthly prices all the same. The
> 0.57-against-0.00 split it produced, at d = -1.23, is a difference in HTML
> authoring style reported as a difference in strategy.
>
> Still true: don't hand-copy a number from this file into a deck. Pull it from
> `report.json` or a fresh `run_analysis.py --product-family auto` run.


rewritten 20/09 the night before the Day 6 gate. Written for the
business audience per the plan: what this means for ING, no method detail —
the "how" lives in D-07 and the code, not here.

> **for whoever builds the presentation from this draft.** Every
> number below (0.362, 0.183, 0.131...) is superseded again. Current state:
> full dataset is **50 pages / 14 banks / 6 product families**
> (`decisions.md`, "scope restored"; `other` folded into `pension`
> the night of 22/09, `belfius_other_fr_01` was mislabeled); `web/public/report.json`'s
> BO-02 positioning defaults to the `current_account_pack` family (16 pages,
> 14 banks) per DR-04, and reads **ING = 0.209** as of its last generation
> (`generated_at: 2026-09-21T18:11:00+00:00`) — re-run
> `export_web_report.py` before quoting it if the rubric merge changes after
> that. Don't hand-copy a number from this file into the deck; pull it from
> `report.json` or a fresh `run_analysis.py` run.

> **(second update).** The rubric consensus moved after the first
> update below: Stephane's sheet was filled for nine pages (machine-proposed and
> adopted), which shifted 15 columns — all five AIDA booleans on ten pages, the
> persuasion levers on six — and re-ordered ING's peer gaps. ING is now **0.131**;
> the leading gaps are figures quoted (+1.61 SD), student targeting (+1.53 SD) and
> **clarity of the offer (+1.30 SD, rubric-sourced, so it moved with the
> consensus)**. Treat the per-feature figures below as superseded by
> `report.json`.

> **— read this first.** The comparison has moved again since this
> draft: it is now **11 banks / 13 pages / 25 features with nothing excluded**
> (Belfius's own current-account page replaced the pension page that kept it out,
> and vdk/hellobank/beobank were added), and ING's traditional↔challenger score in
> `report.json` is now **0.183**, not the 0.362 quoted throughout below. The
> individual figures in this narrative were verified against the 20/09 snapshot,
> so treat them as **pending re-verification**, not as current. Re-run
> `docs/D06`'s numbers after the rubric session closes — the same re-check that
> caught three stale figures on 20/09.

Every number below is read live from `outputs/`/`report.json` on the dataset as
it stood when each line was written — nothing here is typed in from memory, and
nothing here has been hand-verified against an older run the way the previous
draft's numbers were.
Each insight is traceable to a specific feature and source page (NFR-03) and
stated as a hypothesis to test, never a cause — no performance data exists in
this project (PRD 5.2), so nothing here claims that a design choice produces
a better or worse result, only that it is different.

**What changed since the 16/09 draft**, for anyone comparing: the dataset
grew from 7 banks / 2 per group to 9 banks including Belfius, and a
scraper bug in `rate_value_pct` was found and fixed on 20/09 (it was matching
the first "N%" on a page — e.g. "100% en ligne" — instead of an actual rate;
see `docs/decisions.md`). The traditional↔challenger score for ING moved from
0.08 (16/09, 7 banks) to 0.45 (19/09, 9 banks, more features) to **0.362**
(20/09, same 9 banks, after the rate-field fix and re-merging the rubric
scores the fix hadn't reached yet — `scripts/rubric_sheet.py merge` has to
re-run after any change to `campaigns.csv`, not just `run_analysis.py`, or
`campaigns_scored.csv` and the web report stay on the older numbers). None of
the old draft's numbers are wrong for the run they described — they simply
describe an earlier, smaller or less accurate dataset. This version replaces
them rather than reconciling them line by line.

**21/09, the scope changed again.** The compared set grew from 9 banks to **11
banks / 13 pages / 25 features, nothing excluded**: Belfius now has a
current-account page (its earlier capture was a pension page in another family,
which is why it had been sitting out), and three newly-verified banks joined —
**vdk, hellobank, beobank** — through the freeze rule's addition path. ING's
score in the regenerated `report.json` was 0.183 then and is **0.131** now. This narrative's per-feature
figures were read off the 20/09 run, so they are one snapshot behind; the next
pass (after the rubric session) rewrites them against the 10-bank dataset.

---

## 1. None of the kickoff deck's five observations hold up anymore

The kickoff deck's eyeball impressions were tested against the current data,
one by one:

| Observation | Verdict |
| --- | --- |
| Belfius is pretty verbose | **Not testable** — every bank is in the same word-count band |
| KBC is straight to the point | **Not testable** — same reason |
| ING is the only traditional bank using animation | **Not testable** — the animation feature is withdrawn |
| ING no longer places text next to picture | **Not supported** — "beside" is still ING's most common layout |
| Revolut uses very little text | **Not testable** — same reason |

**What it means, and a limitation worth naming out loud.** The three
word-count claims are "not testable" for an unglamorous reason: **all 14
banks now land in the same word-count band ("long")**. The comparison had to
switch from a raw word count to a coarser, language-safe band once a second
and third language entered the dataset (a raw count silently drops out of a
mixed-language comparison entirely — see D-07) — and at this sample size,
that band no longer separates anyone. Of the two claims that don't depend on
word count, image/text layout is cleanly not supported; animation is not
testable — the feature that measured it is withdrawn (see above).
Net honest takeaway for the room: **zero of the five launch-deck impressions
survive measurement on the current dataset** — one is not supported on real
evidence, and four are not testable: one because its feature is withdrawn,
three because the current method can't yet tell these banks apart on length
(the band's edges stop at 600 words; every captured page carries 950 or more). That gap is itself worth a line in the room, not something to paper
over with a false "winner".

## 2. ING's page is the most urgent and the most persuasion-heavy in the set

ING's `urgency_marker_count` is 4.00 against a peer mean of 0.64 (+3.69 SD) —
the largest gap of any measured feature. Its `persuasion_lever_count` (5.00
vs peer mean 1.67, +3.68 SD) is the second-largest — this one is rubric-
sourced, from the one judged sheet. ING also claims fast digital onboarding at 0.67
against a peer mean of 0.15 (+1.42 SD) — the fourth-largest gap, behind
`value_prop_clarity` (5.00 vs 3.97, +1.36 SD).

**Read the urgency number with its history.** Until it was re-derived, this
figure said the opposite: 0.33 against 0.64, *below* peers. `urgency_marker_count`
was matched against a per-language term list only, and a deadline that lives in
a date carries none of those terms — "Déposez 50 € … avant le 11/10/2026" scored
zero, while a page saying "offre temporaire" with no date at all scored several.
All 14 banks were then re-measured from the stored snapshots with the same
extended rule, and only ING's three pack pages moved. That is not an artefact
of scoring ING more generously: every date on a peer page is an *effective-from*
date ("à partir du", "depuis le") or a cookie-policy timestamp, not an expiry.
On this dataset ING is the only bank whose captured pages carry a dated deadline
at all.

**What it means.** Three of ING's four biggest deviations from its peers
point the same direction: more deadline language, more persuasion technique
stacking, and a clearer value proposition than most of the comparison. Whether
that reads as energetic or as pressure to a real visitor is exactly the kind of
question this project cannot answer alone (no performance data) — but it is now
a precise, testable pattern, not a vague impression.

## 3. ~~ING is measurably darker than its peers~~, on a page that also invokes the least trust

> **the darkness half of this heading is WITHDRAWN - do not
> present it.** It was measured on a broken feature. `background_luminance`
> averaged the whole page strip, so on a long page it reported "how much
> white body copy is there", not how dark the page looks: ING's expat page
> scored 0.916 (near white) on a 14,516px capture whose first screen is
> black (0.521). Re-derived on the first screen instead
> (`scripts/fix_background_luminance.py`, 23/09), the ranking **inverts**:
> ING is the BRIGHTEST bank in the set at **0.666**, against a peer mean of
> **0.354**, with the challengers darkest by far (bunq 0.041, Revolut
> 0.088). The 0.198 below came from the older hero-image-only method. The
> trust-axis half of this section is unaffected and still stands.

ING's `background_luminance` was reported as 0.198 against a peer mean of 0.591
(-1.17 SD) — see the withdrawal note above; that figure and the reading built
on it are both superseded. On the AI Score axes (six signals, 0-10, each a mean of already-
measured features — see the Analysis tab for the exact formulas), ING scores
**digital 8.9** and **cross-sell 10.0** (every page pushes a bundled offer)
but **trust 0.0** — the lowest of the six axes by a wide margin, next to
**simplicity 2.5** and **personalisation 3.8**. The `innovation` axis is
withdrawn — both its inputs fail — and returns `None` for every bank.

**What it means.** The trust axis only measures three specific signals
(institutional tenure/ownership cited, a prominent regulatory disclosure,
branch network cited as a benefit) — a low score says these three signals
are largely absent from ING's current-account pages, not that ING is
untrusted. Still, for a 150-year-old institution, a page that reads as
digitally confident and heavily cross-selling but rarely reaches for its own
institutional weight is a specific, arguable gap — one a challenger bank
would not have the option to close the same way.

## 4. Traditional and challenger banks argue from opposite playbooks — and ING's own new "subscription framing" signal draws the same line

Cohen's d ranks: challengers target expats explicitly (100% of challenger
pages vs 18% of traditional pages, d = +2.31); traditional pages show people
in photography far more (91% vs 25%, d = -1.84).

A new signal, added this week: **`subscription_style_framing`** — whether a
bank frames its account tiers as a phone- or streaming-style subscription
("abonnement") rather than a traditional banking "pack". Traditional banks:
0%. Challengers: 50% (d = +1.80). Checked in the raw page text before being
added as a feature: Revolut uses "abonnement" 16 times, bunq 9 times, every
traditional bank in scope 0 times.

**What it means.** This is a second, independent measurement landing on the
same traditional/challenger line the rate-framing and expat-targeting gaps
already draw: challengers are reframing what a bank account *is* — a
subscribed service, not a "pack" — for a segment traditional banks aren't
naming on the page at all.

## 5. ING segments across pages, not within them

`target_personas` (a new model-assisted field, one structured call per page,
same pattern as every other model-assisted feature) shows ING's current-
account pages naming **3 of the 8 possible personas** across its 3 pages —
mass market, student and expat. Revolut names four on its single page, the
widest in this family; most other banks name one, and Argenta, Belfius, CBC,
Crelan and KBC name exactly one: mass market.

Across ING's whole page set rather than the current-account family alone, the
count rises to **6 of the 8** — mass market, student, expat, family, investor
and retiree — tied with KBC for the widest coverage in the dataset. The
personas do not stack up on one page: each lands on a different product page.

**What it means.** Read together with insight 3 (low trust-signal presence)
and the AI Score's `personalisation` axis (3.8/10, 2nd of 14 banks), ING is not
failing to speak to enough audiences. It reaches them by dedicating a page to
each rather than by widening any single page — the opposite of Revolut, which
names four personas on one page and builds that breadth around a single
product story. Neither approach is better on this evidence. What the split
does raise is a routing question rather than a copy one: breadth spread across
pages only works if the right customer reaches the right page.

## 6. ING's search-interest footprint looks like a challenger's, not like its own peer group's

Google Trends by Belgian region (Brussels/Flanders/Wallonia, added this
week): of the 6 traditional banks, 5 peak outside Brussels — KBC and Argenta
peak in Flanders (100 vs 11 and 24 in Wallonia), BNP Paribas Fortis, Crelan
and Belfius all peak in Wallonia (100). **ING is the exception**: it peaks in
Brussels (100), same as all three challengers (Revolut, N26, bunq — also 100
in Brussels each). Every other traditional bank's lowest region is Brussels;
for ING, Brussels is the highest.

**What it means.** This is search interest, not campaign performance or
communication content — it says nothing about *what* a page argues, only
*where* people are looking for the brand, and 5 of 6 traditional banks
matching their known regional roots is a sanity check on the pipeline, not a
discovery on its own. ING breaking that pattern, in the same direction as
every challenger in the set, is the one region-level result that lines up
with the overall traditional↔challenger positioning score (0.41, clearly
with the traditional banks) from a completely independent measurement. Worth
noting in the room as a second signal pointing the same way, not proof of
anything by itself — the same "context, never an outcome" rule the existing
Trends tab already applies.

---

## What ties these together

Read side by side, the pattern is not "ING is doing something wrong" — it's
that ING's page combines signals that don't usually travel together: the
most urgency and persuasion-technique density in the set, high digital and
cross-sell scores, persona coverage tied for the widest in the set, and yet the
lowest presence of the institutional-trust signals a traditional bank is
uniquely positioned to use, on a visibly darker page than its own peer
group. Every one of these is a hypothesis the data can surface, not a cause
it can prove — no click, conversion or performance data exists in this
project. But five independent measurements pointing at the same page from
different angles is worth a slide, and worth a question in the room: is this
a deliberate repositioning, or five separate choices that happened to add up
this way?
