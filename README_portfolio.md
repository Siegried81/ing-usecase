# Banking Campaigns Comparator — ING use case

Measuring how fourteen Belgian banks communicate comparable products, so the
differences can be argued from evidence instead of impression.

A two-week proof of concept for ING DACI / Customer AI, built 14–25 September 2026
by a team of three: Siegried Camus (lead, marketing framework, integration), Dan
Ukendi (search-interest pipeline), Stephane van der Aa (collection architecture,
GenAI). This fork carries the full project; the section below says which parts
were mine.

---

## The problem, and the ceiling

A bank wants to know how its public campaign pages differ from its competitors'.
The obvious approach — scrape some pages, ask a model which is better — produces a
number nobody can defend.

So the project is built the other way round. Every claim traces to one declared
feature in one dictionary, the dictionary is frozen and version-checked, and the
system is explicit about what it cannot say:

**No performance data exists here.** Nothing links a design choice to a click, a
conversion or a sale. Every finding is *"ING does X differently"*, never *"X works
better"*. That is structural — there is no outcome variable in the dataset at all.

Getting that boundary right, and keeping it under deadline pressure, is most of
what this project is about.

## What it does

```
targets.yaml → robots.txt gate → capture (static / headless / headful)
             → deterministic extraction + one structured LLM call per page
             → human rubric sheet → validated dataset
             → analysis → report.json → recommendations → generated demo site
```

51 pages · 14 banks · 6 product families · 104 declared features · 449 tests, all
network mocked.

## What makes it worth reading

- **One measuring stick.** `config/feature_dictionary.yaml` is the single source of
  truth. The schema, the validator and the docs are derived from it, and a column
  that is not in it is a hard validation error. Each feature declares how it was
  produced and how far it can be compared across languages.
- **Compliance as a gate, not a setting.** `assert_can_fetch()` checks live
  `robots.txt` before every fetch — including hero images and same-origin
  sub-resources — and fails closed. There is no flag to skip it, and a test asserts
  the gate fires before the browser even launches.
- **No agent loops.** Every LLM call is one structured call: fixed prompt, schema
  validation against the dictionary's own allowed values, bounded retry. The model
  is pinned so a difference between two banks is a difference between two banks,
  not between two judges; a provider fallback is recorded on the row, never silent.
- **The limitations document is generated from the data**, not written from memory
  on the last evening. If two captures failed, it says which two and why.
- **Withdrawal is a first-class outcome.** Five features are measured but never
  compared, each because it turned out to describe the capture rather than the
  bank. The exclusion lives in the analysis code, so a re-run cannot undo it.

## What I worked on

From the git history, my own contributions were concentrated on:

- **Measurement correctness and the withdrawals** — finding and fixing the rate
  parser that read "100% en ligne" as an interest rate; the luminance metric that
  averaged a whole page strip and inverted a published claim; the urgency counter
  that scored a dated deadline as zero; the blank-versus-zero bug that had silently
  cut a comparison's peer group by a third. Several of these moved a number that
  was already on a slide.
- **The compliance gate**, including the hero-image fetch that was bypassing it.
- **Reputation signals** — news-theme classification, Belgian-source filtering, and
  the quota-outage handling that stops "no key" from reading as "no news".
- **The judged rubric sheet** — I am the single named rater for the 13
  judgement-based features, against the written scales in `SCORING_GUIDE.md`.
- **Integration** — 66 of the 75 merged pull requests, and the correction passes
  that kept the deck's figures matching the code.
- **The Streamlit operator dashboard**, later folded into the React UI's operator
  tabs.

The collection architecture, the headless render path and the search-interest
pipeline were built by my teammates. I have not relabelled their work.

## Read next

**[`technical_deep_dive.md`](technical_deep_dive.md)** — the real documentation:
every module explained, the measurement decisions and why, the twenty bugs that
shaped the code, and an honest list of what is still open.

The bug section is the part I would point a reviewer at. Almost none of them are
crashes — the dominant failure mode in a measurement pipeline is code that runs
cleanly, passes every range check, and reports the wrong thing.

## Run it

The fixture path needs no API key and no network:

```bash
pip install -r requirements.txt
cp .env.example .env
python3 scripts/make_fixture.py       # synthetic dataset — every row is invented
python3 scripts/run_analysis.py
python3 -m pytest tests/ -q
```

Fixture archetypes deliberately encode the kickoff deck's *claims*, so a fixture
run always confirms them. Never read a fixture result as evidence — that warning is
printed by the code itself.

Real collection needs an LLM key, a Playwright Chromium install and network access.
`docs/pipeline.md` has the command order and the mandatory re-merge rule.

## Licence

Not licensed for redistribution. The repository contains client requirement
documents and captured pages from third-party bank websites; those are not mine to
relicense.
