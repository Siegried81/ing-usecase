# Banking Campaigns Comparator - Feature Dictionary

> Generated from `config/feature_dictionary.yaml` by `scripts/build_feature_docs.py`.
> Edit the YAML, never this file.

**Version** 0.1.0 · **Status** draft · **Date** 2026-09-14  
**Owner** Stephane (Analysis & Generative AI Lead)  
**Grain** One row per campaign page per capture date.  
**Freeze target** End of Day 2 - Tuesday 15 September 2026

104 features — 66 core, 38 extended.

## How to read the tables

| Column | Meaning |
| --- | --- |
| **Extraction** | How the value is produced, and therefore how much it can be trusted. |
| **Comparability** | How far the value travels. `within_language` values cannot cross NL/FR/EN. |
| **Tier** | `core` is the Day 6 MVP minimum; `extended` is added only after the gate passes. |

- **automatic** (trust: high, owner: Dan) — Computed by code, deterministic, reproducible exactly.
- **rubric** (trust: medium, owner: Siegried) — Scored by a human against a written scale with defined levels.
- **model_assisted** (trust: medium, owner: Stephane) — Produced by an LLM or vision model with the prompt and model version recorded.
- **derived** (trust: high, owner: Stephane) — Computed from other features in this dictionary. Never entered by hand.

## Provenance & compliance

*DR-02, DR-05, LC-01* — 18 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `page_id` | string | automatic | cross_language | core | Unique key for the page-capture. Format {bank}_{product_family}_{language}_{nn}. |
| `bank` | categorical<br>`ing` · `kbc` · `bnp_paribas_fortis` · `argenta` · `crelan` · `belfius` · `revolut` · `n26` · `bunq` · `vdk` · `hellobank` · `beobank` · `cbc` · `keytrade` | automatic | cross_language | core | Bank whose page this is. |
| `bank_category` | categorical<br>`traditional` · `challenger` | automatic | cross_language | core | Traditional incumbent or digital challenger. The axis BO-02 asks about. |
| `product_family` | categorical<br>`term_account` · `current_account_pack` · `savings_account` · `mortgage` · `investment` · `pension` · `other` | automatic | cross_language | core | Product family the page promotes. Comparisons are only valid within one family (DR-04). |
| `page_role` | categorical<br>`campaign_landing` · `product_detail` · `comparison` · `other` | automatic | cross_language | extended | What the page is for within the funnel. |
| `url` | string | automatic | cross_language | core | Full source URL as fetched. |
| `language` | categorical<br>`nl` · `fr` · `en` | automatic | cross_language | core | Language of the page version captured.<br>*Controls every within_language feature. Fixing one language is decision 2 in the plan.* |
| `captured_at` | datetime | automatic | cross_language | core | UTC timestamp of the fetch. Every conclusion is valid for this date only. |
| `collection_method` | categorical<br>`static_fetch` · `headless_render` · `headful_render` · `manual_capture` | automatic | cross_language | core | How the page was retrieved. Static fetch misses JavaScript-built layout (risk R-02). manual_capture is a page a person opened in a normal browser and saved, used where an edge/CDN declines automated traffic - the content is identical, but there is no HTTP status of our own and the capture time is the person's, not the pipeline's. |
| `robots_allowed` | boolean | automatic | cross_language | core | Whether robots.txt allowed this path for the user agent used, checked before fetching. Carried in the row so compliance evidence travels with the data (LC-01).<br>*A row with robots_allowed = false must never exist. The validator treats it as a hard error.* |
| `snapshot_html_path` | string | automatic | cross_language | core | Relative path to the stored raw HTML snapshot. |
| `screenshot_path` | string | automatic | cross_language | core | Relative path to the stored full-page screenshot. |
| `data_source` | categorical<br>`real` · `synthetic_fixture` · `llm_generated` | automatic | cross_language | core | Whether the row is a real capture or a synthetic fixture row. Guards against fixture data reaching a finding.<br>*llm_generated marks a campaign produced in the stretch step, scored by the same extractor.* |
| `extraction_model` | string | automatic | cross_language | core | Provider and model that produced the model_assisted fields for this row, as "provider/model". Blank for rows with no model-assisted features.<br>*Comparisons are only fair when every bank was labelled by the same model. A dataset mixing models is not invalid, but the mix has to be reported as a limitation (D-09) rather than discovered afterwards.* |
| `capture_quality` | categorical<br>`ok` · `suspect` · `unusable` | automatic | cross_language | core | Whether the captured page looks like a real campaign page. 'unusable' means an error/maintenance page or a shell that never rendered its content, and the row must be excluded from analysis.<br>*Deliberately conservative - a genuinely short challenger page is 'suspect', not 'unusable'. Only unambiguous cases are excluded automatically.* |
| `http_status` | integer<br>[100, 599] | automatic | cross_language | core | HTTP status returned when the page was fetched. Anything other than 2xx is not a campaign page. |
| `shadow_hosts_flattened` | integer<br>[0, ∞] | automatic | cross_language | core | Number of shadow roots inlined into the HTML before extraction. Above zero means the page is built from web components and would have been largely invisible to a light-DOM-only extractor. |
| `capture_quality_note` | string | automatic | cross_language | core | Why capture_quality got that verdict, in words, for the limitations section. |

## Tone & messaging

*PRD section 11 - "Is it formal, simple, persuasive?"* — 18 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `word_count` | integer<br>[0, ∞] | automatic | within_language | core | Visible words in the page body, excluding navigation, footer and cookie banner.<br>*The deck calls Belfius "pretty verbose" and Revolut "very few text". This is the test.* |
| `sentence_count` | integer<br>[0, ∞] | automatic | within_language | extended | Number of sentences in the page body. |
| `avg_sentence_length` | float<br>[0, ∞] | automatic | within_language | core | Mean words per sentence. |
| `readability_score` | float | automatic | within_language | core | Readability index of the body text. Higher means easier.<br>*Formula differs per language - see readability_formula. Raw scores are NOT comparable across languages; use readability_band for cross-language work.* |
| `readability_formula` | categorical<br>`flesch_douma_nl` · `kandel_moles_fr` · `flesch_reading_ease_en` | automatic | cross_language | core | Which readability formula produced readability_score. |
| `readability_band` | categorical<br>`very_easy` · `easy` · `medium` · `hard` · `very_hard` | derived | cross_language | core | Readability score bucketed into language-neutral bands, so it can cross languages. |
| `word_count_band` | categorical<br>`very_short` · `short` · `medium` · `long` | derived | cross_language | core | word_count bucketed into fixed-threshold bands, so it can be compared across languages.<br>*same idea as readability_band, but fixed universal cutoffs rather than a language-normalising formula (word_count has no such formula). REDUCES the cross-language comparability problem, does not eliminate it - French runs ~15-20% longer than English for the same content. See src/comparator/bands.py for the thresholds.* |
| `sentence_count_band` | categorical<br>`very_short` · `short` · `medium` · `long` | derived | cross_language | extended | sentence_count bucketed into fixed-threshold bands, so it can be compared across languages.<br>*same caveat as word_count_band.* |
| `avg_sentence_length_band` | categorical<br>`short_sentences` · `medium_sentences` · `long_sentences` | derived | cross_language | core | avg_sentence_length bucketed into fixed-threshold bands, so it can be compared across languages.<br>*same caveat as word_count_band.* |
| `second_person_ratio_band` | categorical<br>`rarely_direct` · `sometimes_direct` · `mostly_direct` | derived | cross_language | core | second_person_ratio bucketed into fixed-threshold bands, so it can be compared across languages.<br>*a ratio travels a little better across languages than a raw count, banded anyway for consistency with the rest of this set.* |
| `first_person_plural_band` | categorical<br>`rare` · `occasional` · `frequent` | derived | cross_language | extended | first_person_plural_count bucketed into fixed-threshold bands, so it can be compared across languages.<br>*same caveat as word_count_band.* |
| `second_person_ratio` | float<br>[0, 1] | automatic | within_language | core | Share of personal pronouns that address the reader (je/u/jij, vous/tu, you).<br>*Direct address is a known challenger-bank marker. Cheap to compute, high signal.* |
| `first_person_plural_count` | integer<br>[0, ∞] | automatic | within_language | extended | Occurrences of bank-as-we pronouns (wij/we, nous, we/our). |
| `question_count` | integer<br>[0, ∞] | automatic | cross_language | extended | Number of question marks in body text. |
| `urgency_marker_count` | integer<br>[0, ∞] | automatic | cross_language | core | Occurrences of scarcity or deadline language, matched against a per-language term list (only until, limited offer, nog tot, offre limitee, ...).<br>*year corrected. The ING term-account promo carries "This offer is only available until 13/10/2026".* |
| `numeric_claim_count` | integer<br>[0, ∞] | automatic | cross_language | core | Count of numeric claims in body text (percentages, amounts, durations). |
| `formality_score` | integer<br>[1, 5] | rubric | cross_language | core | How formal the register is. 1 = conversational, 5 = institutional. |
| `clarity_score` | integer<br>[1, 5] | rubric | cross_language | extended | How easily a first-time reader grasps the offer. 1 = opaque, 5 = immediate. |

### Rubric — `formality_score`

- **1** — Speaks like a friend. Contractions, slang, direct address throughout.
- **2** — Informal but composed. Direct address, short sentences, no jargon.
- **3** — Neutral business register.
- **4** — Formal. Full forms of address, product and regulatory vocabulary.
- **5** — Institutional and legalistic. Reads like a product sheet.

### Rubric — `clarity_score`

- **1** — Can't tell what's being offered without reading twice.
- **2** — Vague - the product is named but the offer itself (rate, benefit, condition) is unclear.
- **3** — Understandable with effort - the offer is there but buried among secondary information.
- **4** — Clear - offer, audience and next step are identifiable at a glance.
- **5** — Immediate - the value proposition is unmistakable within the first few seconds.

## Topics & value proposition

*PRD section 11 - "What is being offered? How is it framed?"* — 10 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `disclaimer_word_share_band` | categorical<br>`minimal` · `moderate` · `heavy` | derived | cross_language | extended | disclaimer_word_share bucketed into fixed-threshold bands, so it can be compared across languages.<br>*same caveat as word_count_band.* |
| `primary_product` | string | model_assisted | cross_language | core | The specific product named on the page, in the page's own words. |
| `rate_shown` | boolean | automatic | cross_language | core | Whether an interest rate or price is displayed on the page. |
| `rate_value_pct` | float<br>[0, ∞] | automatic | within_capture_window | core | The headline rate as a percentage, when one is shown.<br>*Rates move. Only comparable between pages captured in the same window.* |
| `rate_prominence` | categorical<br>`hero` · `above_fold` · `below_fold` · `absent` | rubric | cross_language | core | Where the rate sits in the visual hierarchy. |
| `benefit_framing` | categorical<br>`rational` · `emotional` · `mixed` | model_assisted | cross_language | core | Whether the offer is argued with figures, with feelings, or both. |
| `fab_level` | categorical<br>`feature` · `advantage` · `benefit` | model_assisted | cross_language | core | Dominant level of the feature-advantage-benefit ladder. "3.2% gross annual" is a feature; "your money works while you sleep" is a benefit. |
| `value_prop_clarity` | integer<br>[1, 5] | rubric | cross_language | extended | How clearly the page states what is offered, to whom, against which alternative. |
| `disclaimer_present` | boolean | automatic | cross_language | extended | Whether legal or risk disclaimers appear on the page. |
| `disclaimer_word_share` | float<br>[0, 1] | automatic | within_language | extended | Share of body words that sit inside disclaimer blocks. |

### Rubric — `rate_prominence`

- **above_fold** — The rate is visible without scrolling, but is not the dominant visual element.
- **absent** — No rate is shown anywhere on the page.
- **below_fold** — The rate only appears after scrolling.
- **hero** — The rate is the largest or most visually dominant element on the page.

### Rubric — `value_prop_clarity`

- **1** — No stated value proposition - reads like a product description, not an offer.
- **2** — What is offered is named, but who it is for and the alternative are absent.
- **3** — What and who are clear, but the implied alternative is absent or only implicit.
- **4** — What, who and the implied alternative are all identifiable.
- **5** — What, who and the alternative are explicit and quantified.

## Visuals & illustrations

*PRD section 11 - "What kind of images are used? What do they show?"* — 9 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `image_count` | integer<br>[0, ∞] | automatic | cross_language | core | Number of content images, excluding icons under 32px and tracking pixels. |
| `hero_image_present` | boolean | automatic | cross_language | core | Whether a single large image occupies the top of the page.<br>*The deck says Fortis and ING both lead with "1 very large picture on the top".* |
| `hero_image_area_ratio` | float<br>[0, 1] | automatic | cross_language | extended | Hero image area as a share of the above-the-fold viewport. |
| `total_image_area_ratio` | float<br>[0, 1] | automatic | cross_language | core | Combined image area as a share of total page area.<br>*Tests the deck's "large images everywhere" claim about Revolut.* |
| `animated_asset_count` | integer<br>[0, ∞] | automatic | cross_language | core | Number of animated assets (GIF, video, Lottie, CSS keyframe animation). |
| `has_animation` | boolean | derived | cross_language | core | Whether the page contains any motion at all.<br>*The deck's sharpest ING-vs-peers claim - ING has "partially animated figures and blinging gif" while the other three traditional banks are "static pictures".* |
| `dominant_image_type` | categorical<br>`photo` · `illustration` · `render_3d` · `icon_only` · `none` | model_assisted | cross_language | core | The visual register of the imagery.<br>*Revolut is described as "3D Animated pictures" - render_3d should separate it from the incumbents.* |
| `people_present` | boolean | model_assisted | cross_language | core | Whether any image shows people. |
| `imagery_register` | categorical<br>`lifestyle` · `product` · `abstract` · `mixed` · `none` | model_assisted | cross_language | extended | What the imagery depicts. |

## Colours & design

*PRD section 11 - "How is attention guided? What stands out?"* — 7 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `dominant_colour_hex` | string | automatic | cross_language | core | Most frequent non-neutral colour in the rendered page. |
| `palette_hex` | list[string] | automatic | cross_language | core | Top five colours by pixel share, most frequent first. |
| `brand_colour_share` | float<br>[0, 1] | automatic | cross_language | core | Share of coloured pixels within tolerance of the bank's primary brand colour.<br>*The deck's claim that ING uses "not only orange" is measurable here.* |
| `accent_colour_count` | integer<br>[0, ∞] | automatic | cross_language | extended | Number of distinct accent colours used for emphasis. |
| `accent_locations` | list[string]<br>`text` · `icons` · `imagery` · `background` · `buttons` | rubric | cross_language | core | Where the brand accent actually appears.<br>*Directly tests the deck's distinction - Fortis uses green "in text and icons, not in pictures", Belfius uses red "in text and pictures". this is a perceptual judgement call, independent from the automatic brand_colour_share (strict pixel-distance match on the hero image only). The two are expected to disagree sometimes - e.g. a human says "yes, accent in imagery" for a subtle tint that brand_colour_share's Euclidean tolerance doesn't count. Do not try to reconcile them; report both, a mismatch between "looks branded" and "measures as branded" is itself a finding.* |
| `background_luminance` | float<br>[0, 1] | automatic | cross_language | core | Mean relative luminance of the page background. 0 = black, 1 = white.<br>*Separates dark-themed challengers (Revolut "deep blue and dark") from white incumbent pages.* |
| `cta_contrast_ratio` | float<br>[1, 21] | automatic | cross_language | extended | WCAG contrast ratio between the primary call-to-action and its background. |

### Rubric — `accent_locations`

- **background** — Accent colour used as a section or page background.
- **buttons** — Accent colour used on call-to-action buttons or other interactive elements.
- **icons** — Accent colour used on icons or small graphic markers.
- **imagery** — Accent colour appears within the photos, illustrations or renders themselves.
- **text** — Accent colour used on headlines or body text.

## Layout & structure

*PRD section 11 - "Is the page easy to read? How is it organised?"* — 11 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `text_to_image_ratio_band` | categorical<br>`image_heavy` · `balanced` · `text_heavy` | derived | cross_language | core | text_to_image_ratio bucketed into fixed-threshold bands, so it can be compared across languages.<br>*same caveat as word_count_band; also inherits the text_to_image_ratio approximation noted in collection/scraper.py for static_fetch rows.* |
| `page_height_px` | integer<br>[0, ∞] | automatic | cross_language | core | Full rendered page height at a fixed 1440x900 viewport.<br>*Viewport must be identical for every capture or this feature is meaningless. widened to nullable. A manually saved capture (collection_method = manual_capture) carries a VIEWPORT screenshot, not a full-page one, so the page height genuinely cannot be measured from it - Siegried's saves are ~1,000px tall for pages we measure live at 12,000px. Deriving a height from them would be inventing one. Blank is the honest value, and the feature accounting already drops a feature that is missing for some bank.* |
| `section_count` | integer<br>[0, ∞] | automatic | cross_language | core | Number of distinct content blocks on the page. |
| `cta_count` | integer<br>[0, ∞] | automatic | cross_language | core | Number of distinct call-to-action buttons or links. |
| `cta_above_fold` | boolean | automatic | cross_language | core | Whether at least one call to action is visible without scrolling. |
| `text_image_layout` | categorical<br>`beside` · `stacked` · `overlaid` | rubric | cross_language | core | How the dominant pattern relates text and image: side by side (beside), one above the other (stacked), or text written directly on top of the image (overlaid, e.g. a full-bleed hero photo with a headline over it).<br>*The single observation the deck repeats for every bank. ING is called out as the one where "text and picture not anymore next to each other". no "no_image" value on purpose - a page with no image at all leaves this field null (nullable: true), it is not forced into one of the three categories above.* |
| `text_to_image_ratio` | float<br>[0, ∞] | automatic | within_language | core | Text area divided by image area in the rendered page. |
| `above_fold_element_count` | integer<br>[0, ∞] | automatic | cross_language | extended | Number of distinct interactive or content elements visible without scrolling. |
| `has_comparison_table` | boolean | automatic | cross_language | extended | Whether the page contains a product comparison table. |
| `layout_archetype` | categorical<br>`hero_stacked` · `split_columns` · `card_grid` · `long_form` | rubric | cross_language | core | Overall structural pattern of the page.<br>*real pages often mix patterns (e.g. a hero_stacked header over a card_grid body) - score the pattern of the FIRST SCREEN (above the fold), not the page as a whole, so raters have one consistent rule.* |
| `mobile_first_design_signal` | boolean | rubric | cross_language | extended | Whether the page's visual design reads as built mobile-first (single-column cards, large tap targets, minimal above-fold density) rather than desktop-first (multi-column, hover-dependent, dense), judged from the desktop screenshot. Not a responsive/viewport measurement - this project only captures one fixed viewport. |

### Rubric — `text_image_layout`

- **beside** — Text and image sit side by side, both fully visible (e.g. photo left, text block right).
- **overlaid** — Text is written directly on top of the image (e.g. a full-bleed hero photo with a headline over it).
- **stacked** — Image and text follow each other vertically, not overlapping.

### Rubric — `layout_archetype`

- **card_grid** — Content is organised as a grid of self-contained cards or tiles.
- **hero_stacked** — One large hero visual at the top, content stacked vertically below it.
- **long_form** — Continuous scrolling sections with no strong grid or card structure.
- **split_columns** — The page is organised into two or more side-by-side columns throughout.

### Rubric — `mobile_first_design_signal`

- **False** — Multi-column layout, dense information, hover-dependent interactions.
- **True** — Single-column, card-like blocks, large tap-friendly buttons, minimal density above the fold.

## Marketing principles

*Plan section 4.3 - AIDA, Cialdini, feature-advantage-benefit* — 7 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `aida_attention` | boolean | rubric | cross_language | core | Does the page open with something that stops the reader? |
| `aida_interest` | boolean | rubric | cross_language | core | Does it give a reason to keep reading beyond the headline? |
| `aida_desire` | boolean | rubric | cross_language | core | Does it make the offer feel worth having, not just understood? |
| `aida_action` | boolean | rubric | cross_language | core | Is there an unmistakable next step? |
| `aida_coverage_score` | integer<br>[0, 4] | derived | cross_language | core | How many of the four AIDA stages the page covers. |
| `persuasion_levers` | list[string]<br>`reciprocity` · `commitment` · `social_proof` · `authority` · `liking` · `scarcity` | rubric | cross_language | core | Which of Cialdini's six persuasion principles are used on the page.<br>*Turns the vague word "persuasive" into a closed, countable list.* |
| `persuasion_lever_count` | integer<br>[0, 6] | derived | cross_language | core | Number of distinct persuasion levers detected. |

### Rubric — `aida_attention`

- **False** — The opening is generic enough that skipping it would lose nothing.
- **True** — Something on the first screen (headline, visual, number) is genuinely arresting, not generic.

### Rubric — `aida_interest`

- **False** — The page front-loads everything, or gives no reason to continue past the first line.
- **True** — There is a reason to keep reading beyond the headline - a specific detail, a question, a hinted benefit.

### Rubric — `aida_desire`

- **False** — The page states facts (rate, features) without making the reader want the outcome.
- **True** — The offer is made to feel worth having - concrete benefit, social proof or emotional payoff, not only a spec sheet.

### Rubric — `aida_action`

- **False** — No clear call to action, or several CTAs competing for the same visitor with no clear way to tell which applies.
- **True** — There is one unmistakable next step - a single call to action, or several CTAs clearly segmented by audience/situation so each visitor still has exactly one obvious path (e.g. "not retired yet" vs "already retired").


### Rubric — `persuasion_levers`

- **authority** — The page invokes expertise, credentials, regulator backing, or institutional tenure.
- **commitment** — The page asks for a small first step that implies a larger one.
- **liking** — The page uses a friendly tone, relatable imagery, or a likeable brand voice to build affinity.
- **reciprocity** — The page offers something free or upfront before asking for commitment.
- **scarcity** — The page uses deadlines, limited availability, or "only until" language.
- **social_proof** — The page cites other customers, ratings, review counts, or user numbers.

## Banking-domain signals (Siegried's addendum)

*PRD section 11 bis / Plan section 4.3 bis - retail-banking angles a generic marketing framework misses* — 24 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `audience_segment` | categorical<br>`retail` · `professional` · `mixed` | model_assisted | cross_language | core | Whether the page addresses an individual, a professional/self-employed activity, or both.<br>*retail vs pro is a different axis than traditional vs challenger; most banks run both but frame differently.* |
| `is_bundled_offer` | boolean | model_assisted | cross_language | extended | Whether the page pushes a bundle (account + card + insurance + investment) in the same funnel, rather than one isolated product.<br>*the bancassurance model (bundled) vs single-product neobank is a business-model signal, not a tone or design choice.* |
| `cross_sell_delivery_model` | categorical<br>`internal_advisor_led` · `partner_addon_digital` · `not_applicable` | model_assisted | cross_language | extended | How a cross-sold product (insurance, investment) is delivered when one is offered - an in-house product with a dedicated advisor (bancassurance), a digital add-on distributed through a third-party partner with no advisor, or not applicable (nothing cross-sold on this page). |
| `target_personas` | list[string]<br>`student` · `family` · `entrepreneur_self_employed` · `expat` · `investor` · `retiree` · `digital_nomad` · `mass_market` | model_assisted | cross_language | extended | Which customer persona archetypes this page's copy/imagery explicitly addresses. |
| `cross_sold_products` | list[string]<br>`term_account` · `current_account_pack` · `savings_account` · `mortgage` · `investment` · `pension` · `insurance` · `credit_card` · `partner_perk` · `other` | model_assisted | cross_language | extended | Other products this page cross-sells or cross-references alongside its own product_family. Not limited to banking families: a page that pitches insurance, a credit card or a partner perk is cross-selling, and collapsing those into `other` counts a page naming ten add-ons the same as one naming a single unknown. |
| `subscription_style_framing` | boolean | model_assisted | cross_language | extended | Whether the account tiers are framed as a subscription/plan (like a phone or streaming service) rather than a traditional banking "pack". |
| `rate_framing` | categorical<br>`base_rate` · `promo_bonus` · `capped_tiered` · `not_shown` | model_assisted | within_capture_window | core | Whether the headline rate is the regulated base rate, a promotional bonus, a capped/tiered rate presented as the full rate, or no rate is shown.<br>*complements rate_shown/rate_value_pct/rate_prominence (which measure IF and WHERE a rate appears) with WHAT KIND of rate it is. Belgian savings accounts are legally a base rate (>=0.50%) plus a fidelity/growth premium; a "capped_tiered" rate ("up to X%") applying only to a low ceiling or a short window is a known framing tactic.* |
| `primary_cta_type` | categorical<br>`self_service_online` · `book_advisor_or_branch` · `other` | model_assisted | cross_language | core | Whether the primary call to action is self-service online, booking an advisor/branch visit, or something else.<br>*a distribution-model signal; a neobank structurally cannot offer book_advisor_or_branch.* |
| `switching_framing` | categorical<br>`retention_reassurance` · `acquisition_encouragement` · `not_applicable` | model_assisted | cross_language | extended | Whether the message reassures against switching away (retention) or actively encourages switching in (acquisition), if applicable at all.<br>*Belgium's bank-switching service makes this a concrete, mesurable framing choice, not a vague "tone".* |
| `regulatory_disclosure_prominence` | categorical<br>`prominent` · `present_not_prominent` · `absent` · `not_applicable` | model_assisted | cross_language | core | How visible the mandated disclosure THAT APPLIES TO THIS PAGE'S product_family is: APR/TAEG for mortgage, the deposit guarantee scheme for term_account/savings_account, a capital-at-risk warning for investment. not_applicable when no such disclosure is expected for this product_family (e.g. a plain current_account_pack with no credit component) - do not score it "absent" in that case, absent is reserved for a disclosure that IS expected but isn't shown.<br>*distinct from disclaimer_present/disclaimer_word_share (which measure raw presence and word share automatically): this judges whether disclosures are placed where a reader will actually see them, which is what a compliance reviewer cares about.* |
| `hidden_conditions_behind_free_claim` | boolean | model_assisted | cross_language | extended | Whether "free" is the headline claim while conditions (minimum balance, usage requirement) sit in small print.<br>*not the deck's NPS-irritator finding (p.11's irritator is ad volume/frequency across channels, not hidden conditions behind a "free" claim, and isn't measurable from one page anyway). Stands on its own as a common banking dark pattern.* |
| `esg_claim_specificity` | categorical<br>`no_claim` · `vague_adjective_only` · `backed_by_reference_or_figure` | model_assisted | cross_language | extended | Whether a sustainability claim carries a verifiable reference or figure, is an adjective only, or is absent.<br>*recalibrated from an earlier idea of reading the SFDR Article 6/8/9 classification directly off the page; that classification lives in the KID/prospectus, rarely on a marketing page, so this coarser version is the realistic one.* |
| `green_product_specific_benefit` | boolean | model_assisted | cross_language | extended | Whether a concrete financial benefit (e.g. a rate discount) is explicitly tied to a green/energy-performance criterion, vs a generic sustainability claim.<br>*a green mortgage with an actual rate discount is a stronger signal than "we are sustainable".* |
| `mentions_loyalty_or_referral` | boolean | automatic | cross_language | extended | Whether the page advertises a loyalty programme or a referral scheme ("invite a friend").<br>*a public-page proxy for CRM/retention strategy. True CRM/personalisation data sits behind authentication and is out of reach entirely (DR-01/DR-09) - this is not a substitute for it, just the closest observable signal on a public page.* |
| `images_have_alt_text` | boolean | automatic | cross_language | extended | Whether content images on the page carry non-empty alt text. |
| `meta_title` | string | automatic | within_language | extended | The <title> tag content - what the bank prioritises for organic search, often different from the page's visual message. |
| `institutional_trust_signal_present` | boolean | model_assisted | cross_language | extended | Whether the page invokes tenure, customer count, or ownership backing (e.g. state ownership) as a trust/safety argument.<br>*e.g. Belfius is 100%% Belgian-State-owned, a safety argument unique to that bank, tracing to the 2011 Dexia/Belfius restructuring.* |
| `youth_student_targeting` | boolean | model_assisted | cross_language | extended | Whether a junior/student account or youth-oriented offer is promoted, as a long-horizon acquisition strategy. |
| `secondary_bank_positioning` | boolean | model_assisted | cross_language | extended | Whether the bank frames itself as an addition to an existing bank ("keep your current bank, add us") rather than a full replacement. |
| `expat_cross_border_targeting` | boolean | model_assisted | cross_language | extended | Whether the page targets expats/international clients (e.g. English content framed around "moving to Belgium"). |
| `branch_network_cited_as_benefit` | boolean | model_assisted | cross_language | extended | Whether the page explicitly cites physical branch/ATM network size as an advantage. |
| `fast_digital_onboarding_claim` | boolean | model_assisted | cross_language | extended | Whether the page claims a fast, frictionless digital account-opening process (e.g. "open an account in 5 minutes", no branch visit needed, instant approval).<br>*structurally unavailable to a neobank; a hard marker of business model.* |
| `first_time_investor_targeting` | boolean | model_assisted | cross_language | extended | Whether the page frames investing as a first step for a novice (e.g. "start with as little as", beginner glossary, low/no minimum) rather than assuming existing investment experience. |
| `senior_preretirement_targeting` | boolean | model_assisted | cross_language | extended | Whether the page targets a pre-retirement/senior life stage - pension planning, wealth transfer or succession, end-of-career estate management - as the entry point. |
