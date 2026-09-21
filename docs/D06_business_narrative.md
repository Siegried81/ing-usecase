# D-06 — Business narrative, draft insights

sieg 16/09, rewritten 20/09 the night before the Day 6 gate. Written for the
business audience per the plan: what this means for ING, no method detail —
the "how" lives in D-07 and the code, not here.

> **steve 21/09 (second update).** The rubric consensus moved after the first
> update below: Stephane's sheet was filled for nine pages (machine-proposed and
> adopted), which shifted 15 columns — all five AIDA booleans on ten pages, the
> persuasion levers on six — and re-ordered ING's peer gaps. ING is now **0.131**;
> the leading gaps are figures quoted (+1.61 SD), student targeting (+1.53 SD) and
> **clarity of the offer (+1.30 SD, rubric-sourced, so it moved with the
> consensus)**. Treat the per-feature figures below as superseded by
> `report.json`.

> **steve 21/09 — read this first.** The comparison has moved again since this
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
| Belfius is pretty verbose | **Not supported** |
| KBC is straight to the point | **Not supported** |
| ING is the only traditional bank using animation | **Not supported** — Crelan, KBC and Belfius are animated too |
| ING no longer places text next to picture | **Not supported** — "beside" is still ING's most common layout |
| Revolut uses very little text | **Not supported** |

**What it means, and a limitation worth naming out loud.** The three
word-count claims are "not supported" for an unglamorous reason: **all 9
banks now land in the same word-count band ("long")**. The comparison had to
switch from a raw word count to a coarser, language-safe band once a second
and third language entered the dataset (a raw count silently drops out of a
mixed-language comparison entirely — see D-07) — and at this sample size,
that band no longer separates anyone. The two claims that don't depend on
word count (animation, image/text layout) are cleanly not supported instead.
Net honest takeaway for the room: **zero of the five launch-deck impressions
survive measurement on the current dataset** — two on real evidence, three
because the current method can't yet tell these particular banks apart on
length. That gap is itself worth a line in the room, not something to paper
over with a false "winner".

## 2. ING's page is the most urgent and the most persuasion-heavy in the set

ING's `urgency_marker_count` is 3.5 against a peer mean of 1.10 (+2.46 SD) —
the largest gap of any measured feature. Its `persuasion_lever_count` (3.5
vs peer mean 2.08, +1.94 SD) is the second-largest — this one is rubric-
sourced and currently reflects Siegried's ratings only (Dan and Stephane are
still at 0/23, see the Status table), so treat the peer mean as one rater's
view, not a settled average. ING also claims fast digital onboarding at 0.75
against a peer mean of 0.23 (+1.52 SD) — the third-largest gap.

**What it means.** Three of ING's four biggest deviations from its peers
point the same direction: more deadline language, more persuasion technique
stacking, and a stronger fast-onboarding claim than any other bank in the
comparison. Whether that reads as energetic or as pressure to a real visitor
is exactly the kind of question this project cannot answer alone (no
performance data) — but it is now a precise, testable pattern, not a vague
impression.

## 3. ING is measurably darker than its peers, on a page that also invokes the least trust

ING's `background_luminance` is 0.198 against a peer mean of 0.591 (-1.17
SD) — a visibly dark page for a traditional bank, whose peers run close to
white. On the AI Score axes (six signals, 0-10, each a mean of already-
measured features — see the Analysis tab for the exact formulas), ING scores
**digital 8.8** and **cross-sell 10.0** (every page pushes a bundled offer)
but **trust 0.8** — the lowest of the six axes by a wide margin, next to
**simplicity 2.5** and **innovation 3.8**.

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

## 5. ING addresses more customer personas than any other bank — but shallowly

<!-- sieg 20/09: "5 distinct personas" -> "5 of the 8 possible personas" (8 = values allowed for target_personas in the dictionary), so the reader sees the scale. -->

`target_personas` (a new model-assisted field, one structured call per page,
same pattern as every other model-assisted feature) shows ING's current-
account pages naming **5 of the 8 possible personas** across its 4 pages — mass
market (75%), expat (50%), student (50%), family (25%), entrepreneur/self-
employed (25%). No other bank in the comparison names more than 4, and most
name 1-3. Argenta and KBC name exactly one: mass market.

**What it means.** Read together with insight 3 (low trust-signal presence)
and the AI Score's `personalisation` axis (6.2/10, mid-pack), ING is not
failing to speak to enough audiences — if anything it is the broadest bank
in the set. The open question is depth: 4 pages naming 5 of the 8 personas means most
personas get one page's worth of attention, while Revolut and N26 (also
broad, 3-4 personas each) build that breadth around a single, more focused
product story. Worth testing whether a page that speaks to five audiences at
once is heard clearly by any of them.

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
with the overall traditional↔challenger positioning score (0.362, "leaning
towards the challengers") from a completely independent measurement. Worth
noting in the room as a second signal pointing the same way, not proof of
anything by itself — the same "context, never an outcome" rule the existing
Trends tab already applies.

---

## What ties these together

Read side by side, the pattern is not "ING is doing something wrong" — it's
that ING's page combines signals that don't usually travel together: the
most urgency and persuasion-technique density in the set, high digital and
cross-sell scores, the broadest persona coverage of any bank, and yet the
lowest presence of the institutional-trust signals a traditional bank is
uniquely positioned to use, on a visibly darker page than its own peer
group. Every one of these is a hypothesis the data can surface, not a cause
it can prove — no click, conversion or performance data exists in this
project. But five independent measurements pointing at the same page from
different angles is worth a slide, and worth a question in the room: is this
a deliberate repositioning, or five separate choices that happened to add up
this way?
