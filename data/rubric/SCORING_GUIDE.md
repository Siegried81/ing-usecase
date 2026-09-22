# Rubric scoring guide

> Generated from `config/feature_dictionary.yaml`. Score each page with the
> screenshot open. Leave a cell blank rather than guessing — a missing score is
> reported honestly; an invented one is not.

One named person scores every page against these scales. No second rater
and no reliability measure: that is the chosen scope of this proof of
concept, and single-judge bias is recorded as future work rather than
answered here. Write the page id you scored from, and leave a cell blank
whenever the page does not give you the evidence to fill it.

## `formality_score`

How formal the register is. 1 = conversational, 5 = institutional.

Enter a whole number from **1** to **5**.

| Level | Means |
| --- | --- |
| **1** | Speaks like a friend. Contractions, slang, direct address throughout. |
| **2** | Informal but composed. Direct address, short sentences, no jargon. |
| **3** | Neutral business register. |
| **4** | Formal. Full forms of address, product and regulatory vocabulary. |
| **5** | Institutional and legalistic. Reads like a product sheet. |

## `clarity_score`

How easily a first-time reader grasps the offer. 1 = opaque, 5 = immediate.

Enter a whole number from **1** to **5**.

| Level | Means |
| --- | --- |
| **1** | Can't tell what's being offered without reading twice. |
| **2** | Vague - the product is named but the offer itself (rate, benefit, condition) is unclear. |
| **3** | Understandable with effort - the offer is there but buried among secondary information. |
| **4** | Clear - offer, audience and next step are identifiable at a glance. |
| **5** | Immediate - the value proposition is unmistakable within the first few seconds. |

## `rate_prominence`

Where the rate sits in the visual hierarchy.

Allowed values:

- `hero`
- `above_fold`
- `below_fold`
- `absent`

| Level | Means |
| --- | --- |
| **above_fold** | The rate is visible without scrolling, but is not the dominant visual element. |
| **absent** | No rate is shown anywhere on the page. |
| **below_fold** | The rate only appears after scrolling. |
| **hero** | The rate is the largest or most visually dominant element on the page. |

## `value_prop_clarity`

How clearly the page states what is offered, to whom, against which alternative.

Enter a whole number from **1** to **5**.

| Level | Means |
| --- | --- |
| **1** | No stated value proposition - reads like a product description, not an offer. |
| **2** | What is offered is named, but who it is for and the alternative are absent. |
| **3** | What and who are clear, but the implied alternative is absent or only implicit. |
| **4** | What, who and the implied alternative are all identifiable. |
| **5** | What, who and the alternative are explicit and quantified. |

## `accent_locations`

Where the brand accent actually appears.

Allowed values:

- `text`
- `icons`
- `imagery`
- `background`
- `buttons`

| Level | Means |
| --- | --- |
| **background** | Accent colour used as a section or page background. |
| **buttons** | Accent colour used on call-to-action buttons or other interactive elements. |
| **icons** | Accent colour used on icons or small graphic markers. |
| **imagery** | Accent colour appears within the photos, illustrations or renders themselves. |
| **text** | Accent colour used on headlines or body text. |

*Directly tests the deck's distinction - Fortis uses green "in text and icons, not in pictures", Belfius uses red "in text and pictures". sieg 15/09: this is a perceptual judgement call, independent from the automatic brand_colour_share (strict pixel-distance match on the hero image only). The two are expected to disagree sometimes - e.g. a human says "yes, accent in imagery" for a subtle tint that brand_colour_share's Euclidean tolerance doesn't count. Do not try to reconcile them; report both, a mismatch between "looks branded" and "measures as branded" is itself a finding.*

## `text_image_layout`

How the dominant pattern relates text and image: side by side (beside), one above the other (stacked), or text written directly on top of the image (overlaid, e.g. a full-bleed hero photo with a headline over it).

Allowed values:

- `beside`
- `stacked`
- `overlaid`

| Level | Means |
| --- | --- |
| **beside** | Text and image sit side by side, both fully visible (e.g. photo left, text block right). |
| **overlaid** | Text is written directly on top of the image (e.g. a full-bleed hero photo with a headline over it). |
| **stacked** | Image and text follow each other vertically, not overlapping. |

*The single observation the deck repeats for every bank. ING is called out as the one where "text and picture not anymore next to each other". sieg 15/09: no "no_image" value on purpose - a page with no image at all leaves this field null (nullable: true), it is not forced into one of the three categories above.*

## `layout_archetype`

Overall structural pattern of the page.

Allowed values:

- `hero_stacked`
- `split_columns`
- `card_grid`
- `long_form`

| Level | Means |
| --- | --- |
| **card_grid** | Content is organised as a grid of self-contained cards or tiles. |
| **hero_stacked** | One large hero visual at the top, content stacked vertically below it. |
| **long_form** | Continuous scrolling sections with no strong grid or card structure. |
| **split_columns** | The page is organised into two or more side-by-side columns throughout. |

*sieg 15/09: real pages often mix patterns (e.g. a hero_stacked header over a card_grid body) - score the pattern of the FIRST SCREEN (above the fold), not the page as a whole, so raters have one consistent rule.*

## `mobile_first_design_signal`

Whether the page's visual design reads as built mobile-first (single-column cards, large tap targets, minimal above-fold density) rather than desktop-first (multi-column, hover-dependent, dense), judged from the desktop screenshot. Not a responsive/viewport measurement - this project only captures one fixed viewport.

| Level | Means |
| --- | --- |
| **False** | Multi-column layout, dense information, hover-dependent interactions. |
| **True** | Single-column, card-like blocks, large tap-friendly buttons, minimal density above the fold. |

## `aida_attention`

Does the page open with something that stops the reader?

| Level | Means |
| --- | --- |
| **False** | The opening is generic enough that skipping it would lose nothing. |
| **True** | Something on the first screen (headline, visual, number) is genuinely arresting, not generic. |

## `aida_interest`

Does it give a reason to keep reading beyond the headline?

| Level | Means |
| --- | --- |
| **False** | The page front-loads everything, or gives no reason to continue past the first line. |
| **True** | There is a reason to keep reading beyond the headline - a specific detail, a question, a hinted benefit. |

## `aida_desire`

Does it make the offer feel worth having, not just understood?

| Level | Means |
| --- | --- |
| **False** | The page states facts (rate, features) without making the reader want the outcome. |
| **True** | The offer is made to feel worth having - concrete benefit, social proof or emotional payoff, not only a spec sheet. |

## `aida_action`

Is there an unmistakable next step?

| Level | Means |
| --- | --- |
| **False** | No clear call to action, or several CTAs competing for the same visitor with no clear way to tell which applies. |
| **True** | There is one unmistakable next step - a single call to action, or several CTAs clearly segmented by audience/situation so each visitor still has exactly one obvious path (e.g. "not retired yet" vs "already retired"). |

## `persuasion_levers`

Which of Cialdini's six persuasion principles are used on the page.

Allowed values:

- `reciprocity`
- `commitment`
- `social_proof`
- `authority`
- `liking`
- `scarcity`

| Level | Means |
| --- | --- |
| **authority** | The page invokes expertise, credentials, regulator backing, or institutional tenure. |
| **commitment** | The page asks for a small first step that implies a larger one. |
| **liking** | The page uses a friendly tone, relatable imagery, or a likeable brand voice to build affinity. |
| **reciprocity** | The page offers something free or upfront before asking for commitment. |
| **scarcity** | The page uses deadlines, limited availability, or "only until" language. |
| **social_proof** | The page cites other customers, ratings, review counts, or user numbers. |

*Turns the vague word "persuasive" into a closed, countable list.*
