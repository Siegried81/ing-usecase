# Day 6 gate — discussion notes

> **steve 21/09, gate day.** The per-bank table below predates this morning's
> re-collection: the chain now runs for **11 banks / 13 pages** with nothing
> excluded (Belfius has a current-account page; vdk, hellobank and beobank were
> added; Revolut returned via a static fetch), headless geometry renders in this
> environment, and BNP Paribas Fortis (503) remains manual-capture only. The one
> blocker below is unchanged: **an independent second human rater**. Siegried's
> sheet is complete at 23/23; Stephane's 9 pages were machine-proposed and
> adopted (the sheet says so); Dan is still at 0/23. Agreement is now measurable
> for all 13 features, with three below the module's 60% bar.
>
> **sieg 22/09: this callout is itself now stale on two points.** BNP Paribas
> Fortis no longer needs manual capture — `method: headful` fetches it live
> (decisions.md, "steve 21/09, BNP Paribas Fortis captured", written the same
> day as this note but not reflected here). And Stephane's scores are no
> longer machine-proposed/adopted: checked directly today, 0 of his 13
> current overlapping scores match the model's output. Scope is now 50
> pages / 14 banks / 6 families (decisions.md, "sieg 21/09, scope restored";
> `other` folded into `pension` later the same night - `belfius_other_fr_01`
> was Belfius's pension page, mislabeled).

sieg 15/09, prepared ahead of the Monday gate review. Per the plan (section
6): the team asks one question — does the chain run end-to-end, from a URL to
a scored, comparable row, to a bank profile, for every bank in scope? Thirty
minutes, one decision, all three.

## Per-bank pipeline status

sieg 16/09, current snapshot — re-check and update the morning of the gate,
this will keep moving. One row per in-scope bank.

**sieg 20/09, refreshed again the night before the gate** — the 18/09 table
below was itself stale (Belfius and BNP Paribas Fortis shown as "excluded —
no page in `current_account_pack`"; KBC/Belfius/N26 shown missing a
screenshot). Both are fixed since: Belfius and BNP each got a real
current-account-pack capture this week, and every current-account-pack row
now has a screenshot. Real state from `data/processed/campaigns.csv` and
`outputs/bank_profiles.json`'s own `_scope`:

| Bank | Captured (HTML) | Robots allowed | Screenshot | LLM extraction | Rubric: model | Rubric: siegried | Rubric: dan | Rubric: stephane | Profile card | End-to-end? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ING | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| KBC | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| Belfius | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| Revolut | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| N26 | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| BNP Paribas Fortis | yes (manual capture) | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| Argenta | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| Crelan | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| bunq | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |

Every bank in scope now has a real capture, a screenshot, LLM extraction and
a profile card — collection and extraction are done, and
`bank_profiles.json`'s `_scope.banks_excluded_no_page_in_family` is now
empty (was `["belfius", "bnp_paribas_fortis"]`). The gate has exactly **one**
real blocker left, the same one for all 9 banks: **Dan and Stephane's rubric
sheets are still at 0/23 pages each** (Siegried's and the model's are both
complete, 23/23 — see the README Status table). Nothing is end-to-end until
at least two independent human raters have scored.

Note on BNP Paribas Fortis's capture itself (superseded): the CDN-blocking
issue from 16/09 (robots.txt allowed the page, but automated fetches got a
non-2xx response the same page loaded fine in a normal browser) is worked
around, not solved — `collection_method=manual_capture` for this row, via
`scripts/import_captures.py` (README, "When a site will not serve the
pipeline"). The underlying CDN behaviour was never diagnosed further.

## The decision

Per the plan's own table:

- **YES** (every bank end-to-end) → Days 7–8 attempt the LLM generation
  stretch (Step 5, already built and running per the dry-run). Stephane
  moves to generation; Siegried and Dan take over remaining analysis and
  documentation in parallel.
- **NO** (chain broken) → stretch dropped immediately, no debate. Days 7–8
  spent completing/hardening the comparator instead. Generation presented as
  designed-but-not-built, with criteria and prompt structure shown, not
  demonstrated.
- **PARTIALLY** (works for some banks only) → `[decide threshold: how many
  banks is "enough" to call the comparator itself done, vs. still hardening]`
  — sieg 20/09: this is no longer the live scenario. Collection/extraction
  is 9/9 banks, not partial by bank anymore. The actual partial state at
  the gate is by **rater**, not by bank: only 1 of 3 rubric raters
  (Siegried) has scored, so every human-scored feature is still one
  person's judgement, not a settled comparison. Decide the threshold on
  that axis instead (is 1/3 raters enough to present provisionally?).

## Talking points to bring

- What broke, concretely, for any bank that isn't end-to-end — as of 20/09
  this no longer applies at the collection/extraction level (9/9 banks, see
  the table above); the one open step is the rubric, and it's the same step
  for every bank.
- Whether a dataset with only 1 of 3 rubric raters done is already enough to
  answer the PRD's core questions (BO-01–BO-04) provisionally, or whether
  the gate should wait for Dan and Stephane regardless.
- Sample-size caveat to carry into the analysis regardless of the gate
  outcome: descriptive only, no significance claims (PRD risk R-03).
- If Step 5 proceeds: confirm the guardrails still hold (labelled synthetic,
  no invented rates, no competitor assets reused, human review before
  anything is shown) — not re-litigate them.
