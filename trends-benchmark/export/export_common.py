"""Shared logic for the brand-notoriety export (see export_brand_notoriety.py).

Produces a Markdown report (methodology, share of search, known events,
anomalies) plus a CSV of the raw Trends time series and a CSV of the
derived brand_share_of_search table. Meant as the data handoff for a
downstream pipeline that matches these anomalies against real ad/campaign
activity.
"""

import csv
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (  # noqa: E402
    ANOMALY_TYPE_LABELS, BANK_DISPLAY_LABELS, DB_PATH, GEO, KNOWN_EVENTS,
    PRODUCTS, SEASONAL_RATIO_THRESHOLD, TERM_DISPLAY_LABELS, TIMEFRAME,
    Z_SCORE_THRESHOLD,
)

EXPORT_DIR = os.path.dirname(os.path.abspath(__file__))
IN_SCOPE_FICHES = tuple(p["product_id"] for p in PRODUCTS)


def display_term(term):
    return TERM_DISPLAY_LABELS.get(term, term)


def display_bank(bank):
    return BANK_DISPLAY_LABELS.get(bank, bank)


def fetch_all(conn, query, params=()):
    cur = conn.execute(query, params)
    columns = [d[0] for d in cur.description]
    return columns, cur.fetchall()


def md_table(columns, rows):
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        cells = ["" if v is None else str(v).replace("|", "-").replace("\n", " ") for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def brand_flags_lookup(conn):
    """term -> flags recorded for that brand's resolution (six-bank extension,
    phase 1A). Empty for ING/KBC/CBC, which predate term_validation.
    """
    try:
        _, rows = fetch_all(
            conn,
            "SELECT term, flags FROM term_validation WHERE scope = 'brand' "
            "AND call_index = 0 AND slot_language != '__done__'",
        )
    except sqlite3.OperationalError:
        return {}
    return {r[0]: r[1] or "" for r in rows}


def export_trends_csv(conn, csv_path):
    placeholders = ",".join("?" * len(IN_SCOPE_FICHES))
    columns, rows = fetch_all(
        conn,
        "SELECT product_id, product_label, term, bank, language, date, value "
        f"FROM trends_data WHERE product_id IN ({placeholders}) "
        "ORDER BY product_id, bank, term, date",
        IN_SCOPE_FICHES,
    )
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def export_share_csv(conn, csv_path):
    columns, rows = fetch_all(
        conn,
        "SELECT bank, date, source_fiche, raw_value, scale_factor, rescaled_value, share_pct "
        "FROM brand_share_of_search ORDER BY bank, date",
    )
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def known_events_rows():
    events = sorted(KNOWN_EVENTS, key=lambda e: e["date"])
    return [(e["date"], display_bank(e["bank"]), e["label"]) for e in events]


def aggregate_share(conn):
    _, rows = fetch_all(conn, "SELECT bank, SUM(rescaled_value) FROM brand_share_of_search GROUP BY bank")
    totals = dict(rows)
    grand_total = sum(totals.values())
    if grand_total == 0:
        return []
    ordered = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return [(display_bank(bank), f"{(total / grand_total) * 100:.1f}%") for bank, total in ordered]


def scale_factors(conn):
    _, rows = fetch_all(
        conn, "SELECT DISTINCT source_fiche, scale_factor FROM brand_share_of_search ORDER BY source_fiche"
    )
    return [(fiche, f"{factor:.4f}") for fiche, factor in rows]


def build_markdown(conn, trends_csv_filename, share_csv_filename, trends_row_count, share_row_count):
    _, trends_range = fetch_all(
        conn,
        "SELECT MIN(date), MAX(date) FROM trends_data WHERE product_id IN ({})".format(
            ",".join("?" * len(IN_SCOPE_FICHES))
        ),
        IN_SCOPE_FICHES,
    )
    min_date, max_date = trends_range[0]

    brand_flags = brand_flags_lookup(conn)

    anomaly_cols = [
        "Fiche", "Terme", "Banque", "Date", "Valeur",
        "Type d'anomalie", "Score de déviation", "Flags du terme",
    ]
    placeholders = ",".join("?" * len(IN_SCOPE_FICHES))
    _, anomaly_rows = fetch_all(
        conn,
        "SELECT product_id, term, bank, date, value, anomaly_type, deviation_score FROM anomalies "
        f"WHERE product_id IN ({placeholders}) ORDER BY date",
        IN_SCOPE_FICHES,
    )
    anomaly_rows_fmt = [
        (
            r[0], display_term(r[1]), display_bank(r[2]), r[3], r[4],
            ANOMALY_TYPE_LABELS.get(r[5], r[5]), round(r[6], 3), brand_flags.get(r[1], ""),
        )
        for r in anomaly_rows
    ]

    lines = []
    lines.append("# Export notoriété de marque — Benchmark ING vs concurrents")
    lines.append("")
    lines.append(
        "Document généré automatiquement à partir de `benchmark.db`, destiné à servir "
        "d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires "
        "réelles). Le projet compare uniquement la notoriété de marque (recherche du nom de "
        "banque, sans contexte produit) des 9 banques du panel : ING, KBC, CBC, BNP Paribas "
        "Fortis, Argenta, Crelan, Revolut, N26, bunq."
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
        "- **Chaînage / share of search** : les 9 banques sont réparties sur 3 fiches "
        "(`marque_generique`, `marque_generique_traditionnelles`, "
        "`marque_generique_neobanques`), limite pytrends de 5 termes par requête oblige. "
        "`ING` et `KBC` apparaissent, inchangés, dans les 3 requêtes : ils servent d'ancre "
        "commune. Pour chaque fiche autre que la référence (`marque_generique`), un facteur "
        "d'échelle unique est calculé sur la moyenne des deux ancres, puis appliqué à ses "
        "autres termes (voir `analysis/share_of_search.py`). La part de voix se calcule ensuite "
        "sur le volume rescalé : `part(banque) = volume_rescalé(banque) / somme_9_banques`, "
        "sur la somme des valeurs de toute la période (pas une moyenne des parts "
        "hebdomadaires, pour ne pas sur-pondérer les semaines à volume quasi nul)."
    )
    lines.append(
        "- **Limite du chaînage** : cette technique suppose que le ratio d'échelle entre deux "
        "requêtes pytrends reste stable sur toute la période - hypothèse standard de cette "
        "méthode, mais approximative."
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
        "- **Désambiguïsation des marques** (BNPPF, Argenta, N26 passent par un topic "
        "Knowledge Graph plutôt qu'une chaîne brute) : voir `data/term_validation_report.md` "
        "et `docs/pipeline_google_trends.md` section 7bis."
    )
    lines.append(
        "- **Hors périmètre** : ce projet ne collecte aucune donnée publicitaire "
        "(Meta Ad Library, Google Ads Transparency Center). Le rapprochement entre ces "
        "anomalies et des campagnes publicitaires réelles est fait dans un pipeline séparé, "
        "en utilisant cet export comme donnée d'entrée."
    )
    lines.append("")

    lines.append("## Événements structurels connus")
    lines.append("")
    lines.append(
        "Ruptures de marché documentées, fournies pour interprétation : elles produisent "
        "des anomalies attendues qui ne sont pas des campagnes publicitaires. Cette liste "
        "n'intervient jamais dans la détection."
    )
    lines.append("")
    lines.append(md_table(["Date", "Banque", "Événement"], known_events_rows()))
    lines.append("")

    lines.append("## Fiches marque")
    lines.append("")
    lines.append("| Fiche | Termes de recherche (banque) |")
    lines.append("|---|---|")
    for p in PRODUCTS:
        terms = [f"{display_term(t['term'])} ({display_bank(t['bank'])})" for t in p["terms"]]
        lines.append(f"| {p['product_label']} (`{p['product_id']}`) | {', '.join(terms)} |")
    lines.append("")

    lines.append("## Part de voix (share of search)")
    lines.append("")
    lines.append(
        "Part de chaque banque sur le volume de recherche total du panel des 9 banques, sur "
        f"l'ensemble de la période. Détail hebdomadaire dans **`{share_csv_filename}`**."
    )
    lines.append("")
    lines.append(md_table(["Banque", "Part de voix"], aggregate_share(conn)))
    lines.append("")
    lines.append("Facteurs d'échelle appliqués (chaînage vers `marque_generique`) :")
    lines.append("")
    lines.append(md_table(["Fiche source", "Facteur"], scale_factors(conn)))
    lines.append("")

    lines.append("## Données Google Trends brutes")
    lines.append("")
    lines.append(
        f"{trends_row_count} points hebdomadaires, du {min_date} au {max_date}. Fournies "
        f"séparément dans **`{trends_csv_filename}`** (colonnes : product_id, product_label, "
        f"term, bank, language, date, value) et, sous forme rescalée avec part de voix, dans "
        f"**`{share_csv_filename}`** ({share_row_count} lignes) - non incluses ici pour garder "
        "ce document lisible."
    )
    lines.append("")

    lines.append(f"## Anomalies détectées ({len(anomaly_rows_fmt)})")
    lines.append("")
    lines.append(md_table(anomaly_cols, anomaly_rows_fmt))
    lines.append("")

    return "\n".join(lines)


def run_export(trends_csv_filename, share_csv_filename, md_filename):
    trends_csv_path = os.path.join(EXPORT_DIR, trends_csv_filename)
    share_csv_path = os.path.join(EXPORT_DIR, share_csv_filename)
    md_path = os.path.join(EXPORT_DIR, md_filename)

    conn = sqlite3.connect(DB_PATH)
    trends_row_count = export_trends_csv(conn, trends_csv_path)
    share_row_count = export_share_csv(conn, share_csv_path)
    markdown = build_markdown(conn, trends_csv_filename, share_csv_filename, trends_row_count, share_row_count)
    conn.close()

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Wrote {md_path}")
    print(f"Wrote {trends_csv_path} ({trends_row_count} rows)")
    print(f"Wrote {share_csv_path} ({share_row_count} rows)")
