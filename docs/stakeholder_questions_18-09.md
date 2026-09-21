# Ten questions for Diego and Victor — 18/09

> **steve 21/09:** kept as written — these are the questions, not the answers.
> Question 1 is worth re-reading beside the code, because the project's central
> guardrail follows from it: with no CTR or accept-rate data, nothing here may
> claim that a design choice changes an outcome, and every recommendation in the
> web UI is stated as a hypothesis to test rather than a cause (PRD 5.2).

steph 18/09. Ordered by how much the answer changes what we do, because the
meeting may run short. Each one says what prompted it, so none of them is a
question we could have answered ourselves.

---

## 1. Can we have CTR or accept-rate data for even one product?

**Why we are asking.** Every finding in the deck is of the form *"ING does X
differently"* — never *"X works better"*. That ceiling is not caution, it is
structural: we have no outcome variable at all. Your own kickoff deck showed
weekly CTR of 0.60–1.06% across 1,307 banners, so the data exists somewhere.

**What changes.** One product's banner CTR joined to our feature rows turns a
descriptive comparison into a testable one — we could say which measured
features move with performance and which do not. Without it, every
recommendation stays a hypothesis for someone else to test. This is the single
largest upgrade available to the project.

*PRD Q-04, still open since Day 1.*

---

## 2. Which product should anchor the comparison — current-account packs, or term accounts?

**Why we are asking.** We compare **current-account packs**, because that is the
one product where enough banks had a comparable page. But your own deck framed
the competitive story around the September term-account cycle following the 2023
state bonds. Those are different questions.

**What changes.** If term accounts are the commercially live question, the
collection targets change and roughly a day of re-collection follows. Worth
knowing before we harden anything.

*PRD Q-03.*

---

## 3. Are public marketing pages the right surface, given your problem is inbound banners?

**Why we are asking.** The problem you described is **inbound** — 110M
interactions, banners inside web and app, a top-5 NPS irritator. What we can
legally and practically collect is the **public open web**: acquisition pages
aimed at non-customers. These are not the same communication, to the same
people, with the same constraints.

**What changes.** If the real target is in-app banners, then the durable
deliverable is the feature framework rather than this comparison, and we should
say so explicitly in both decks. If the open web is genuinely of interest in its
own right, we stop caveating it as a proxy.

---

## 4. ING writes roughly twice as much as its peers. Is that deliberate, or regulatory?

**Why we are asking.** It is our most robust finding — word count is counted, not
judged, and ING's pages carry markedly more text than the peer average on the
same product. But we cannot tell *why* from the outside, and the two
explanations point in opposite directions.

**What changes.** If it is mandated disclosure, it is not a finding at all and we
should drop it. If it is accumulated content nobody has pruned, it is the most
actionable thing we have. Nobody outside ING can settle this.

---

## 5. Which language should be the reference — FR or NL?

**Why we are asking.** Our current dataset mixes both. Word counts and
readability are not comparable across languages, so those features currently
carry a translation effect on top of the editorial one. (We also found the team
had scored a KBC page in English while the dataset held the Dutch one — the same
ambiguity, one layer down.)

**What changes.** One language across all banks removes a confound from the
headline finding in question 4. A day of re-collection, and worth it.

*PRD Q-07.*

---

## 6. Do you have internal standards we should be scoring against?

**Why we are asking.** Our judged features encode *our* notion of good marketing
— AIDA, Cialdini, feature-advantage-benefit. Defensible, and generic. If ING has
its own campaign standards, tone-of-voice guide or accessibility bar, scoring
against those would change the question from *"how does ING differ from the
market?"* to *"where does ING miss its own standard?"* — which is far more
actionable internally.

**What changes.** We would re-point the rubric at your framework. The machinery
does not care which rubric it runs.

---

## 7. Four of the five observations in your kickoff deck did not survive measurement. How do you want that handled?

**Why we are asking.** The deck stated that Belfius is verbose, KBC is concise,
ING is the only traditional bank using animation. Measured, most of these do not
hold — KBC is the longest, and KBC and Belfius both animate.

We think this is the most valuable thing the project produced: it is exactly what
a measurement framework is for. But it corrects your own briefing, and we would
rather agree the framing with you than surprise a room with it.

**What changes.** Whether it leads the business deck as a headline ("informed
impressions needed correcting") or sits in the method section as a validation
result.

---

## 8. Which competitor actually matters commercially?

**Why we are asking.** We currently weight all nine banks equally, which is a
methodological default, not a business judgement. Our similarity analysis can be
pointed at whichever comparison matters.

**What changes.** If Revolut is the real threat, we report ING-vs-challengers. If
it is KBC on current accounts, the interesting axis is ING against one
traditional peer, and half our dataset becomes context rather than subject.

---

## 9. What happens to this after Day 10 — and who owns it?

**Why we are asking.** The framework is built to extend to social and in-app
banners, and that extension is where it becomes genuinely useful to your team.
That is a real commitment, not a script anyone can inherit: the rubric needs
scorers, the collection needs maintenance, and campaign pages change without
notice.

**What changes.** It determines what we spend the last two days on. Handover
documentation and reproducibility if someone picks it up; a tighter, more
finished demo if it stops here.

---

## 10. Can the repository and deliverables be shared, and at what level?

**Why we are asking.** We store competitor page snapshots and screenshots for
reproducibility. We treat everything as internal and redistribute nothing, but
"internal" has not been confirmed by anyone at ING, and it affects where this
can live after we hand it over.

**What changes.** Whether the handover is a repository, a report, or both — and
whether the stored captures travel with it.

*PRD Q-05.*

---

## Two things to state, not ask

- **Our numbers moved this morning.** Human rubric scores replaced model ones on
  several features, and two findings reversed — including one that had ING
  looking *less* clear than peers, which now reads *more* clear. Anything
  quoted from the draft narrative needs re-checking against today's run before
  the deck is locked.
- **BNP Paribas Fortis declines automated access.** Their edge returns 503 to any
  automated client, including from a normal residential connection. We did not
  work around it — we used a page a person opened in a browser and saved. Worth
  them hearing from us rather than discovering it.
