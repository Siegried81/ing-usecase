"""Candidate term data for the six-bank extension (BNP Paribas Fortis,
Argenta, Crelan, Revolut, N26, bunq), consumed only by
collectors/term_resolver.py.

This is deliberately kept separate from config.PRODUCTS: nothing here is
read by the collector, the anomaly detection step, the app or the exports.
term_resolver.py tests these candidates against live Google Trends data and
writes its findings to the term_validation table and to
data/term_validation_report.md; the winning terms are then copied into
config.PRODUCTS by hand after human review.

Candidate list of each slot is ordered by trial priority (rank 1 first).
"""

BASE_PRODUCT_ORDER = [
    "compte_professionnel",
    "compte_a_vue",
    "compte_epargne",
    "investissement_courtage",
    "app_mobile",
    "carte_credit",
    "epargne_pension",
    "assurance_habitation",
    "pret_hypothecaire",
]

TRADITIONAL_BANKS = ["BNPPF", "ARGENTA", "CRELAN"]
NEOBANKS = ["REVOLUT", "N26", "BUNQ"]

BANK_SUFFIX = {
    "BNPPF": "_bnppf",
    "ARGENTA": "_argenta",
    "CRELAN": "_crelan",
    "REVOLUT": "_revolut",
    "N26": "_n26",
    "BUNQ": "_bunq",
}

# Brand token used to build product-level search terms (section 1.1).
# Distinct from the brand term resolved in phase 1A, which is only used by
# the brand and context sheets.
BRAND_TOKEN = {
    "BNPPF": "BNP",
    "ARGENTA": "Argenta",
    "CRELAN": "Crelan",
    "REVOLUT": "Revolut",
    "N26": "N26",
    "BUNQ": "bunq",
}

CARD_NETWORK = {"BNPPF": "visa", "ARGENTA": "mastercard", "CRELAN": "visa"}

# Base products available per bank, in BASE_PRODUCT_ORDER (section 1.2).
BANK_PRODUCT_AVAILABILITY = {
    "BNPPF": list(BASE_PRODUCT_ORDER),
    "ARGENTA": list(BASE_PRODUCT_ORDER),
    "CRELAN": list(BASE_PRODUCT_ORDER),
    "REVOLUT": ["compte_professionnel", "compte_a_vue", "compte_epargne", "investissement_courtage", "app_mobile"],
    "N26": ["compte_professionnel", "compte_a_vue", "compte_epargne", "investissement_courtage", "app_mobile"],
    "BUNQ": ["compte_professionnel", "compte_a_vue", "compte_epargne", "investissement_courtage", "app_mobile", "carte_credit"],
}

PRODUCT_LABEL_BASE = {
    "compte_professionnel": "Compte professionnel / indépendant",
    "compte_a_vue": "Compte à vue particulier",
    "compte_epargne": "Compte épargne particulier",
    "investissement_courtage": "Investissement / courtage en ligne",
    "app_mobile": "Application mobile bancaire",
    "carte_credit": "Carte de crédit",
    "epargne_pension": "Épargne-pension",
    "assurance_habitation": "Assurance habitation",
    "pret_hypothecaire": "Prêt hypothécaire",
}

# Notes to carry into the exports (section 8 of the extension brief).
PRODUCT_NOTES = {
    ("ARGENTA", "investissement_courtage"): (
        "L'offre d'investissement d'Argenta repose sur des fonds et des plans "
        "d'investissement avec conseil, pas sur une plateforme de courtage "
        "d'actions comparable a Bolero."
    ),
    ("CRELAN", "investissement_courtage"): (
        "L'offre d'investissement de Crelan repose sur des fonds et des plans "
        "d'investissement avec conseil, pas sur une plateforme de courtage "
        "d'actions comparable a Bolero."
    ),
}

# A candidate is either the [ING->B] substitution (see term_resolver.py:
# resolve_ing_replace) or a literal template with {b} standing in for
# BRAND_TOKEN[bank] and {reseau} for CARD_NETWORK[bank]. "broad" marks a
# candidate as a broad-match fallback (section 2.5); if selected it carries
# the broad_fallback flag.
ING_REPLACE = "__ing_replace__"


def lit(template, broad=False):
    return {"kind": "literal", "template": template, "broad": broad}


ING_R = {"kind": "ing_replace", "broad": False}

# Section 3.1 - traditional banks (BNPPF, ARGENTA, CRELAN), slots fr/nl.
TRADITIONAL_PRODUCT_CANDIDATES = {
    "compte_professionnel": {
        "fr": [ING_R, lit("compte pro {b}"), lit("{b} indépendant")],
        "nl": [ING_R, lit("{b} zakelijk"), lit("{b} zelfstandige")],
    },
    "compte_a_vue": {
        "fr": [ING_R, lit("compte courant {b}"), lit("compte {b}", broad=True)],
        "nl": [ING_R, lit("{b} zichtrekening"), lit("{b} rekening", broad=True)],
    },
    "compte_epargne": {
        "fr": [ING_R, lit("compte épargne {b}"), lit("épargne {b}")],
        "nl": [ING_R, lit("{b} spaarrekening"), lit("{b} sparen")],
    },
    "investissement_courtage": {
        "fr": [ING_R, lit("investir {b}")],
        "nl": [ING_R, lit("{b} beleggen")],
    },
    "carte_credit": {
        "fr": [ING_R, lit("carte de crédit {b}"), lit("{b} {reseau}", broad=True)],
        "nl": [ING_R, lit("{b} kredietkaart"), lit("{b} {reseau}", broad=True)],
    },
    "epargne_pension": {
        "fr": [ING_R, lit("épargne pension {b}"), lit("{b} pension", broad=True)],
        "nl": [ING_R, lit("{b} pensioensparen"), lit("{b} pensioen", broad=True)],
    },
    "assurance_habitation": {
        "fr": [ING_R, lit("assurance habitation {b}"), lit("assurance incendie {b}")],
        "nl": [ING_R, lit("{b} woningverzekering"), lit("{b} brandverzekering")],
    },
    "pret_hypothecaire": {
        "fr": [ING_R, lit("prêt hypothécaire {b}"), lit("crédit hypothécaire {b}")],
        "nl": [ING_R, lit("{b} woonkrediet"), lit("{b} hypotheek")],
    },
}

# Section 3.1 - app_mobile: single neutral slot, literal candidates per bank
# (app names are bank-specific, never built from BRAND_TOKEN + template).
TRADITIONAL_APP_MOBILE_CANDIDATES = {
    "BNPPF": [lit("easy banking app"), lit("easy banking", broad=True), lit("BNP app")],
    "ARGENTA": [lit("Argenta app"), lit("Argenta banking")],
    "CRELAN": [lit("Crelan Mobile"), lit("Crelan app")],
}

# Section 3.2 - neobanks (REVOLUT, N26, BUNQ), slots fr/nl/en.
NEOBANK_PRODUCT_CANDIDATES = {
    "compte_professionnel": {
        "fr": [ING_R, lit("compte pro {b}")],
        "nl": [ING_R, lit("{b} zakelijk")],
        "en": [lit("{b} Business")],
    },
    "compte_a_vue": {
        "fr": [ING_R, lit("compte {b}", broad=True)],
        "nl": [ING_R, lit("{b} rekening", broad=True)],
        "en": [lit("{b} account", broad=True)],
    },
    "compte_epargne": {
        "fr": [ING_R, lit("épargne {b}")],
        "nl": [ING_R, lit("{b} sparen")],
        "en": [lit("{b} savings")],
    },
    "investissement_courtage": {
        "fr": [ING_R, lit("investir {b}")],
        "nl": [ING_R, lit("{b} beleggen")],
        # "en" is bank-specific, see NEOBANK_INVEST_EN.
    },
    # carte_credit: BUNQ only (section 3.2).
    "carte_credit": {
        "fr": [ING_R, lit("carte de crédit bunq")],
        "nl": [ING_R, lit("bunq kredietkaart")],
        "en": [lit("bunq credit card")],
    },
}

NEOBANK_INVEST_EN = {
    "REVOLUT": [lit("Revolut stocks"), lit("Revolut trading", broad=True)],
    "N26": [lit("N26 invest"), lit("N26 stocks")],
    "BUNQ": [lit("bunq stocks")],
}

# Section 3.2 - app_mobile: single neutral slot, "{b} app".
NEOBANK_APP_MOBILE_CANDIDATES = {
    "REVOLUT": [lit("Revolut app")],
    "N26": [lit("N26 app")],
    "BUNQ": [lit("bunq app")],
}

# Section 2.2 - slot removal order when a neobank fiche (ING refs + fr/nl/en
# slots) exceeds 5 terms: slots are dropped starting from the end of the
# priority list in the brief, i.e. this is the literal drop order.
SLOT_DROP_ORDER = {
    "compte_professionnel": ["nl", "fr", "en"],
    "__default__": ["en", "nl", "fr"],
}

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
