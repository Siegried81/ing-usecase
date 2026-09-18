"""Synthetic fixture data, so analysis code can be built before the scraper exists.

Project Plan, Day 2: "Dan publishes five hand-collected rows in the agreed format
so Stephane can start analysis code before the full scrape exists." This module is
the placeholder that unblocks day 2 - it is replaced by Dan's real rows, not merged
with them.

EVERY ROW IS INVENTED. Values are drawn from per-bank archetypes that encode the
*hypotheses* in the kickoff deck (PRD section 2.4) so the pipeline produces
plausible-shaped output. Nothing here is evidence, and every row is stamped
data_source = 'synthetic_fixture' so the validator says so out loud.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from comparator import bands
from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.schema import format_list

# Per-bank archetypes. Each value is a (mean, spread) the generator jitters around,
# or a fixed categorical. These encode the deck's CLAIMS, which is exactly what the
# real analysis is supposed to test - so never read a fixture result as confirmation.
ARCHETYPES: dict[str, dict] = {
    "ing": dict(
        category="traditional", brand="#ff6200", words=(520, 60), images=(7, 2),
        animated=(3, 1), bg=0.97, brand_share=0.14, hero=True, adjacent=False,
        img_type="photo", formality=3, layout="hero_stacked", people=True,
        accents=["text", "icons", "buttons", "imagery"], levers=["scarcity", "authority"],
        second_person=0.58, urgency=(2, 1), text_img_ratio=(2.1, 0.3), archetype_note="broad palette, some motion",
    ),
    "kbc": dict(
        category="traditional", brand="#00aeef", words=(330, 50), images=(5, 1),
        animated=(0, 0), bg=0.98, brand_share=0.11, hero=False, adjacent=True,
        img_type="photo", formality=4, layout="split_columns", people=True,
        accents=["text", "icons"], levers=["authority"],
        second_person=0.44, urgency=(1, 1), text_img_ratio=(2.6, 0.3), archetype_note="straight to the point",
    ),
    "bnp_paribas_fortis": dict(
        category="traditional", brand="#00915a", words=(610, 70), images=(6, 2),
        animated=(0, 0), bg=0.98, brand_share=0.09, hero=True, adjacent=True,
        img_type="photo", formality=4, layout="split_columns", people=True,
        accents=["text", "icons"], levers=["authority", "social_proof"],
        second_person=0.40, urgency=(1, 1), text_img_ratio=(2.9, 0.4), archetype_note="green in text and icons only",
    ),
    "argenta": dict(
        category="traditional", brand="#e94e1b", words=(470, 60), images=(4, 1),
        animated=(0, 0), bg=0.99, brand_share=0.08, hero=False, adjacent=True,
        img_type="photo", formality=4, layout="long_form", people=True,
        accents=["text", "buttons"], levers=["liking"],
        second_person=0.46, urgency=(0, 1), text_img_ratio=(3.4, 0.4), archetype_note="text-led",
    ),
    "crelan": dict(
        category="traditional", brand="#009640", words=(540, 70), images=(4, 1),
        animated=(0, 0), bg=0.98, brand_share=0.10, hero=False, adjacent=True,
        img_type="photo", formality=4, layout="long_form", people=True,
        accents=["text", "icons"], levers=["liking", "authority"],
        second_person=0.43, urgency=(1, 1), text_img_ratio=(3.1, 0.4), archetype_note="text-led",
    ),
    "belfius": dict(
        category="traditional", brand="#c8102e", words=(720, 80), images=(5, 2),
        animated=(0, 0), bg=0.97, brand_share=0.16, hero=False, adjacent=True,
        img_type="photo", formality=4, layout="split_columns", people=True,
        accents=["text", "imagery"], levers=["authority"],
        second_person=0.42, urgency=(1, 1), text_img_ratio=(3.6, 0.4), archetype_note="verbose, red in text and pictures",
    ),
    "revolut": dict(
        category="challenger", brand="#0666eb", words=(140, 40), images=(11, 3),
        animated=(6, 2), bg=0.18, brand_share=0.31, hero=True, adjacent=False,
        img_type="render_3d", formality=2, layout="card_grid", people=False,
        accents=["imagery", "background", "buttons"], levers=["social_proof", "scarcity", "liking"],
        second_person=0.71, urgency=(3, 1), text_img_ratio=(0.7, 0.2), archetype_note="dark, 3D, minimal copy",
    ),
    "n26": dict(
        category="challenger", brand="#36a18b", words=(210, 40), images=(9, 2),
        animated=(3, 1), bg=0.95, brand_share=0.22, hero=True, adjacent=False,
        img_type="render_3d", formality=2, layout="card_grid", people=False,
        accents=["imagery", "buttons"], levers=["social_proof", "liking"],
        second_person=0.68, urgency=(2, 1), text_img_ratio=(1.0, 0.2), archetype_note="product renders, light ground",
    ),
    "bunq": dict(
        category="challenger", brand="#3394ff", words=(190, 40), images=(10, 3),
        animated=(4, 2), bg=0.22, brand_share=0.27, hero=True, adjacent=False,
        img_type="illustration", formality=2, layout="card_grid", people=False,
        accents=["imagery", "background", "buttons"], levers=["liking", "social_proof"],
        second_person=0.74, urgency=(2, 1), text_img_ratio=(0.8, 0.2), archetype_note="dark, illustrated",
    ),
}

# sieg 14/09: was hardcoded to "flesch_douma_nl" regardless of the `language`
# argument below, so a fixture built with language="fr" or "en" silently
# claimed Dutch-formula scoring. Table added so build_fixture() can look up
# the right formula per language instead.
_READABILITY_FORMULA = {
    "nl": "flesch_douma_nl",
    "fr": "kandel_moles_fr",
    "en": "flesch_reading_ease_en",
}
# sieg 17/09, audit finding (LOW): this was a THIRD independent copy of the
# same readability threshold edges (collection/scraper.py and derive.py had
# their own too) - all three now call bands.readability_band().


def build_fixture(
    fd: FeatureDictionary | None = None,
    *,
    banks: list[str] | None = None,
    pages_per_bank: int = 2,
    language: str = "nl",
    product_family: str = "term_account",
    seed: int = 20260914,
) -> pd.DataFrame:
    """Generate a synthetic dataset shaped like the real one."""
    fd = fd or load_dictionary()
    rng = np.random.default_rng(seed)
    banks = banks or list(ARCHETYPES)
    captured = datetime(2026, 9, 15, 9, 0, tzinfo=timezone.utc)

    rows: list[dict] = []
    for bank in banks:
        a = ARCHETYPES[bank]
        for i in range(pages_per_bank):
            words = max(60, int(rng.normal(*a["words"])))
            sentences = max(4, int(words / rng.normal(14, 2)))
            images = max(1, int(rng.normal(*a["images"])))
            animated = max(0, int(rng.normal(*a["animated"])))
            readability = float(np.clip(rng.normal(78 - a["formality"] * 7, 6), 5, 98))
            aida = {
                "aida_attention": True,
                "aida_interest": True,
                "aida_desire": bool(rng.random() > (0.15 if a["category"] == "challenger" else 0.35)),
                "aida_action": bool(rng.random() > 0.1),
            }
            levers = a["levers"]
            # sieg 14/09: pulled out of the dict literal below so each value is
            # drawn exactly once and reused for both the raw field and its
            # _band equivalent - inlining the same rng.normal(...) call twice
            # would draw two different numbers and make the band disagree
            # with the raw value it's supposed to describe.
            second_person_ratio_value = round(float(np.clip(rng.normal(a["second_person"], 0.05), 0, 1)), 3)
            first_person_plural_value = int(max(0, rng.normal(6, 3)))
            disclaimer_word_share_value = round(float(np.clip(rng.normal(0.18 if a["category"] == "traditional" else 0.07, 0.04), 0, 1)), 3)
            # steph 15/09, FIXED: this was drawn independently from an archetype,
            # so the fixture's text_to_image_ratio disagreed with its OWN
            # word_count and image_count by ~40x (ING: stored 1.18, implied
            # 77.33). collection/scraper.py defines the feature as
            # word_count / image_count, and a fixture that does not obey the
            # extractor's own definition silently invalidates anything tuned on
            # it - which is exactly what happened to the bands.py thresholds.
            # The archetype's intent (text-led vs image-led) is already carried
            # by word_count and image_count, so it is not lost here.
            text_to_image_ratio_value = round(words / max(images, 1), 2)
            rows.append(
                {
                    "page_id": f"{bank}_{product_family}_{language}_{i + 1:02d}",
                    "bank": bank,
                    "bank_category": a["category"],
                    "product_family": product_family,
                    "page_role": "campaign_landing" if i == 0 else "product_detail",
                    "url": f"https://www.example-{bank.replace('_', '-')}.invalid/{language}/{product_family}/{i + 1}",
                    "language": language,
                    "captured_at": captured.isoformat(),
                    "collection_method": "headless_render",
                    "robots_allowed": True,
                    "snapshot_html_path": f"data/raw/{bank}/{product_family}_{i + 1}.html",
                    "screenshot_path": f"data/raw/{bank}/{product_family}_{i + 1}.png",
                    "data_source": "synthetic_fixture",
                    # tone
                    "word_count": words,
                    "word_count_band": bands.word_count_band(words),  # sieg 14/09
                    "sentence_count": sentences,
                    "sentence_count_band": bands.sentence_count_band(sentences),  # sieg 14/09
                    "avg_sentence_length": round(words / sentences, 2),
                    "avg_sentence_length_band": bands.avg_sentence_length_band(words / sentences),  # sieg 14/09
                    "readability_score": round(readability, 1),
                    "readability_formula": _READABILITY_FORMULA[language],  # sieg 14/09: was hardcoded to nl
                    "readability_band": bands.readability_band(readability),
                    "second_person_ratio": second_person_ratio_value,
                    "second_person_ratio_band": bands.second_person_ratio_band(second_person_ratio_value),  # sieg 14/09
                    "first_person_plural_count": first_person_plural_value,
                    "first_person_plural_band": bands.first_person_plural_band(first_person_plural_value),  # sieg 14/09
                    "question_count": int(max(0, rng.normal(2, 1.5))),
                    "urgency_marker_count": max(0, int(rng.normal(*a["urgency"]))),
                    "numeric_claim_count": int(max(0, rng.normal(9 if a["category"] == "traditional" else 4, 2))),
                    "formality_score": int(np.clip(rng.normal(a["formality"], 0.5), 1, 5)),
                    "clarity_score": int(np.clip(rng.normal(4 if a["category"] == "challenger" else 3, 0.6), 1, 5)),
                    # topics
                    "primary_product": "Termijnrekening" if a["category"] == "traditional" else "Savings vault",
                    "rate_shown": True,
                    "rate_value_pct": round(float(rng.normal(2.6, 0.4)), 2),
                    "rate_prominence": "hero" if a["category"] == "traditional" else "above_fold",
                    "benefit_framing": "rational" if a["category"] == "traditional" else "emotional",
                    "fab_level": "feature" if a["category"] == "traditional" else "benefit",
                    "value_prop_clarity": int(np.clip(rng.normal(3.5, 0.7), 1, 5)),
                    "disclaimer_present": True,
                    "disclaimer_word_share": disclaimer_word_share_value,
                    "disclaimer_word_share_band": bands.disclaimer_word_share_band(disclaimer_word_share_value),  # sieg 14/09
                    # visuals
                    "image_count": images,
                    "hero_image_present": a["hero"],
                    "hero_image_area_ratio": round(float(np.clip(rng.normal(0.55 if a["hero"] else 0.15, 0.08), 0, 1)), 3),
                    "total_image_area_ratio": round(float(np.clip(rng.normal(0.28 if a["category"] == "traditional" else 0.55, 0.06), 0, 1)), 3),
                    "animated_asset_count": animated,
                    "has_animation": animated > 0,
                    "dominant_image_type": a["img_type"],
                    "people_present": a["people"],
                    "imagery_register": "lifestyle" if a["people"] else "product",
                    # colours
                    "dominant_colour_hex": a["brand"],
                    "palette_hex": format_list([a["brand"], "#ffffff", "#111111", "#f4f4f4", "#888888"]),
                    "brand_colour_share": round(float(np.clip(rng.normal(a["brand_share"], 0.02), 0, 1)), 3),
                    "accent_colour_count": int(np.clip(rng.normal(3 if a["category"] == "traditional" else 2, 1), 1, 8)),
                    "accent_locations": format_list(a["accents"]),
                    "background_luminance": round(float(np.clip(rng.normal(a["bg"], 0.02), 0, 1)), 3),
                    "cta_contrast_ratio": round(float(np.clip(rng.normal(5.2, 1.2), 1, 21)), 2),
                    # layout
                    "page_height_px": int(max(800, rng.normal(4200 if a["category"] == "traditional" else 5600, 500))),
                    "section_count": int(max(2, rng.normal(7, 2))),
                    "cta_count": int(max(1, rng.normal(4 if a["category"] == "traditional" else 7, 1.5))),
                    "cta_above_fold": bool(rng.random() > (0.4 if a["category"] == "traditional" else 0.05)),
                    # sieg 15/09: text_image_adjacent (boolean) -> text_image_layout
                    # (categorical) - "stacked" for ing specifically (the deck claim
                    # H4 is "no longer next to picture", not "overlaid" like the
                    # challengers below), "overlaid" for the other non-beside banks,
                    # matching the real N26/Revolut hero screenshots (full-bleed
                    # photo, headline written on top).
                    "text_image_layout": "beside" if a["adjacent"] else ("stacked" if bank == "ing" else "overlaid"),
                    "text_to_image_ratio": text_to_image_ratio_value,
                    "text_to_image_ratio_band": bands.text_to_image_ratio_band(text_to_image_ratio_value),  # sieg 14/09
                    "above_fold_element_count": int(max(1, rng.normal(6, 2))),
                    "has_comparison_table": bool(rng.random() > 0.5),
                    "layout_archetype": a["layout"],
                    # marketing principles
                    **aida,
                    "aida_coverage_score": sum(aida.values()),
                    "persuasion_levers": format_list(levers),
                    "persuasion_lever_count": len(levers),
                    # banking-domain (sieg 14/09) - grounded in the same discussion that
                    # produced these dimensions, not random: traditional = bancassurance
                    # bundle / branch network / base-rate framing / retention posture;
                    # challenger = self-service / capped-teaser rate / acquisition posture.
                    # belfius and ing get one deliberate, documented exception each below.
                    # SAME CAVEAT AS THE REST OF THIS FILE: this is fixture data, testing
                    # against it will always "confirm" the hypothesis it was built from.
                    "audience_segment": "retail",
                    "is_bundled_offer": a["category"] == "traditional",
                    # sieg 15/09: a challenger can be is_bundled_offer=False (no bundle
                    # PUSHED in this funnel) and still be partner_addon_digital here (it
                    # HAS a travel/purchase-protection add-on via a third party elsewhere
                    # in the app) - that gap between the two fields is deliberate, it is
                    # exactly the nuance the 15/09 discussion flagged: bancassurance
                    # (own product, dedicated advisor) vs a distributed digital add-on
                    # are not the same thing even when both count as "some cross-sell".
                    "cross_sell_delivery_model": "internal_advisor_led" if a["category"] == "traditional" else "partner_addon_digital",
                    "rate_framing": "base_rate" if a["category"] == "traditional" else "capped_tiered",
                    "primary_cta_type": "book_advisor_or_branch" if a["category"] == "traditional" else "self_service_online",
                    "switching_framing": "retention_reassurance" if a["category"] == "traditional" else "acquisition_encouragement",
                    "regulatory_disclosure_prominence": "prominent" if a["category"] == "traditional" else "present_not_prominent",
                    "hidden_conditions_behind_free_claim": a["category"] == "challenger",
                    "esg_claim_specificity": "backed_by_reference_or_figure" if bank == "ing" else ("vague_adjective_only" if a["category"] == "traditional" else "no_claim"),
                    "green_product_specific_benefit": bool(bank == "ing" and rng.random() > 0.5),
                    "mentions_loyalty_or_referral": a["category"] == "challenger",
                    "images_have_alt_text": bool(rng.random() > 0.3),
                    "meta_title": f"{bank.replace('_', ' ').title()} - {product_family.replace('_', ' ')} - {language.upper()}",
                    # institutional_trust_signal_present: belfius is 100% Belgian-State-owned,
                    # a safety argument no other bank in scope can make the same way.
                    "institutional_trust_signal_present": bank == "belfius",
                    "youth_student_targeting": bool(rng.random() > (0.6 if a["category"] == "challenger" else 0.8)),
                    "secondary_bank_positioning": a["category"] == "challenger",
                    # expat_cross_border_targeting: ING's historical reputation with expats/
                    # cross-border workers in Belgium.
                    "expat_cross_border_targeting": bank == "ing",
                    "branch_network_cited_as_benefit": a["category"] == "traditional",
                    # sieg 15/09: fast digital onboarding is a challenger-side claim in
                    # this archetype set - traditional banks route account opening
                    # through an advisor/branch step more often (see primary_cta_type above).
                    "fast_digital_onboarding_claim": a["category"] == "challenger",
                    # sieg 15/09: challengers lead with low/no-minimum, self-service
                    # investing (round-ups, robo style); traditional banks route a
                    # first-time investor to an advisor instead of a beginner page.
                    "first_time_investor_targeting": a["category"] == "challenger",
                    # sieg 15/09: pension/succession framing is a traditional-bank
                    # posture in this archetype set - challengers skew toward a
                    # younger customer base and don't lead with this angle.
                    "senior_preretirement_targeting": a["category"] == "traditional",
                    # sieg 15/09: mirrors the "dark, 3D/illustrated, card_grid" visual
                    # register already encoded per-archetype above (img_type/layout) -
                    # challengers use the same card-grid, tap-friendly register here.
                    "mobile_first_design_signal": a["layout"] == "card_grid",
                }
            )

    return pd.DataFrame(rows)
