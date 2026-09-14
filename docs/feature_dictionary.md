# Banking Campaigns Comparator - Feature Dictionary

> Generated from `config/feature_dictionary.yaml` by `scripts/build_feature_docs.py`.
> Edit the YAML, never this file.

**Version** 0.1.0 · **Status** draft · **Date** 2026-09-14  
**Owner** Stephane (Analysis & Generative AI Lead)  
**Grain** One row per campaign page per capture date.  
**Freeze target** End of Day 2 - Tuesday 15 September 2026

67 features — 53 core, 14 extended.

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

*DR-02, DR-05, LC-01* — 13 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `page_id` | string | automatic | cross_language | core | Unique key for the page-capture. Format {bank}_{product_family}_{language}_{nn}. |
| `bank` | categorical<br>`ing` · `kbc` · `bnp_paribas_fortis` · `argenta` · `crelan` · `belfius` · `revolut` · `n26` · `bunq` | automatic | cross_language | core | Bank whose page this is. |
| `bank_category` | categorical<br>`traditional` · `challenger` | automatic | cross_language | core | Traditional incumbent or digital challenger. The axis BO-02 asks about. |
| `product_family` | categorical<br>`term_account` · `current_account_pack` · `savings_account` · `mortgage` · `investment` · `other` | automatic | cross_language | core | Product family the page promotes. Comparisons are only valid within one family (DR-04). |
| `page_role` | categorical<br>`campaign_landing` · `product_detail` · `comparison` · `other` | automatic | cross_language | extended | What the page is for within the funnel. |
| `url` | string | automatic | cross_language | core | Full source URL as fetched. |
| `language` | categorical<br>`nl` · `fr` · `en` | automatic | cross_language | core | Language of the page version captured.<br>*Controls every within_language feature. Fixing one language is decision 2 in the plan.* |
| `captured_at` | datetime | automatic | cross_language | core | UTC timestamp of the fetch. Every conclusion is valid for this date only. |
| `collection_method` | categorical<br>`static_fetch` · `headless_render` | automatic | cross_language | core | How the page was retrieved. Static fetch misses JavaScript-built layout (risk R-02). |
| `robots_allowed` | boolean | automatic | cross_language | core | Whether robots.txt allowed this path for the user agent used, checked before fetching. Carried in the row so compliance evidence travels with the data (LC-01).<br>*A row with robots_allowed = false must never exist. The validator treats it as a hard error.* |
| `snapshot_html_path` | string | automatic | cross_language | core | Relative path to the stored raw HTML snapshot. |
| `screenshot_path` | string | automatic | cross_language | core | Relative path to the stored full-page screenshot. |
| `data_source` | categorical<br>`real` · `synthetic_fixture` · `llm_generated` | automatic | cross_language | core | Whether the row is a real capture or a synthetic fixture row. Guards against fixture data reaching a finding.<br>*llm_generated marks a campaign produced in the stretch step, scored by the same extractor.* |

## Tone & messaging

*PRD section 11 - "Is it formal, simple, persuasive?"* — 13 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `word_count` | integer<br>[0, ∞] | automatic | within_language | core | Visible words in the page body, excluding navigation, footer and cookie banner.<br>*The deck calls Belfius "pretty verbose" and Revolut "very few text". This is the test.* |
| `sentence_count` | integer<br>[0, ∞] | automatic | within_language | extended | Number of sentences in the page body. |
| `avg_sentence_length` | float<br>[0, ∞] | automatic | within_language | core | Mean words per sentence. |
| `readability_score` | float | automatic | within_language | core | Readability index of the body text. Higher means easier.<br>*Formula differs per language - see readability_formula. Raw scores are NOT comparable across languages; use readability_band for cross-language work.* |
| `readability_formula` | categorical<br>`flesch_douma_nl` · `kandel_moles_fr` · `flesch_reading_ease_en` | automatic | cross_language | core | Which readability formula produced readability_score. |
| `readability_band` | categorical<br>`very_easy` · `easy` · `medium` · `hard` · `very_hard` | derived | cross_language | core | Readability score bucketed into language-neutral bands, so it can cross languages. |
| `second_person_ratio` | float<br>[0, 1] | automatic | within_language | core | Share of personal pronouns that address the reader (je/u/jij, vous/tu, you).<br>*Direct address is a known challenger-bank marker. Cheap to compute, high signal.* |
| `first_person_plural_count` | integer<br>[0, ∞] | automatic | within_language | extended | Occurrences of bank-as-we pronouns (wij/we, nous, we/our). |
| `question_count` | integer<br>[0, ∞] | automatic | cross_language | extended | Number of question marks in body text. |
| `urgency_marker_count` | integer<br>[0, ∞] | automatic | cross_language | core | Occurrences of scarcity or deadline language, matched against a per-language term list (only until, limited offer, nog tot, offre limitee, ...).<br>*The ING term-account promo in the deck carries "This offer is only available until 13/10/2025".* |
| `numeric_claim_count` | integer<br>[0, ∞] | automatic | cross_language | core | Count of numeric claims in body text (percentages, amounts, durations). |
| `formality_score` | integer<br>[1, 5] | rubric | cross_language | core | How formal the register is. 1 = conversational, 5 = institutional. |
| `clarity_score` | integer<br>[1, 5] | rubric | cross_language | extended | How easily a first-time reader grasps the offer. 1 = opaque, 5 = immediate. |

### Rubric — `formality_score`

- **1** — Speaks like a friend. Contractions, slang, direct address throughout.
- **2** — Informal but composed. Direct address, short sentences, no jargon.
- **3** — Neutral business register.
- **4** — Formal. Full forms of address, product and regulatory vocabulary.
- **5** — Institutional and legalistic. Reads like a product sheet.

## Topics & value proposition

*PRD section 11 - "What is being offered? How is it framed?"* — 9 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `primary_product` | string | model_assisted | cross_language | core | The specific product named on the page, in the page's own words. |
| `rate_shown` | boolean | automatic | cross_language | core | Whether an interest rate or price is displayed on the page. |
| `rate_value_pct` | float<br>[0, ∞] | automatic | within_capture_window | core | The headline rate as a percentage, when one is shown.<br>*Rates move. Only comparable between pages captured in the same window.* |
| `rate_prominence` | categorical<br>`hero` · `above_fold` · `below_fold` · `absent` | rubric | cross_language | core | Where the rate sits in the visual hierarchy. |
| `benefit_framing` | categorical<br>`rational` · `emotional` · `mixed` | rubric | cross_language | core | Whether the offer is argued with figures, with feelings, or both. |
| `fab_level` | categorical<br>`feature` · `advantage` · `benefit` | rubric | cross_language | core | Dominant level of the feature-advantage-benefit ladder. "3.2% gross annual" is a feature; "your money works while you sleep" is a benefit. |
| `value_prop_clarity` | integer<br>[1, 5] | rubric | cross_language | extended | How clearly the page states what is offered, to whom, against which alternative. |
| `disclaimer_present` | boolean | automatic | cross_language | extended | Whether legal or risk disclaimers appear on the page. |
| `disclaimer_word_share` | float<br>[0, 1] | automatic | within_language | extended | Share of body words that sit inside disclaimer blocks. |

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
| `accent_locations` | list[string]<br>`text` · `icons` · `imagery` · `background` · `buttons` | rubric | cross_language | core | Where the brand accent actually appears.<br>*Directly tests the deck's distinction - Fortis uses green "in text and icons, not in pictures", Belfius uses red "in text and pictures".* |
| `background_luminance` | float<br>[0, 1] | automatic | cross_language | core | Mean relative luminance of the page background. 0 = black, 1 = white.<br>*Separates dark-themed challengers (Revolut "deep blue and dark") from white incumbent pages.* |
| `cta_contrast_ratio` | float<br>[1, 21] | automatic | cross_language | extended | WCAG contrast ratio between the primary call-to-action and its background. |

## Layout & structure

*PRD section 11 - "Is the page easy to read? How is it organised?"* — 9 features

| Feature | Type | Extraction | Comparability | Tier | Definition |
| --- | --- | --- | --- | --- | --- |
| `page_height_px` | integer<br>[0, ∞] | automatic | cross_language | core | Full rendered page height at a fixed 1440x900 viewport.<br>*Viewport must be identical for every capture or this feature is meaningless.* |
| `section_count` | integer<br>[0, ∞] | automatic | cross_language | core | Number of distinct content blocks on the page. |
| `cta_count` | integer<br>[0, ∞] | automatic | cross_language | core | Number of distinct call-to-action buttons or links. |
| `cta_above_fold` | boolean | automatic | cross_language | core | Whether at least one call to action is visible without scrolling. |
| `text_image_adjacent` | boolean | rubric | cross_language | core | Whether the dominant pattern places text and image side by side, rather than stacking them vertically.<br>*The single observation the deck repeats for every bank. ING is called out as the one where "text and picture not anymore next to each other".* |
| `text_to_image_ratio` | float<br>[0, ∞] | automatic | within_language | core | Text area divided by image area in the rendered page. |
| `above_fold_element_count` | integer<br>[0, ∞] | automatic | cross_language | extended | Number of distinct interactive or content elements visible without scrolling. |
| `has_comparison_table` | boolean | automatic | cross_language | extended | Whether the page contains a product comparison table. |
| `layout_archetype` | categorical<br>`hero_stacked` · `split_columns` · `card_grid` · `long_form` | rubric | cross_language | core | Overall structural pattern of the page. |

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
