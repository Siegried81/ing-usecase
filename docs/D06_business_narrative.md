# D-06 — Business narrative, draft insights

sieg 16/09. Draft material for the business presentation (D-06). Written for
the business audience per the plan: what this means for ING, no method
detail — the "how" lives in D-07 and the code, not here.

Each insight below is traceable to a specific feature and source page
(NFR-03) and stated as a hypothesis to test, never a cause — no performance
data exists in this project (PRD 5.2), so nothing here claims that a design
choice produces a better or worse result, only that it is different.

---

## 1. ING writes more than double what its peers do

ING's page carries 4,217 words. The peer average, on the same product
category, is 2,005 — less than half. This is not a matter of interpretation:
word count is measured automatically, the same way for every bank.

**What it means.** A prospective customer opening ING's page meets over
twice the reading load of a KBC or N26 visitor before reaching the same
decision. Worth testing whether that length serves the offer or dilutes it.

## 2. Four of the five impressions from the launch deck don't hold up

The kickoff deck's eyeball observations were tested one by one against the
real data:

| Observation | Verdict |
| --- | --- |
| Belfius is the most verbose | **Not supported** — KBC is (2,644 words vs Belfius's 1,354) |
| KBC is straight to the point | **Not supported** — the opposite: it's the longest |
| ING is the only traditional bank using animation | **Not supported** — KBC and Belfius are animated too |
| Revolut uses very little text | **Supported** |

**What it means.** The method exists precisely to catch this — informal
impressions, even well-informed ones, don't always survive contact with
measurement. One insight the team can state with confidence: three of the
four assumptions the project started from needed correcting before they
could be acted on.

## 3. ING sits clearly on the traditional side, not in the middle

Projected onto the traditional↔challenger axis (0 = traditional centroid,
1 = challenger centroid), ING scores 0.08.

**What it means.** Despite a visibly digital-forward brand narrative, ING's
communication style — on the features actually measured — reads as
solidly traditional, not as a bank positioned between the two worlds.

## 4. ING leans harder on urgency and image volume than any peer

Two more automatic, high-trust measurements: ING uses urgency language
("only until...") 6.35 standard deviations above the peer mean, and carries
49 images against a peer average of 14.5 — 4.09 standard deviations above.
Both numbers were independently hand-verified against the per-bank profile
cards before being used here.

**What it means.** Combined with insight 1, a pattern emerges: ING's page is
not just longer, it is also busier — more visual volume, more urgency
cueing, in the same space a peer covers with a third of the words and a
fraction of the images. Whether that combination reads as energetic or as
noisy to a real visitor is exactly the kind of question this project cannot
answer alone (no performance data) — but it is now a precise, testable one
instead of a vague impression.

---

## What ties these together

Not one weakness — one consistent pattern. ING's page pushes more content,
more urgency, more visuals into the same decision, while sitting closer to
the traditional cluster than its digital ambitions might suggest. Whether
that is a deliberate choice or an accumulated one is exactly the kind of
question the data can surface but not answer — which is the honest
framing to carry into the room.
