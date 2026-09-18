"""Shared configuration for the KBC vs ING Google Trends benchmark."""

import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "benchmark.db")
CSV_DIR = os.path.join(BASE_DIR, "data", "csv")
SCHEMA_PATH = os.path.join(BASE_DIR, "db", "schema.sql")

GEO = "BE"
TIMEFRAME = "today 5-y"

# Human-readable label for terms that are Knowledge Graph topic mids rather
# than plain search strings. A bare "CBC" string is heavily polluted on
# Google Trends (basal cell carcinoma, CBC News/Radio-Canada, blood count
# tests), even with geo=BE, so the CBC brand-level term below queries the
# disambiguated topic instead - confirmed via pytrends.suggestions() and an
# interest_over_time() coverage check (mean 54.2, 262/262 non-zero points,
# vs. a polluted mean of 71.6 for the bare string or near-zero for
# "CBC Banque et Assurance", which is too specific to have real volume).
TERM_DISPLAY_LABELS = {
    "/g/1z3t2x3c8": "CBC Banque & Assurance",
    # Brand topics resolved by collectors/term_resolver.py (phase 1A of the
    # six-bank extension). A bare string was kept wherever it was already
    # unambiguous on geo=BE, so only these three banks use a topic mid.
    "/m/07sc3dj": "BNP Paribas Fortis",
    "/m/03lmky": "Argenta",
    "/g/11c1p5t9vb": "N26",
}

# Bank codes used in the `bank` column of trends_data / anomalies. Stored as
# free text in SQLite (no CHECK constraint), so this dict is the reference
# list for the whole pipeline.
BANK_DISPLAY_LABELS = {
    "ING": "ING",
    "KBC": "KBC",
    "CBC": "CBC",
    "BNPPF": "BNP Paribas Fortis",
    "ARGENTA": "Argenta",
    "CRELAN": "Crelan",
    "REVOLUT": "Revolut",
    "N26": "N26",
    "BUNQ": "bunq",
}

BANK_SEGMENTS = {
    "ING": "traditionnelle",
    "KBC": "traditionnelle",
    "CBC": "traditionnelle",
    "BNPPF": "traditionnelle",
    "ARGENTA": "traditionnelle",
    "CRELAN": "traditionnelle",
    "REVOLUT": "néobanque",
    "N26": "néobanque",
    "BUNQ": "néobanque",
}

# Product sheets: source of truth for terms, banks and languages.
# Order here defines display order across the pipeline and the Streamlit app.
# Each sheet has at most 5 terms (pytrends hard limit per request).
PRODUCTS = [
    {
        "product_id": "compte_professionnel",
        "product_label": "Compte professionnel / indépendant",
        "terms": [
            {"term": "KBC zakelijke rekening", "bank": "KBC", "language": "nl"},
            {"term": "compte professionnel ING", "bank": "ING", "language": "fr"},
            {"term": "ING zakelijke rekening", "bank": "ING", "language": "nl"},
            {"term": "Business'Bank ING", "bank": "ING", "language": "en"},
            {"term": "KBC Business Pro", "bank": "KBC", "language": "en"},
        ],
    },
    {
        "product_id": "compte_a_vue",
        "product_label": "Compte à vue particulier",
        "terms": [
            {"term": "KBC zichtrekening", "bank": "KBC", "language": "nl"},
            {"term": "compte à vue ING", "bank": "ING", "language": "fr"},
            {"term": "ING zichtrekening", "bank": "ING", "language": "nl"},
            {"term": "ING Do Basic", "bank": "ING", "language": "en"},
            {"term": "Compte Plus KBC", "bank": "KBC", "language": "fr"},
        ],
    },
    {
        "product_id": "compte_epargne",
        "product_label": "Compte épargne particulier",
        "terms": [
            {"term": "KBC spaarrekening", "bank": "KBC", "language": "nl"},
            {"term": "compte épargne ING", "bank": "ING", "language": "fr"},
            {"term": "ING spaarrekening", "bank": "ING", "language": "nl"},
            {"term": "ING Orange Savings", "bank": "ING", "language": "en"},
            {"term": "KBC Start2Save", "bank": "KBC", "language": "en"},
        ],
    },
    {
        "product_id": "investissement_courtage",
        "product_label": "Investissement / courtage en ligne",
        "terms": [
            {"term": "Bolero", "bank": "KBC", "language": "en"},
            {"term": "ING Self Invest", "bank": "ING", "language": "en"},
        ],
    },
    {
        "product_id": "app_mobile",
        "product_label": "Application mobile bancaire",
        "terms": [
            {"term": "KBC Mobile", "bank": "KBC", "language": "en"},
            {"term": "ING Banking", "bank": "ING", "language": "en"},
            {"term": "ING Smart Banking", "bank": "ING", "language": "en"},
            {"term": "KBC Touch", "bank": "KBC", "language": "en"},
        ],
    },
    {
        "product_id": "carte_credit",
        "product_label": "Carte de crédit",
        "terms": [
            {"term": "KBC kredietkaart", "bank": "KBC", "language": "nl"},
            {"term": "carte de crédit ING", "bank": "ING", "language": "fr"},
            {"term": "ING kredietkaart", "bank": "ING", "language": "nl"},
            {"term": "ING Card", "bank": "ING", "language": "en"},
            {"term": "KBC Flex Budget", "bank": "KBC", "language": "en"},
        ],
    },
    {
        "product_id": "epargne_pension",
        "product_label": "Épargne-pension",
        "terms": [
            {"term": "KBC pensioensparen", "bank": "KBC", "language": "nl"},
            {"term": "épargne pension ING", "bank": "ING", "language": "fr"},
            {"term": "ING pensioensparen", "bank": "ING", "language": "nl"},
            {"term": "ING Star Fund", "bank": "ING", "language": "en"},
            {"term": "KBC Pension Savings Fund", "bank": "KBC", "language": "en"},
        ],
    },
    {
        "product_id": "assurance_habitation",
        "product_label": "Assurance habitation",
        "terms": [
            {"term": "KBC brandverzekering", "bank": "KBC", "language": "nl"},
            {"term": "assurance habitation ING", "bank": "ING", "language": "fr"},
            {"term": "ING Home Insurance", "bank": "ING", "language": "en"},
        ],
    },
    {
        "product_id": "pret_hypothecaire",
        "product_label": "Prêt hypothécaire",
        "terms": [
            {"term": "KBC hypothecair krediet", "bank": "KBC", "language": "nl"},
            {"term": "prêt hypothécaire ING", "bank": "ING", "language": "fr"},
            {"term": "ING hypothecair krediet", "bank": "ING", "language": "nl"},
        ],
    },
    # CBC is KBC Group's own commercial brand for Wallonia and French-speaking
    # Brussels - a distinct brand with its own search demand, not a separate
    # legal entity. Mirrors the 9 KBC-vs-ING sheets above, one per product,
    # querying CBC vs the same ING terms in a fresh request (Trends values are
    # only comparable within one request, so ING has to be re-queried here
    # rather than reusing the KBC-vs-ING data). No CBC-specific term exists
    # for investissement_courtage (Bolero is a shared KBC Group brokerage
    # platform, not region-branded), so that sheet has no CBC counterpart.
    {
        "product_id": "compte_professionnel_cbc",
        "product_label": "Compte professionnel / indépendant (CBC vs ING)",
        "terms": [
            {"term": "compte professionnel CBC", "bank": "CBC", "language": "fr"},
            {"term": "KBC Business Pro", "bank": "CBC", "language": "en"},
            {"term": "compte professionnel ING", "bank": "ING", "language": "fr"},
            {"term": "ING zakelijke rekening", "bank": "ING", "language": "nl"},
            {"term": "Business'Bank ING", "bank": "ING", "language": "en"},
        ],
    },
    {
        "product_id": "compte_a_vue_cbc",
        "product_label": "Compte à vue particulier (CBC vs ING)",
        "terms": [
            {"term": "compte à vue CBC", "bank": "CBC", "language": "fr"},
            {"term": "compte à vue ING", "bank": "ING", "language": "fr"},
            {"term": "ING zichtrekening", "bank": "ING", "language": "nl"},
            {"term": "ING Do Basic", "bank": "ING", "language": "en"},
        ],
    },
    {
        "product_id": "compte_epargne_cbc",
        "product_label": "Compte épargne particulier (CBC vs ING)",
        "terms": [
            {"term": "compte épargne CBC", "bank": "CBC", "language": "fr"},
            {"term": "compte épargne ING", "bank": "ING", "language": "fr"},
            {"term": "ING spaarrekening", "bank": "ING", "language": "nl"},
            {"term": "ING Orange Savings", "bank": "ING", "language": "en"},
        ],
    },
    {
        "product_id": "app_mobile_cbc",
        "product_label": "Application mobile bancaire (CBC vs ING)",
        "terms": [
            {"term": "CBC Mobile", "bank": "CBC", "language": "en"},
            {"term": "CBC Touch", "bank": "CBC", "language": "en"},
            {"term": "ING Banking", "bank": "ING", "language": "en"},
            {"term": "ING Smart Banking", "bank": "ING", "language": "en"},
        ],
    },
    {
        "product_id": "carte_credit_cbc",
        "product_label": "Carte de crédit (CBC vs ING)",
        "terms": [
            {"term": "carte de crédit CBC", "bank": "CBC", "language": "fr"},
            {"term": "carte de crédit ING", "bank": "ING", "language": "fr"},
            {"term": "ING kredietkaart", "bank": "ING", "language": "nl"},
            {"term": "ING Card", "bank": "ING", "language": "en"},
        ],
    },
    {
        "product_id": "epargne_pension_cbc",
        "product_label": "Épargne-pension (CBC vs ING)",
        "terms": [
            {"term": "épargne pension CBC", "bank": "CBC", "language": "fr"},
            {"term": "épargne pension ING", "bank": "ING", "language": "fr"},
            {"term": "ING pensioensparen", "bank": "ING", "language": "nl"},
            {"term": "ING Star Fund", "bank": "ING", "language": "en"},
        ],
    },
    {
        # CBC term is a generic "assurance" query (as given), not
        # home-insurance-specific like the KBC/ING terms elsewhere - the CBC
        # series here measures general insurance interest, not a like-for-like
        # home insurance comparison. Flagged as a known scope difference.
        "product_id": "assurance_habitation_cbc",
        "product_label": "Assurance habitation (CBC vs ING)",
        "terms": [
            {"term": "assurance CBC", "bank": "CBC", "language": "fr"},
            {"term": "assurance habitation ING", "bank": "ING", "language": "fr"},
            {"term": "ING Home Insurance", "bank": "ING", "language": "en"},
        ],
    },
    {
        "product_id": "pret_hypothecaire_cbc",
        "product_label": "Prêt hypothécaire (CBC vs ING)",
        "terms": [
            {"term": "prêt hypothécaire CBC", "bank": "CBC", "language": "fr"},
            {"term": "prêt hypothécaire ING", "bank": "ING", "language": "fr"},
            {"term": "ING hypothecair krediet", "bank": "ING", "language": "nl"},
        ],
    },
    {
        "product_id": "marque_generique",
        "product_label": "Marque (recherche générique)",
        "terms": [
            {"term": "KBC", "bank": "KBC", "language": "en"},
            {"term": "ING", "bank": "ING", "language": "en"},
            {"term": "/g/1z3t2x3c8", "bank": "CBC", "language": "en"},
        ],
    },
    # Six-bank extension (BNPPF, Argenta, Crelan, Revolut, N26, bunq). Terms
    # below are exactly the winners recorded in term_validation by
    # collectors/term_resolver.py - see data/term_validation_report.md for
    # every candidate tested and why the others were rejected or dropped.
    # Most of the 43 candidate product sheets were dropped entirely: once
    # normalized against ING's much larger search volume in the same
    # request, most of these banks' product-specific terms round to near
    # zero (the renormalization effect flagged in the brief's section 4.1).
    # Only 10 product sheets survived; Revolut keeps exactly one, N26 and
    # bunq keep none at product level (they still appear in the brand
    # sheets below).
    {
        "product_id": "compte_a_vue_bnppf",
        "product_label": "Compte à vue particulier (BNP Paribas Fortis vs ING)",
        "terms": [
            {"term": "compte à vue ING", "bank": "ING", "language": "fr"},
            {"term": "ING zichtrekening", "bank": "ING", "language": "nl"},
            {"term": "ING Do Basic", "bank": "ING", "language": "en"},
            {"term": "compte BNP", "bank": "BNPPF", "language": "fr"},
            {"term": "BNP rekening", "bank": "BNPPF", "language": "nl"},
        ],
    },
    {
        "product_id": "app_mobile_bnppf",
        "product_label": "Application mobile bancaire (BNP Paribas Fortis vs ING)",
        "terms": [
            {"term": "ING Banking", "bank": "ING", "language": "en"},
            {"term": "ING Smart Banking", "bank": "ING", "language": "en"},
            {"term": "easy banking app", "bank": "BNPPF", "language": "multi"},
        ],
    },
    {
        # nl slot ("BNP kredietkaart") was dropped - coverage 0.004, see report.
        "product_id": "carte_credit_bnppf",
        "product_label": "Carte de crédit (BNP Paribas Fortis vs ING)",
        "terms": [
            {"term": "carte de crédit ING", "bank": "ING", "language": "fr"},
            {"term": "ING kredietkaart", "bank": "ING", "language": "nl"},
            {"term": "ING Card", "bank": "ING", "language": "en"},
            {"term": "BNP visa", "bank": "BNPPF", "language": "fr"},
        ],
    },
    {
        # nl slot ("BNP pensioensparen") was dropped - coverage 0.019, see report.
        "product_id": "epargne_pension_bnppf",
        "product_label": "Épargne-pension (BNP Paribas Fortis vs ING)",
        "terms": [
            {"term": "épargne pension ING", "bank": "ING", "language": "fr"},
            {"term": "ING pensioensparen", "bank": "ING", "language": "nl"},
            {"term": "ING Star Fund", "bank": "ING", "language": "en"},
            {"term": "BNP pension", "bank": "BNPPF", "language": "fr"},
        ],
    },
    {
        "product_id": "compte_a_vue_argenta",
        "product_label": "Compte à vue particulier (Argenta vs ING)",
        "terms": [
            {"term": "compte à vue ING", "bank": "ING", "language": "fr"},
            {"term": "ING zichtrekening", "bank": "ING", "language": "nl"},
            {"term": "ING Do Basic", "bank": "ING", "language": "en"},
            {"term": "compte Argenta", "bank": "ARGENTA", "language": "fr"},
            {"term": "Argenta rekening", "bank": "ARGENTA", "language": "nl"},
        ],
    },
    {
        # fr slot ("compte épargne Argenta") was dropped - coverage 0.019, see report.
        "product_id": "compte_epargne_argenta",
        "product_label": "Compte épargne particulier (Argenta vs ING)",
        "terms": [
            {"term": "compte épargne ING", "bank": "ING", "language": "fr"},
            {"term": "ING spaarrekening", "bank": "ING", "language": "nl"},
            {"term": "ING Orange Savings", "bank": "ING", "language": "en"},
            {"term": "Argenta spaarrekening", "bank": "ARGENTA", "language": "nl"},
        ],
    },
    {
        "product_id": "app_mobile_argenta",
        "product_label": "Application mobile bancaire (Argenta vs ING)",
        "terms": [
            {"term": "ING Banking", "bank": "ING", "language": "en"},
            {"term": "ING Smart Banking", "bank": "ING", "language": "en"},
            {"term": "Argenta app", "bank": "ARGENTA", "language": "multi"},
        ],
    },
    {
        "product_id": "app_mobile_crelan",
        "product_label": "Application mobile bancaire (Crelan vs ING)",
        "terms": [
            {"term": "ING Banking", "bank": "ING", "language": "en"},
            {"term": "ING Smart Banking", "bank": "ING", "language": "en"},
            {"term": "Crelan app", "bank": "CRELAN", "language": "multi"},
        ],
    },
    {
        # nl slot ("Crelan kredietkaart") was dropped - coverage 0.008, see report.
        "product_id": "carte_credit_crelan",
        "product_label": "Carte de crédit (Crelan vs ING)",
        "terms": [
            {"term": "carte de crédit ING", "bank": "ING", "language": "fr"},
            {"term": "ING kredietkaart", "bank": "ING", "language": "nl"},
            {"term": "ING Card", "bank": "ING", "language": "en"},
            {"term": "Crelan visa", "bank": "CRELAN", "language": "fr"},
        ],
    },
    {
        # nl slot ("Revolut rekening") was dropped - coverage 0.057, see report.
        "product_id": "compte_a_vue_revolut",
        "product_label": "Compte à vue particulier (Revolut vs ING)",
        "terms": [
            {"term": "compte à vue ING", "bank": "ING", "language": "fr"},
            {"term": "ING zichtrekening", "bank": "ING", "language": "nl"},
            {"term": "ING Do Basic", "bank": "ING", "language": "en"},
            {"term": "compte Revolut", "bank": "REVOLUT", "language": "fr"},
        ],
    },
    {
        "product_id": "marque_generique_traditionnelles",
        "product_label": "Marques — banques traditionnelles",
        "terms": [
            {"term": "ING", "bank": "ING", "language": "en"},
            {"term": "KBC", "bank": "KBC", "language": "en"},
            {"term": "/m/07sc3dj", "bank": "BNPPF", "language": "multi"},
            {"term": "/m/03lmky", "bank": "ARGENTA", "language": "multi"},
            {"term": "Crelan", "bank": "CRELAN", "language": "multi"},
        ],
    },
    {
        "product_id": "marque_generique_neobanques",
        "product_label": "Marques — néobanques",
        "terms": [
            {"term": "ING", "bank": "ING", "language": "en"},
            {"term": "KBC", "bank": "KBC", "language": "en"},
            {"term": "Revolut", "bank": "REVOLUT", "language": "multi"},
            {"term": "/g/11c1p5t9vb", "bank": "N26", "language": "multi"},
            {"term": "bunq", "bank": "BUNQ", "language": "multi"},
        ],
    },
    {
        "product_id": "contexte_integration_bnppf_bpost",
        "product_label": "Contexte — intégration de bpost banque dans BNP Paribas Fortis (janvier 2024)",
        "terms": [
            {"term": "ING", "bank": "ING", "language": "en"},
            {"term": "/m/07sc3dj", "bank": "BNPPF", "language": "multi"},
            {"term": "bpost bank", "bank": "BNPPF", "language": "en"},
            {"term": "bpost banque", "bank": "BNPPF", "language": "fr"},
        ],
    },
    {
        "product_id": "contexte_fusion_crelan_axa",
        "product_label": "Contexte — fusion d'AXA Bank Belgium dans Crelan (juin 2024)",
        "terms": [
            {"term": "ING", "bank": "ING", "language": "en"},
            {"term": "Crelan", "bank": "CRELAN", "language": "multi"},
            {"term": "AXA Bank", "bank": "CRELAN", "language": "en"},
            {"term": "AXA Banque", "bank": "CRELAN", "language": "fr"},
        ],
    },
]

PRODUCT_BY_ID = {p["product_id"]: p for p in PRODUCTS}

# Anomaly detection: a point must clear both thresholds to be flagged.
Z_SCORE_THRESHOLD = 1.5
SEASONAL_RATIO_THRESHOLD = 1.3

ANOMALY_TYPE_LABELS = {
    "isolated_spike": "Pic isolé",
    "sustained_trend": "Tendance soutenue",
}

# Term resolution thresholds for the six-bank extension (BNPPF, Argenta,
# Crelan, Revolut, N26, bunq). Used by collectors/term_resolver.py only;
# config.PRODUCTS itself is edited by hand after the resulting report is
# reviewed, so these do not affect the existing 18 sheets.
BRAND_MIN_COVERAGE = 0.90
PRODUCT_SELECT_COVERAGE = 0.50
PRODUCT_FLOOR_COVERAGE = 0.25
MAX_CANDIDATE_CALLS_PER_FICHE = 3

# Structural market events. Display and exports only: anomaly detection never
# reads this list, so a break in a series is still detected on its own merits
# and only annotated here afterwards.
KNOWN_EVENTS = [
    {
        "bank": "BNPPF",
        "date": "2024-01-22",
        "label": "Intégration de bpost banque (environ 1 million de clients migrés)",
    },
    {
        "bank": "N26",
        "date": "2024-03-14",
        "label": "Lancement du compte épargne en Belgique",
    },
    {
        "bank": "CRELAN",
        "date": "2024-06-10",
        "label": (
            "Fusion avec AXA Bank Belgium, migration IT d'environ 840 000 clients "
            "(week-end des 8 et 9 juin)"
        ),
    },
    {
        "bank": "BUNQ",
        "date": "2024-12-17",
        "label": "bunq Stocks disponible en Belgique",
    },
    {
        "bank": "REVOLUT",
        "date": "2025-05-01",
        "label": (
            "Comptes belges (IBAN BE) pour les nouveaux clients, migration des "
            "clients existants au cours de 2025"
        ),
    },
    {
        "bank": "REVOLUT",
        "date": "2025-08-21",
        "label": (
            "Lancement du compte épargne à intérêts versés quotidiennement "
            "(date de couverture presse)"
        ),
    },
    {
        "bank": "BUNQ",
        "date": "2026-07-24",
        "label": (
            "Lancement des IBAN belges et de Wero en Belgique "
            "(date de couverture presse)"
        ),
    },
]

MAX_TERMS_PER_PRODUCT = 5


def _validate_products():
    """Fail fast on a malformed PRODUCTS entry rather than at collection time."""
    seen_ids = set()
    for product in PRODUCTS:
        pid = product["product_id"]
        if pid in seen_ids:
            raise ValueError(f"Duplicate product_id in PRODUCTS: {pid}")
        seen_ids.add(pid)

        terms = product["terms"]
        if len(terms) > MAX_TERMS_PER_PRODUCT:
            raise ValueError(
                f"Product sheet '{pid}' has {len(terms)} terms, "
                f"pytrends allows at most {MAX_TERMS_PER_PRODUCT}."
            )

        for term in terms:
            if term["bank"] not in BANK_DISPLAY_LABELS:
                raise ValueError(f"Unknown bank '{term['bank']}' in product sheet '{pid}'.")
            if term["term"].startswith(("/m/", "/g/")) and term["term"] not in TERM_DISPLAY_LABELS:
                raise ValueError(
                    f"Topic mid '{term['term']}' in product sheet '{pid}' has no "
                    "TERM_DISPLAY_LABELS entry."
                )


_validate_products()
