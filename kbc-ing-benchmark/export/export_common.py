"""Shared logic for per-bank data exports (see export_kbc_data.py / export_ing_data.py).

Each export produces a Markdown document (methodology + product sheets +
anomalies) plus a CSV of the full raw Trends time series, which is too
large to inline readably. Meant as the data handoff for a downstream
pipeline that matches these anomalies against real ad/campaign activity.
"""

import csv
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (  # noqa: E402
    ANOMALY_TYPE_LABELS, BANK_DISPLAY_LABELS, BANK_SEGMENTS, DB_PATH, GEO,
    KNOWN_EVENTS, PRODUCT_FLOOR_COVERAGE, PRODUCT_SELECT_COVERAGE, PRODUCTS,
    SEASONAL_RATIO_THRESHOLD, TERM_DISPLAY_LABELS, TIMEFRAME, Z_SCORE_THRESHOLD,
)


def display_term(term):
    return TERM_DISPLAY_LABELS.get(term, term)


def display_bank(bank):
    return BANK_DISPLAY_LABELS.get(bank, bank)

EXPORT_DIR = os.path.dirname(os.path.abspath(__file__))

# Product-scope caveats carried into every export that contains the bank,
# so a downstream consumer never compares two sheets that do not measure
# comparable offers.
PRODUCT_NOTES = {
    "ARGENTA": [
        "`investissement_courtage` : l'offre d'investissement d'Argenta repose sur des "
        "fonds, des plans d'investissement et du conseil, pas sur une plateforme de "
        "courtage d'actions comparable à Bolero. Le `product_id` est conservé pour la "
        "symétrie inter-banques.",
    ],
    "CRELAN": [
        "`investissement_courtage` : l'offre d'investissement de Crelan repose sur des "
        "fonds, des plans d'investissement et du conseil, pas sur une plateforme de "
        "courtage d'actions comparable à Bolero. Le `product_id` est conservé pour la "
        "symétrie inter-banques.",
    ],
    "BNPPF": [
        "Les termes produit utilisent le jeton `BNP` : en broad match, `compte à vue BNP` "
        "inclut `compte à vue BNP Paribas Fortis`, qui est un sous-ensemble strict et "
        "donc toujours moins couvrant.",
        "Les recherches passant par les marques sœurs Hello bank! et Fintro ne sont pas "
        "captées par ces termes.",
    ],
    "REVOLUT": [
        "`app_mobile` mesure l'intérêt pour l'application, qui est le canal unique de "
        "cette banque : cette fiche n'est pas comparable à celle d'une banque à réseau "
        "d'agences.",
    ],
    "N26": [
        "`app_mobile` mesure l'intérêt pour l'application, qui est le canal unique de "
        "cette banque : cette fiche n'est pas comparable à celle d'une banque à réseau "
        "d'agences.",
    ],
    "BUNQ": [
        "`app_mobile` mesure l'intérêt pour l'application, qui est le canal unique de "
        "cette banque : cette fiche n'est pas comparable à celle d'une banque à réseau "
        "d'agences.",
    ],
}


def term_validation_lookup(conn):
    """(product_id, term) -> (coverage, flags) from the phase 1 resolution.

    Empty for the 18 historical sheets, which predate term_validation and
    were never put through the candidate selection protocol.
    """
    lookup = {}
    try:
        _, brand_rows = fetch_all(
            conn,
            "SELECT term, flags FROM term_validation "
            "WHERE scope = 'brand' AND call_index = 0 AND slot_language != '__done__'",
        )
        brand_flags = {r[0]: r[1] for r in brand_rows}

        _, product_rows = fetch_all(
            conn,
            "SELECT product_id, term, coverage, verdict, flags FROM term_validation "
            "WHERE scope = 'product' AND call_index = 0 AND slot_language != '__done__' "
            "AND verdict != 'dropped'",
        )
        for product_id, term, coverage, verdict, flags in product_rows:
            parts = [f for f in (flags or "").split(",") if f]
            if verdict == "selected_low_coverage":
                parts.insert(0, verdict)
            lookup[(product_id, term)] = (coverage, ",".join(parts))

        _, fiche_rows = fetch_all(
            conn,
            "SELECT product_id, term, coverage FROM term_validation "
            "WHERE scope IN ('brand_fiche', 'context_fiche') AND call_index = 1",
        )
        for product_id, term, coverage in fiche_rows:
            lookup[(product_id, term)] = (coverage, brand_flags.get(term) or "")
    except sqlite3.OperationalError:
        # term_validation has not been created yet (fresh database).
        return {}
    return lookup


def format_coverage(value):
    return "" if value is None else f"{value:.3f}"


def known_events_rows(bank=None):
    events = [e for e in KNOWN_EVENTS if bank is None or e["bank"] == bank]
    return [(e["date"], display_bank(e["bank"]), e["label"]) for e in sorted(events, key=lambda e: e["date"])]


def append_known_events_section(lines, bank=None):
    rows = known_events_rows(bank)
    lines.append("## Événements structurels connus")
    lines.append("")
    if not rows:
        lines.append(
            "Aucun événement structurel connu pour cette banque sur la période couverte."
        )
        lines.append("")
        return
    lines.append(
        "Ruptures de marché documentées, fournies pour interprétation : elles "
        "produisent des anomalies attendues qui ne sont pas des campagnes "
        "publicitaires. Cette liste n'intervient jamais dans la détection."
    )
    lines.append("")
    lines.append(md_table(["Date", "Banque", "Événement"], rows))
    lines.append("")


def append_term_selection_method(lines):
    lines.append(
        f"- **Sélection des termes (banques ajoutées en extension)** : pour chaque fiche, "
        f"les termes ING de référence sont repris à l'identique, puis un terme par langue "
        f"est choisi parmi une liste ordonnée de candidats testés en conditions réelles "
        f"(même géographie, même période, même composition de fiche). Un candidat est "
        f"retenu si sa couverture — points non nuls / points totaux — atteint "
        f"{PRODUCT_SELECT_COVERAGE:.2f} ; à défaut, le meilleur candidat observé est "
        f"conservé s'il atteint le plancher de {PRODUCT_FLOOR_COVERAGE:.2f} "
        f"(verdict `selected_low_coverage`), sinon le slot est supprimé."
    )
    lines.append(
        "- **Broad match** : un terme sans guillemets capte les recherches contenant tous "
        "ses mots, dans n'importe quel ordre ; ajouter un mot restreint le périmètre. Les "
        "candidats de repli sont donc volontairement de plus en plus larges, et un terme "
        "retenu à ce titre porte le flag `broad_fallback`."
    )
    lines.append(
        "- **Flags** : `selected_low_coverage` (série peu couverte, anomalies plus "
        "bruitées), `broad_fallback` (terme volontairement large), `asymmetric` (le terme "
        "retenu n'est pas la transposition exacte du terme ING, la comparaison n'est plus "
        "strictement symétrique), `ambiguous_string` (marque retenue sous forme de chaîne "
        "brute faute de topic Knowledge Graph valide)."
    )
    lines.append(
        "- **Détail complet de la sélection** : voir `data/term_validation_report.md` et la "
        "table `term_validation` de `benchmark.db` (un enregistrement par candidat testé)."
    )


def fetch_all(conn, query, params=()):
    cur = conn.execute(query, params)
    columns = [d[0] for d in cur.description]
    return columns, cur.fetchall()


def export_trends_csv(conn, bank, csv_path):
    columns, rows = fetch_all(
        conn,
        "SELECT product_id, product_label, term, bank, language, date, value "
        "FROM trends_data WHERE bank = ? ORDER BY product_id, term, date",
        (bank,),
    )
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def md_table(columns, rows):
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        cells = ["" if v is None else str(v).replace("|", "-").replace("\n", " ") for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_markdown(conn, bank, csv_filename, trends_row_count):
    bank_products = [p for p in PRODUCTS if any(t["bank"] == bank for t in p["terms"])]

    _, trends_range = fetch_all(
        conn,
        "SELECT MIN(date), MAX(date), COUNT(DISTINCT term) FROM trends_data WHERE bank = ?",
        (bank,),
    )
    min_date, max_date, term_count = trends_range[0]

    validation = term_validation_lookup(conn)

    anomaly_cols_fr = [
        "Fiche produit", "Terme", "Date", "Valeur", "Type d'anomalie",
        "Score de déviation", "Couverture du terme", "Flags du terme",
    ]
    _, anomaly_rows = fetch_all(
        conn,
        "SELECT product_id, term, date, value, anomaly_type, deviation_score "
        "FROM anomalies WHERE bank = ? ORDER BY date",
        (bank,),
    )
    anomaly_rows_fr = []
    for r in anomaly_rows:
        coverage, flags = validation.get((r[0], r[1]), (None, ""))
        anomaly_rows_fr.append((
            r[0], display_term(r[1]), r[2], r[3], ANOMALY_TYPE_LABELS.get(r[4], r[4]),
            round(r[5], 3), format_coverage(coverage), flags,
        ))

    bank_label = display_bank(bank)
    segment = BANK_SEGMENTS.get(bank, "")

    lines = []
    lines.append(f"# Export des données {bank_label} — Benchmark marketing ING vs concurrents")
    lines.append("")
    lines.append(
        f"Document généré automatiquement à partir de `benchmark.db`, destiné à servir "
        f"d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires "
        f"réelles). Toutes les données ci-dessous concernent uniquement la banque "
        f"{bank_label} (code `{bank}`, segment : {segment})."
    )
    lines.append("")

    lines.append("## Méthodologie")
    lines.append("")
    lines.append(f"- **Source Google Trends** : bibliothèque `pytrends`, geo=`{GEO}`, timeframe=`{TIMEFRAME}`.")
    lines.append(
        "- **Granularité réelle** : hebdomadaire (Google Trends bascule automatiquement "
        "en hebdomadaire pour une fenêtre de 5 ans, pas mensuel)."
    )
    lines.append(
        f"- **Détection d'anomalies** (par terme) : moyenne d'intérêt calculée par mois "
        f"calendaire sur toutes les années disponibles (profil de saisonnalité de référence). "
        f"Un point est flagué s'il dépasse à la fois (a) la moyenne générale du terme de plus "
        f"de {Z_SCORE_THRESHOLD} écart-type (z-score ≥ {Z_SCORE_THRESHOLD}) et (b) "
        f"{SEASONAL_RATIO_THRESHOLD}× la moyenne saisonnière normale de son mois. Les points "
        "flagués consécutifs sont groupés : un seul point isolé est un **pic isolé** "
        "(`isolated_spike`), deux points consécutifs ou plus sont une **tendance soutenue** "
        "(`sustained_trend`)."
    )
    lines.append(
        "- **Hors périmètre** : ce projet ne collecte aucune donnée publicitaire "
        "(Meta Ad Library, Google Ads Transparency Center). Le rapprochement entre ces "
        "anomalies et des campagnes publicitaires réelles est fait dans un pipeline séparé, "
        "en utilisant cet export comme donnée d'entrée."
    )
    append_term_selection_method(lines)
    lines.append("")

    append_known_events_section(lines, bank)

    lines.append(f"## Fiches produits {bank_label}")
    lines.append("")
    lines.append(f"| Fiche produit | Termes de recherche {bank_label} |")
    lines.append("|---|---|")
    for p in bank_products:
        bank_terms = [display_term(t["term"]) for t in p["terms"] if t["bank"] == bank]
        lines.append(f"| {p['product_label']} (`{p['product_id']}`) | {', '.join(bank_terms)} |")
    lines.append("")

    notes = PRODUCT_NOTES.get(bank)
    if notes:
        lines.append("### Notes produit")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Données Google Trends brutes")
    lines.append("")
    lines.append(
        f"{trends_row_count} points hebdomadaires, {term_count} termes, "
        f"du {min_date} au {max_date}. Fournies séparément dans "
        f"**`{csv_filename}`** (colonnes : product_id, product_label, term, bank, "
        "language, date, value) — non incluses ici pour garder ce document lisible."
    )
    lines.append("")

    lines.append(f"## Anomalies détectées ({len(anomaly_rows_fr)})")
    lines.append("")
    lines.append(md_table(anomaly_cols_fr, anomaly_rows_fr))
    lines.append("")

    return "\n".join(lines)


def run_export(bank, csv_filename, md_filename):
    csv_path = os.path.join(EXPORT_DIR, csv_filename)
    md_path = os.path.join(EXPORT_DIR, md_filename)

    conn = sqlite3.connect(DB_PATH)
    trends_row_count = export_trends_csv(conn, bank, csv_path)
    markdown = build_markdown(conn, bank, csv_filename, trends_row_count)
    conn.close()

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path} ({trends_row_count} rows)")


def export_all_trends_csv(conn, csv_path):
    columns, rows = fetch_all(
        conn,
        "SELECT product_id, product_label, term, bank, language, date, value "
        "FROM trends_data ORDER BY product_id, bank, term, date",
    )
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def build_markdown_all(conn, csv_filename, trends_row_count):
    _, trends_range = fetch_all(
        conn, "SELECT MIN(date), MAX(date), COUNT(DISTINCT term) FROM trends_data",
    )
    min_date, max_date, term_count = trends_range[0]

    validation = term_validation_lookup(conn)

    anomaly_cols_fr = [
        "Fiche produit", "Terme", "Banque", "Date", "Valeur", "Type d'anomalie",
        "Score de déviation", "Couverture du terme", "Flags du terme",
    ]
    _, anomaly_rows = fetch_all(
        conn,
        "SELECT product_id, term, bank, date, value, anomaly_type, deviation_score "
        "FROM anomalies ORDER BY product_id, date",
    )
    anomaly_rows_fr = []
    for r in anomaly_rows:
        coverage, flags = validation.get((r[0], r[1]), (None, ""))
        anomaly_rows_fr.append((
            r[0], display_term(r[1]), display_bank(r[2]), r[3], r[4],
            ANOMALY_TYPE_LABELS.get(r[5], r[5]), round(r[6], 3),
            format_coverage(coverage), flags,
        ))

    bank_list = ", ".join(display_bank(b) for b in BANK_DISPLAY_LABELS)

    lines = []
    lines.append("# Export combiné — Benchmark marketing ING vs concurrents")
    lines.append("")
    lines.append(
        f"Document généré automatiquement à partir de `benchmark.db`, destiné à servir "
        f"d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires "
        f"réelles). Couvre les {len(BANK_DISPLAY_LABELS)} banques du périmètre "
        f"({bank_list}) dans un seul document ; voir les exports par banque "
        f"(`kbc_data_export.md`, `ing_data_export.md`, `cbc_data_export.md`, "
        f"`bnppf_data_export.md`, `argenta_data_export.md`, `crelan_data_export.md`, "
        f"`revolut_data_export.md`, `n26_data_export.md`, `bunq_data_export.md`) pour les "
        f"versions filtrées."
    )
    lines.append("")

    lines.append("## Méthodologie")
    lines.append("")
    lines.append(f"- **Source Google Trends** : bibliothèque `pytrends`, geo=`{GEO}`, timeframe=`{TIMEFRAME}`.")
    lines.append(
        "- **Granularité réelle** : hebdomadaire (Google Trends bascule automatiquement "
        "en hebdomadaire pour une fenêtre de 5 ans, pas mensuel)."
    )
    lines.append(
        f"- **Détection d'anomalies** (par terme) : moyenne d'intérêt calculée par mois "
        f"calendaire sur toutes les années disponibles (profil de saisonnalité de référence). "
        f"Un point est flagué s'il dépasse à la fois (a) la moyenne générale du terme de plus "
        f"de {Z_SCORE_THRESHOLD} écart-type (z-score ≥ {Z_SCORE_THRESHOLD}) et (b) "
        f"{SEASONAL_RATIO_THRESHOLD}× la moyenne saisonnière normale de son mois. Les points "
        "flagués consécutifs sont groupés : un seul point isolé est un **pic isolé** "
        "(`isolated_spike`), deux points consécutifs ou plus sont une **tendance soutenue** "
        "(`sustained_trend`)."
    )
    lines.append(
        "- **Comparabilité des valeurs** : chaque fiche est une requête pytrends indépendante "
        "(jusqu'à 5 termes) ; les valeurs 0-100 ne sont comparables qu'à l'intérieur d'une même "
        "fiche (`product_id`), jamais entre deux fiches différentes."
    )
    lines.append(
        "- **Hors périmètre** : ce projet ne collecte aucune donnée publicitaire "
        "(Meta Ad Library, Google Ads Transparency Center). Le rapprochement entre ces "
        "anomalies et des campagnes publicitaires réelles est fait dans un pipeline séparé, "
        "en utilisant cet export comme donnée d'entrée."
    )
    append_term_selection_method(lines)
    lines.append("")

    append_known_events_section(lines)

    lines.append(f"## Fiches produits ({len(PRODUCTS)})")
    lines.append("")
    lines.append("| Fiche produit | Termes de recherche (banque) |")
    lines.append("|---|---|")
    for p in PRODUCTS:
        terms = [f"{display_term(t['term'])} ({display_bank(t['bank'])})" for t in p["terms"]]
        lines.append(f"| {p['product_label']} (`{p['product_id']}`) | {', '.join(terms)} |")
    lines.append("")

    lines.append("### Notes produit")
    lines.append("")
    for bank in BANK_DISPLAY_LABELS:
        for note in PRODUCT_NOTES.get(bank, []):
            lines.append(f"- **{display_bank(bank)}** — {note}")
    lines.append("")

    lines.append("## Données Google Trends brutes")
    lines.append("")
    lines.append(
        f"{trends_row_count} points hebdomadaires, {term_count} termes, "
        f"du {min_date} au {max_date}, toutes banques confondues. Fournies séparément dans "
        f"**`{csv_filename}`** (colonnes : product_id, product_label, term, bank, "
        "language, date, value) — non incluses ici pour garder ce document lisible."
    )
    lines.append("")

    lines.append(f"## Anomalies détectées ({len(anomaly_rows_fr)})")
    lines.append("")
    lines.append(md_table(anomaly_cols_fr, anomaly_rows_fr))
    lines.append("")

    return "\n".join(lines)


def run_export_all(csv_filename, md_filename):
    csv_path = os.path.join(EXPORT_DIR, csv_filename)
    md_path = os.path.join(EXPORT_DIR, md_filename)

    conn = sqlite3.connect(DB_PATH)
    trends_row_count = export_all_trends_csv(conn, csv_path)
    markdown = build_markdown_all(conn, csv_filename, trends_row_count)
    conn.close()

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path} ({trends_row_count} rows)")
