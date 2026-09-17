# Proposal — a web UI over the comparator

steph 17/09. For the team to accept, amend or reject before anything is built.

## The short version

The codebase is already in the right shape for a UI: `src/comparator/*` is a
library with no I/O assumptions, and `scripts/*` are thin wrappers around it. A
UI is a second caller of that library, not a rewrite of anything.

But most of the pipeline does not benefit much from a UI. **One part benefits
enormously** — rubric scoring — and it is the part currently blocking the
analysis. I would build that first and treat the rest as optional.

---

## 1. Honest evaluation of what we have

**Suits a UI well**

| | why |
| --- | --- |
| Clean library/CLI split | the UI calls `comparator.*` directly; no shelling out to scripts |
| Everything is a file | datasets, sheets, snapshots, screenshots, charts — all inspectable, all serveable |
| Artefacts already exist | PNG, MD, CSV, JSON are produced today; a viewer is mostly plumbing |
| Stateless analysis | `run_analysis` is <2s and pure — cheap to re-run on any parameter change |

**Does not suit a UI, and should not be forced into one**

| | why |
| --- | --- |
| Collection | ~5–8s per page, ~90s for the current 12. Needs a job model, not a request |
| The feature dictionary | it is the frozen contract (P-04). Editing it from a web form would undo the freeze rule. **Read-only in the UI, permanently** |
| Compliance gates | `assert_can_fetch` must stay server-side and non-overridable. **No "skip robots check" toggle, ever** — not behind a flag, not for testing |
| Provenance | a UI that lets someone hand-edit an extracted feature destroys the audit trail. Rubric scores are the one exception, because they are human by design |

**A tradeoff worth stating once.** Dan already has a working Streamlit app in
`kbc-ing-benchmark/`. Streamlit would get 80% of the value below in about a day;
React is roughly 4–5 days for the full scope. With 8 working days left and two
presentations to deliver, that is a real cost. If the goal is *a usable tool for
the team*, Streamlit wins. If the goal is *something to show the business on
Day 10*, React wins, because the rubric-scoring screen and the results view are
demo-grade in a way Streamlit is not. I would still build the React version only
in the phase order below, stopping whenever the deck needs the time more.

---

## 2. What is actually worth exposing

Ranked by value, not by how interesting it is to build.

### ★★★ Rubric scoring — the one that pays for itself

13 features × 12 pages × 3 raters, currently done by editing a CSV while the
screenshot is open in another window. It is the single thing blocking every
judgement-based dimension in the analysis, and Friday's session depends on it.

A scoring screen is dramatically better than a spreadsheet: the screenshot beside
the form, the rubric levels visible next to the field they apply to, and no way
to enter a value the validator would later reject.

Design points that matter more than the UI itself:

- **One rater per session, their own sheet.** Never show another rater's score
  while scoring. NFR-05's agreement number is only meaningful if the judgements
  are independent, and a visible neighbouring score destroys that quietly.
- **The model's sheet is hidden during scoring** for the same reason, then shown
  in the comparison view afterwards.
- **Vision-only features are the point.** `accent_locations`, `text_image_layout`,
  `layout_archetype`, `mobile_first_design_signal` cannot be model-scored — the
  UI is where they get done.
- Blank stays blank. No default selections, no "looks like a 3" nudges.

### ★★★ Dataset explorer — makes "is this the right page?" answerable

Per page: the screenshot, the extracted features grouped by dimension, the
quality verdict and its note, the source URL, and which model labelled it. This
is the screen that would have caught the ING shell and the BNP maintenance page
in seconds rather than after they reached the analysis.

Include the two provenance facts that keep tripping people up: `collection_method`
(live vs manual capture) and `extraction_model`.

### ★★ Results viewer

The four charts, `charts.md`, `limitations.md`, the profile cards, side by side
with the scope banner. Today these are scattered files and two of them disagreed
on their counts until yesterday.

Worth it mostly because it is **the demo surface for Day 10** — a business
audience should not be shown a folder.

### ★★ Run orchestration

Buttons for collection, model scoring, analysis, generation, with live progress
and the per-page quality verdicts appearing as they happen.

Genuinely useful for collection, because watching a bank fail live is how you
learn the page was wrong. Marginal for analysis, which is faster than the click.

### ★ Generation studio

Adjust the target profile, generate, see the scorecard and where the result lands
against the real banks. Good demo value, lowest operational value — and it needs
the P-08 guardrails visible on screen, not buried: labelled synthetic, no invented
rates, and the scorecard always shown next to the copy.

### ✗ Not proposed

Auth, multi-user, a database, dictionary editing, scheduling, deployment. None of
it serves a POC with a Day 10 deadline, and each adds a thing that can break
during a demo.

---

## 3. Architecture

```
React (Vite + TS)  ──HTTP/SSE──►  FastAPI  ──►  comparator.*  ──►  files
                                     │
                                     └── jobs (in-process, one at a time)
```

**FastAPI over the library, not over the scripts.** The scripts stay as they are
— they are how the pipeline runs in CI and on a laptop, and the UI must not
become the only way to run anything.

**Jobs.** Collection and generation are too slow for a request. One in-process
job runner, **one job at a time**: concurrent collection runs would multiply our
request rate against the banks, which LC-05 asks us not to do. Progress over SSE,
log lines streamed to the UI.

**Files stay the source of truth.** The UI reads and writes the same
`data/processed/*.csv` and `data/rubric/*.csv` the CLI uses. No hidden state, no
sync problem, and the audit trail stays exactly where it is.

### API surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/state` | what exists: dataset, outputs, sheets, freeze status |
| `GET` | `/api/dictionary` | features, dimensions, rubric levels — **read-only** |
| `GET` | `/api/dataset` | rows + quality verdicts + scope |
| `GET` | `/api/dataset/{page_id}` | one page, with screenshot and snapshot URLs |
| `GET` | `/api/targets` · `PUT` | collection targets (the scope decision stays a file) |
| `POST` | `/api/runs/{collection\|analysis\|generation\|rubric-model}` | start a job |
| `GET` | `/api/runs/{id}/stream` | SSE progress + log |
| `GET` | `/api/rubric/{rater}/next` | next unscored page for this rater |
| `PUT` | `/api/rubric/{rater}/{page_id}` | save one page's scores |
| `GET` | `/api/rubric/agreement` | raw % and Cohen's kappa |
| `GET` | `/api/results/*` | charts, limitations, profiles |

Validation is the existing `schema.validate` and the dictionary's own allowed
values — the API should not grow a second, looser idea of what is valid.

---

## 4. Screens

1. **Run control** — pipeline stages, last-run times, live job log, quality
   verdicts as they arrive.
2. **Dataset** — table of pages with quality badges; click through to screenshot
   + features + provenance.
3. **Score** — the rubric screen. Screenshot left, form right, rubric levels
   inline, progress across pages, nothing from other raters visible.
4. **Results** — charts with the scope banner, limitations, profile cards.
5. **Generate** — targets, output, scorecard, guardrail status.

---

## 5. Phasing

| Phase | Scope | Rough cost | Stop here if… |
| --- | --- | --- | --- |
| 1 | Rubric scoring + dataset explorer (read-only API) | ~1.5 days | …you only ever build one thing. This unblocks the analysis. |
| 2 | Results viewer | ~1 day | …the Day 10 demo is the goal. |
| 3 | Run orchestration + job runner | ~1.5 days | …collection has stabilised and nobody needs to watch it. |
| 4 | Generation studio | ~1 day | …optional throughout. |

Phase 1 is worth doing **even if Friday's session happens on CSVs**, because the
same screen serves the next scoring round and the vision-only features still need
a human with a screenshot.

---

## 6. Risks

| | mitigation |
| --- | --- |
| UI becomes the only way to run things | scripts stay first-class; CI keeps running them |
| Someone adds a compliance override to unblock a demo | no such parameter exists in the API; the gate is inside the library |
| Scoring independence is lost | one rater per session, others' scores never rendered during scoring |
| It eats the time the deck needs | phase order above; stop after any phase |
| Provenance is edited away | only rubric fields are writable, and only into the rater's own sheet |

## 7. What I need agreed before building

1. **React or Streamlit**, given Dan already has Streamlit working and we have 8 days.
2. **Phase 1 only, or further** — my recommendation is Phase 1 now, decide on the rest after Friday.
3. **Who runs it** — local-only on a laptop, or does it need to be reachable by the others?
