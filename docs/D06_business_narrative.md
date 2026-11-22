# D-06: Business narrative

What the comparison means for ING, without method detail (that is D-07 and the
code). Every point traces to a feature and a source page. Each is a hypothesis to
test, not a cause: the project holds no performance data (PRD 5.2), so nothing
here says a design choice works better or worse, only that it is different.

Figures: 18 current-account pages, 14 banks, 33 comparable features, captured
21 to 23 September 2026. They are read from `outputs/charts.md` and
`web/public/report.json`. Quote them from there or from a fresh
`python3 scripts/run_analysis.py --product-family auto` run, not from this file.

## 1. ING sits with the traditional banks, at the edge

ING scores **0.41** on the traditional (0) to challenger (1) axis, the most
challenger-like of the ten traditional banks. Keytrade, the closest challenger,
is at 0.52. The nearest banks in feature space are Belfius, VDK and BNP Paribas
Fortis. The two groups do not overlap, so the axis separates them.

## 2. The most urgency and persuasion in the set

| Feature | ING | Peer mean | Gap |
| --- | --- | --- | --- |
| `urgency_marker_count` | 4.00 | 0.64 | +3.69 SD |
| `persuasion_lever_count` | 5.00 | 1.67 | +3.68 SD |
| `fast_digital_onboarding_claim` | 0.67 | 0.15 | +1.42 SD |
| `page_height_px` | 11,149 | 6,412 | +1.42 SD |
| `background_luminance` | 0.55 | 0.34 | +1.40 SD |
| `value_prop_clarity` | 5.00 | 3.97 | +1.36 SD |

ING's dated deadlines ("avant le 11/10/2026") count as urgency markers since the
rule was extended to dates. Whether this reads as energetic or as pressure to a
visitor is a question the data cannot answer.

ING's pages are bright, not dark: first-screen luminance is 0.55 against 0.34 for
the peers. The challengers are darkest (bunq 0.04, Revolut 0.09).

## 3. Traditional banks and challengers argue differently

Cohen's d is used to rank features, not as a test (10 against 4 banks):

- Page brightness: traditional 0.43, challenger 0.17 (d = -2.36).
- Shows a rate: 0% against 50% (d = +2.00).
- Frames tiers as a subscription (`subscription_style_framing`): 0% against 50% (d = +2.00).
- Expat targeting: 7% against 50% (d = +1.23).
- Hero image area ratio: 0.25 against 0.62 (d = +1.49).

## 4. ING reaches its audiences page by page

ING's three current-account pages name 3 of the 8 personas: mass market, student
and expat. Revolut names four on one page, the widest. Most other banks name
one, mass market. ING speaks to several audiences by giving each its own page, so
the question for ING is routing, not copy: does the right customer land on the
right page?

## 5. AI Score: digital and bundled, thin on trust

ING scores digital 8.9, bundled offer 10.0, personalisation 3.8, simplicity 2.5
and trust 0.0 (out of 10). Trust measures three signals (institutional tenure,
a prominent regulatory disclosure, the branch network cited as a benefit). A zero
says they are absent from the page, not that ING is untrusted. KBC also scores
0.0. `innovation` is withdrawn and empty for every bank.

## 6. Search interest

Google Trends by region: KBC and Argenta peak in Flanders, BNP Paribas Fortis,
Crelan and Belfius in Wallonia. ING peaks in Brussels (100, Wallonia 98), like
Revolut, N26 and bunq. This is search interest, not campaign performance.

## What cannot be said

- The kickoff deck's five impressions do not survive: four are not testable
  (every bank falls in the same word-count band, and the animation feature is
  withdrawn), and "ING no longer places text next to picture" is not supported
  ("beside" is still its most common layout).
- `cta_count`, `cta_contrast_ratio`, `has_animation`, `animated_asset_count`
  and `has_comparison_table` are withdrawn (see `docs/decisions.md`). Do not quote them.
- The point to take into the room: ING's page stacks urgency, persuasion, digital
  and cross-sell signals that rarely travel together, with no trust signals. Is
  that a deliberate repositioning, or several separate choices that added up?
