# Day 6 gate — discussion notes

sieg 15/09, prepared ahead of the Monday gate review. Per the plan (section
6): the team asks one question — does the chain run end-to-end, from a URL to
a scored, comparable row, to a bank profile, for every bank in scope? Thirty
minutes, one decision, all three.

## Per-bank pipeline status

sieg 16/09, current snapshot — re-check and update the morning of the gate,
this will keep moving. One row per in-scope bank.

**sieg 18/09, refreshed for Monday's gate** — table below was still the
16/09 snapshot (Argenta/Crelan/bunq shown as "not yet configured", BNP
Paribas Fortis shown as blocked with no capture at all). Both are stale;
real state from `data/processed/campaigns.csv` and the rubric sheets:

| Bank | Captured (HTML) | Robots allowed | Screenshot | LLM extraction | Rubric: model | Rubric: siegried | Rubric: dan | Rubric: stephane | Profile card | End-to-end? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ING | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| KBC | yes | yes | **no** | yes | yes | yes | no | no | yes | blocked on screenshot + dan + stephane |
| Belfius | yes | yes | **no** | yes | yes | yes | no | no | **excluded** — no page in `current_account_pack` | blocked on screenshot + dan + stephane, then still excluded from this comparison by family |
| Revolut | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| N26 | yes | yes | **no** | **no** | yes | yes | no | no | yes | blocked on screenshot + LLM extraction + dan + stephane |
| BNP Paribas Fortis | yes (manual capture) | yes | yes | yes | yes | yes | no | no | **excluded** — no page in `current_account_pack` | blocked on dan + stephane, then still excluded from this comparison by family |
| Argenta | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| Crelan | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |
| bunq | yes | yes | yes | yes | yes | yes | no | no | yes | blocked on dan + stephane |

Every bank in scope now has a real capture — collection is done. The gate
has one real blocker left, the same one everywhere: **Dan and Stephane's
rubric sheets are still at 0/12 pages each** (Siegried's and the model's are
both complete, 12/12). Nothing is end-to-end until at least two independent
human raters have scored.

Note on BNP Paribas Fortis and Belfius: they are **not** blocked on
collection — both have a usable capture. `outputs/bank_profiles.json`'s own
`_scope.banks_excluded_no_page_in_family` names the real reason: neither has
a page in `current_account_pack`, the family the current comparison is
filtered to (DR-04 forbids comparing across product families). This was
flagged in the README as an undocumented mystery to ask Stephane about — it
isn't a mystery, the dataset already states it.

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

## Talking points to bring

- What broke, concretely, for any bank that isn't end-to-end (name the step:
  compliance gate, scrape, render, LLM extraction, rubric, profile card).
- Whether a partial dataset (e.g. 6/9 banks) is already enough to answer the
  PRD's core questions (BO-01–BO-04), or whether specific missing banks
  (ING, since BO-01/BO-02 depend on it) block the gate regardless of count.
- Sample-size caveat to carry into the analysis regardless of the gate
  outcome: descriptive only, no significance claims (PRD risk R-03).
- If Step 5 proceeds: confirm the guardrails still hold (labelled synthetic,
  no invented rates, no competitor assets reused, human review before
  anything is shown) — not re-litigate them.
