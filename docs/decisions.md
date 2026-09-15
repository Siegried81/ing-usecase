# Decision log

Project Plan section 9 lists seven decisions needed in the first two days. This
file records the ones taken, so "we decided it on Tuesday" is checkable rather
than remembered. One entry per decision; append, never rewrite.

---

## D6 — Which LLM for model-assisted features and generation

**Owner** Stephane · **Due** Day 2 (Tue 15 Sep 2026) · **Status** decided

**Decision.** DeepSeek `deepseek-chat` is the pinned model for this project.
Every model-assisted feature and every generated campaign is produced by it.

**Why this one.** It is the model we actually have a working key for today, and
Day 2 is the deadline. The requirement was never "the best model" — it was *one*
model, named and recorded, so that a difference between two banks is a difference
between two banks and not between two judges.

**Why pinning matters (NFR-02).** Roughly a quarter of the dictionary —
24 of 97 features — is model-assisted. `collection/llm_extractor.py` falls back
across providers when one is rate-limited. Before today that fallback was
*silent*: a single collection run could label ING with one model and Revolut with
another, and nothing in the dataset would say so. Any finding on those features
would have been partly an artefact of which provider happened to be up.

**What changed in the code.**

| Change | Where |
| --- | --- |
| DeepSeek added at the head of the provider chain | `collection/llm_extractor.py` |
| `_call_llm` now returns `(text, "provider/model")` | `collection/llm_extractor.py` |
| `extract_model_assisted_with_provenance()` returns the model alongside the fields | `collection/llm_extractor.py` |
| New `extraction_model` column, written on every collected row | `config/feature_dictionary.yaml`, `scripts/run_collection.py` |
| `validate()` warns when one dataset contains more than one model, and names which banks got which | `schema.py` |

**Fallback policy.** The other providers stay configured beneath DeepSeek. Losing
a night of collection to one provider outage is worse than a mixed dataset —
but a mixed dataset must be *visible*, not silent. If a run does fall back, the
options are: re-run the affected banks on the pinned model, or report the mix as
a limitation in D-09. Never ignore it.

**Prompts.** Stored in the repository as required, not in a notebook or a chat:
`SYSTEM_PROMPT` in `collection/llm_extractor.py` (feature extraction) and in
`generation.py` (campaign generation). `temperature=0` throughout.

**Cost and licensing.** Paid API, key held by Stephane, never committed —
`.env.example` documents the variable; `.env` is gitignored.

**Revisit if.** DeepSeek quality proves inadequate on the first real captures
(Day 3–4), or agreement with human labels on the validation sample is poor. Any
change of model invalidates the model-assisted features collected before it —
re-run all banks, do not mix.

---

## D5 — Dataset schema and file format

**Owner** Dan + Stephane · **Due** Day 2 · **Status** decided, frozen

One CSV, one row per campaign page, provenance columns first. List-valued
features (`palette_hex`, `accent_locations`, `persuasion_levers`) are stored
pipe-separated so the dataset stays plain CSV.

The freeze is enforced two ways, deliberately:

- `tests/test_schema.py::test_dictionary_matches_frozen_snapshot` (Siegried) —
  byte equality against `config/feature_dictionary.frozen.yaml`. Catches an
  *accidental* edit.
- `scripts/check_schema_freeze.py` (Stephane) — the rule itself: additions pass;
  renames, removals, type changes, narrowed ranges or categories, tier demotions
  and tightened nullability fail, naming the feature.

Byte equality alone is not the rule — it fails on an addition, which section 3.2
explicitly permits, and it *passes* on a rename, because updating both files
makes the bytes match again. A rename is the change that actually breaks
analysis code, so it is the one worth catching.
