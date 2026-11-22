"""Candidate brand terms (BNP Paribas Fortis, Argenta, Crelan, Revolut, N26,
bunq), consumed only by collectors/term_resolver.py.

This is deliberately kept separate from config.PRODUCTS: nothing here is
read by the collector, the analysis steps, the app or the exports.
term_resolver.py tests these candidates against live Google Trends data and
writes its findings to the term_validation table and to
data/term_validation_report.md; the winning terms are then copied into
config.PRODUCTS by hand after human review.
"""

# Section 3.3 - brand terms. "topic_required" means a bare string is only
# ever used as a last-resort fallback (flagged ambiguous_string); a valid
# Knowledge Graph topic must be tried first.
BRAND_CANDIDATES = {
    "BNPPF": {
        "suggestion_keywords": ["BNP Paribas Fortis"],
        "string_candidates": ["BNP Paribas Fortis", "BNP", "Fortis"],
        "topic_required": True,
    },
    "ARGENTA": {
        "suggestion_keywords": ["Argenta", "Argenta bank"],
        "string_candidates": ["Argenta"],
        "topic_required": True,
    },
    "N26": {
        "suggestion_keywords": ["N26", "N26 bank"],
        "string_candidates": ["N26"],
        "topic_required": True,
    },
    "CRELAN": {
        "suggestion_keywords": ["Crelan"],
        "string_candidates": ["Crelan"],
        "topic_required": False,
    },
    "REVOLUT": {
        "suggestion_keywords": ["Revolut"],
        "string_candidates": ["Revolut"],
        "topic_required": False,
    },
    "BUNQ": {
        "suggestion_keywords": ["bunq"],
        "string_candidates": ["bunq"],
        "topic_required": False,
    },
}

# Informational-only control (section 3.3, last bullet): compares the
# existing bare ING/KBC strings against their own Knowledge Graph topics.
# Purely a report entry - never changes config.PRODUCTS.
CONTROL_BRANDS = {
    "ING": {"suggestion_keywords": ["ING"], "string_candidates": ["ING"]},
    "KBC": {"suggestion_keywords": ["KBC"], "string_candidates": ["KBC"]},
}

TOPIC_TYPE_KEYWORDS = [
    "bank", "banque", "financial", "financier", "financière",
    "company", "compagnie", "entreprise", "bedrijf", "neobank", "néobanque",
]

# Section 1.3 - brand fiches. ing_kbc_anchor terms are copied verbatim from
# the existing marque_generique sheet (config.PRODUCTS), never altered.
ING_KBC_ANCHOR_TERMS = [
    {"term": "ING", "bank": "ING", "language": "en"},
    {"term": "KBC", "bank": "KBC", "language": "en"},
]

BRAND_FICHES = [
    {
        "product_id": "marque_generique_traditionnelles",
        "product_label": "Marques — banques traditionnelles",
        "brand_banks": ["BNPPF", "ARGENTA", "CRELAN"],
    },
    {
        "product_id": "marque_generique_neobanques",
        "product_label": "Marques — néobanques",
        "brand_banks": ["REVOLUT", "N26", "BUNQ"],
    },
]

# Section 1.3 - context fiches. The predecessor-brand terms carry the
# absorbing bank's `bank` value, per the brief.
CONTEXT_FICHES = [
    {
        "product_id": "contexte_integration_bnppf_bpost",
        "product_label": "Contexte — intégration de bpost banque dans BNP Paribas Fortis (janvier 2024)",
        "brand_bank": "BNPPF",
        "extra_terms": [
            {"term": "bpost bank", "bank": "BNPPF", "language": "en"},
            {"term": "bpost banque", "bank": "BNPPF", "language": "fr"},
        ],
    },
    {
        "product_id": "contexte_fusion_crelan_axa",
        "product_label": "Contexte — fusion d'AXA Bank Belgium dans Crelan (juin 2024)",
        "brand_bank": "CRELAN",
        "extra_terms": [
            {"term": "AXA Bank", "bank": "CRELAN", "language": "en"},
            {"term": "AXA Banque", "bank": "CRELAN", "language": "fr"},
        ],
    },
]
