# Business web UI

A read-only view of one analysis run, for the business audience (D-06).

```bash
python3 scripts/export_web_report.py --product-family auto   # writes web/public/report.json
cd web && npm install && npm run dev                          # http://localhost:5173
npm run build                                                 # static bundle in web/dist/
```

## Why a snapshot and not a server

The UI reads a single `report.json` and talks to nothing. A browser depending on
a laptop process is the wrong thing to rely on five minutes before a stakeholder
presentation, and a snapshot is the honest shape for a finding anyway: it is true
for one dataset, at one capture date, under one scope. `npm run build` produces a
folder that opens anywhere.

## What it deliberately does

- **Leads with the answer**, not the method. Positioning first, features second.
- **Carries its own scope.** Product family, banks, capture date, language and
  the banks that are *not* in the comparison sit above the first number, not in
  a footnote.
- **Marks judgements as judgements.** `judged` means a person scored it against a
  rubric; `model-judged` means a language model did and no human has checked it.
  Everything unmarked was counted or measured. A business reader cannot otherwise
  tell that "clarity of the offer" is an opinion and "words on the page" is not.
  Derived features inherit the trust of their sources, so AIDA coverage is marked
  even though it is computed.
- **Never shows generated copy alone.** The synthetic label, the scorecard and
  the "says nothing about performance" line are in the same block a stakeholder
  would screenshot (plan risk P-08).
- **Ends on what it cannot support**, rendered from `limitations.md`'s own source
  rather than retyped.

## What it deliberately is not

No pipeline control, no scoring, no dataset editing. This is the findings
surface; the operator tooling is a separate question (see
`docs/web_ui_proposal.md`).

## Keeping it honest

`src/types.ts` mirrors `scripts/export_web_report.py`. Change one, change the
other. Every figure comes from the library through the exporter — the UI does no
arithmetic of its own, so there is no second definition of any number on screen.
