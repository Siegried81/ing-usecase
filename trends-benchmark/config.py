"""Shared configuration for the ING brand-notoriety benchmark."""

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
    # Brand topics resolved by collectors/term_resolver.py (six-bank
    # extension, phase 1A). A bare string was kept wherever it was already
    # unambiguous on geo=BE, so only these banks use a topic mid.
    "/m/07sc3dj": "BNP Paribas Fortis",
    "/m/03lmky": "Argenta",
    "/g/11c1p5t9vb": "N26",
    # Second wave (2026-09-21).
    "/g/121yyfq9": "VDK Bank",
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
    # Second wave (2026-09-21): matches the 14-bank scope of the wider ING
    # Banking Campaigns Comparator project (src/comparator/banks.py there).
    "BELFIUS": "Belfius",
    "BEOBANK": "Beobank",
    "VDK": "VDK Bank",
    "HELLOBANK": "Hello bank!",
    "KEYTRADE": "Keytrade Bank",
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
    "BELFIUS": "traditionnelle",
    "BEOBANK": "traditionnelle",
    "VDK": "traditionnelle",
    "HELLOBANK": "traditionnelle",
    # Branchless direct bank since 1998, not a fintech app like Revolut/N26/
    # bunq - but it sits with them on the incumbent-vs-challenger axis (same
    # classification as src/comparator/banks.py in the wider project).
    "KEYTRADE": "néobanque",
}

# Product sheets: source of truth for terms, banks and languages.
# Order here defines display order across the pipeline and the Streamlit app.
# Each sheet has at most 5 terms (pytrends hard limit per request).
#
# The project's scope was narrowed to brand notoriety only (share of
# search): the 29 product-comparison sheets and the 2 M&A context sheets
# from the six-bank extension were dropped. Only the 3 generic-brand sheets
# remain. ING and KBC appear, unchanged, in all three: that shared anchor is
# what lets analysis/share_of_search.py chain them into one 9-bank scale
# despite pytrends' 5-term-per-request limit (see docs section 7ter).
PRODUCTS = [
    {
        "product_id": "marque_generique",
        "product_label": "Marque (recherche générique)",
        "terms": [
            {"term": "KBC", "bank": "KBC", "language": "en"},
            {"term": "ING", "bank": "ING", "language": "en"},
            {"term": "/g/1z3t2x3c8", "bank": "CBC", "language": "en"},
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
    # Second wave (2026-09-21): matches the 14-bank scope of the wider ING
    # Banking Campaigns Comparator project (src/comparator/banks.py there).
    # Two more bridge fiches were needed since the two existing bridges
    # (traditionnelles, neobanques) were already full at 5 terms each.
    {
        "product_id": "marque_generique_traditionnelles_2",
        "product_label": "Marques — banques traditionnelles (2)",
        "terms": [
            {"term": "ING", "bank": "ING", "language": "en"},
            {"term": "KBC", "bank": "KBC", "language": "en"},
            {"term": "Belfius", "bank": "BELFIUS", "language": "multi"},
            {"term": "Beobank", "bank": "BEOBANK", "language": "multi"},
            {"term": "/g/121yyfq9", "bank": "VDK", "language": "multi"},
        ],
    },
    {
        # Hello bank! (BNP Paribas Fortis's digital-only brand) and Keytrade
        # Bank (a branchless direct bank since 1998) both sit on the
        # incumbent/challenger business-model axis, distinct from the
        # branch-network traditionnelles and from the Revolut/N26/bunq
        # fintech neobanques.
        "product_id": "marque_generique_digitales",
        "product_label": "Marques — banques digitales sans réseau d'agences",
        "terms": [
            {"term": "ING", "bank": "ING", "language": "en"},
            {"term": "KBC", "bank": "KBC", "language": "en"},
            # No Knowledge Graph topic passed validation for "Hello bank" in
            # geo=BE (a generic-sounding phrase and a multi-country BNP
            # Paribas brand) - kept as a flagged ambiguous_string, see
            # data/term_validation_report.md.
            {"term": "Hello bank!", "bank": "HELLOBANK", "language": "multi"},
            {"term": "Keytrade Bank", "bank": "KEYTRADE", "language": "multi"},
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
# Crelan, Revolut, N26, bunq). Used by collectors/term_resolver.py only,
# kept for when a brand term ever needs re-resolving.
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

# Reference sheet for the share-of-search chaining in
# analysis/share_of_search.py: its ING/KBC values define the common scale
# that the other brand sheets get rescaled onto.
SHARE_OF_SEARCH_REFERENCE_FICHE = "marque_generique"
SHARE_OF_SEARCH_ANCHOR_BANKS = ("ING", "KBC")

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
