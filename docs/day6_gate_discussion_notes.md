# Day 6 gate — discussion notes

sieg 15/09, prepared ahead of the Monday gate review. Per the plan (section
6): the team asks one question — does the chain run end-to-end, from a URL to
a scored, comparable row, to a bank profile, for every bank in scope? Thirty
minutes, one decision, all three.

## Per-bank pipeline status

sieg 16/09, current snapshot — re-check and update the morning of the gate,
this will keep moving. One row per in-scope bank.

| Bank | Captured (HTML) | Robots allowed | Screenshot | LLM extraction | Rubric scored | Profile card | End-to-end? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ING | yes | yes | yes | yes | no | yes | blocked on rubric only |
| KBC | yes | yes | yes | yes | no | yes | blocked on rubric only |
| Belfius | yes | yes | yes | yes | no | yes | blocked on rubric only |
| Revolut | yes | yes | yes | yes | no | yes | blocked on rubric only |
| N26 | yes | yes | yes | yes | no | yes | blocked on rubric only |
| BNP Paribas Fortis | no | yes | no | no | no | no | no — see note |
| Argenta | not yet configured | | | | | | no |
| Crelan | not yet configured | | | | | | no |
| bunq | not yet configured | | | | | | no |

Note on BNP Paribas Fortis: robots.txt allows the page, but the capture was
excluded by the quality gate (non-2xx response). Live-checked 16/09 from two
different automated environments and got the same result, while a normal
browser loads the page without issue at the same time — looks like the
site's CDN treating cloud/datacenter traffic differently, not a real outage.
Under investigation; not yet resolved as of this writing.

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
