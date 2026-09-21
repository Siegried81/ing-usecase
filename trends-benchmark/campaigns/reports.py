"""Generate the campaign deliverables from the scored data in benchmark.db:
- export/campaign_scorecards.md - one section per campaign (metadata,
  matched anomalies, score detail or not_scorable reason).
- export/campaign_scorecards.csv - one row per campaign, summary metrics.
- export/campaign_matches.csv - one row per matched anomaly, full audit
  detail (contribution, confound/overlap flags).
- export/campaigns_comparison.md - aggregate KBC vs CBC vs ING comparison.

Run after campaigns/scoring.py. Does not modify the database.
"""

import csv
import json
import logging
import os
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ANOMALY_TYPE_LABELS, BASE_DIR, DB_PATH, TERM_DISPLAY_LABELS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(BASE_DIR, "export")

NOT_SCORABLE_REASON_LABELS = {
    "before_trends_window": "Antérieure à la fenêtre Trends disponible (données depuis 2021-09-12)",
    "date_too_imprecise": "Date trop imprécise pour définir une fenêtre de rapprochement fiable",
}
CAMPAIGN_TYPE_LABELS = {
    "brand": "Image de marque", "product": "Produit", "sponsoring": "Sponsoring", "csr": "RSE/solidaire",
}
BANK_ORDER = ["KBC", "CBC", "ING"]


def display_term(term):
    return TERM_DISPLAY_LABELS.get(term, term)


def fetch_all(conn, query, params=()):
    cur = conn.execute(query, params)
    columns = [d[0] for d in cur.description]
    return columns, cur.fetchall()


def load_campaigns_with_scores(conn):
    _, rows = fetch_all(
        conn,
        """
        SELECT c.id, c.bank, c.name, c.language, c.start_date, c.end_date, c.date_confidence,
               c.agency, c.campaign_type, c.target_fiches, c.channels, c.source_url, c.notes,
               s.status, s.not_scorable_reason, s.anomaly_count, s.fiches_touched,
               s.seasonal_confound_count, s.raw_score, s.breadth_multiplier, s.final_score
        FROM campaigns c
        JOIN campaign_scores s ON s.campaign_id = c.id
        ORDER BY c.bank, c.start_date
        """,
    )
    campaigns = []
    for r in rows:
        campaigns.append({
            "id": r[0], "bank": r[1], "name": r[2], "language": r[3], "start_date": r[4],
            "end_date": r[5], "date_confidence": r[6], "agency": r[7], "campaign_type": r[8],
            "target_fiches": json.loads(r[9]) if r[9] else None, "channels": r[10],
            "source_url": r[11], "notes": r[12], "status": r[13], "not_scorable_reason": r[14],
            "anomaly_count": r[15], "fiches_touched": r[16], "seasonal_confound_count": r[17],
            "raw_score": r[18], "breadth_multiplier": r[19], "final_score": r[20],
        })
    return campaigns


def load_matches_for_campaign(conn, campaign_id):
    _, rows = fetch_all(
        conn,
        """
        SELECT a.product_id, a.term, a.bank, a.date, a.anomaly_type, a.deviation_score,
               m.delay_days, m.possible_seasonal_confound, m.overlapping_campaign_ids, m.contribution
        FROM campaign_anomaly_matches m
        JOIN anomalies a ON a.id = m.anomaly_id
        WHERE m.campaign_id = ?
        ORDER BY a.date
        """,
        (campaign_id,),
    )
    matches = []
    for r in rows:
        matches.append({
            "product_id": r[0], "term": r[1], "bank": r[2], "date": r[3], "anomaly_type": r[4],
            "deviation_score": r[5], "delay_days": r[6], "possible_seasonal_confound": bool(r[7]),
            "overlapping_campaign_ids": json.loads(r[8]) if r[8] else [], "contribution": r[9],
        })
    return matches


def md_table(columns, rows):
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        cells = ["" if v is None else str(v).replace("|", "-").replace("\n", " ") for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_scorecards_md(campaigns, matches_by_campaign):
    lines = ["# Fiches campagnes — rapprochement avec les anomalies Trends", ""]
    lines.append(
        "Une section par campagne cataloguée (KBC, CBC, ING) : métadonnées, anomalies "
        "Trends rapprochées dans la fenêtre d'attribution, et score d'efficacité détaillé. "
        "Voir `campaigns_comparison.md` pour la synthèse agrégée KBC vs CBC vs ING."
    )
    lines.append("")
    lines.append(
        "**Fenêtre d'attribution** : `[start_date, start_date + 21 jours]` (étendue à "
        "`end_date + 21 jours` si connue). **Fiches interrogées** : `target_fiches` + "
        "`marque_generique` de la banque, ou `marque_generique` seul pour les campagnes "
        "`brand`/`sponsoring`/`csr` sans `target_fiches`. **Score** : "
        "`Σ (poids_type × min(score_deviation, 10))` par anomalie rapprochée "
        "(poids 2 pour tendance soutenue, 1 pour pic isolé), avec un facteur ×0.3 sur les "
        "anomalies possiblement dues à une confusion saisonnière (motif large observé la "
        "même semaine chez une autre banque sans campagne active), une contribution "
        "partagée entre campagnes dont les fenêtres se chevauchent sur une même anomalie, "
        "puis un bonus de largeur ×(1 + 0.1×(N_fiches-1))."
    )
    lines.append("")

    for bank in BANK_ORDER:
        bank_campaigns = [c for c in campaigns if c["bank"] == bank]
        if not bank_campaigns:
            continue
        lines.append(f"## {bank}")
        lines.append("")
        for c in bank_campaigns:
            lines.append(f"### {c['name']}")
            lines.append("")
            period = c["start_date"] + (f" → {c['end_date']}" if c["end_date"] else "")
            lines.append(
                f"- **Période** : {period} (confiance : {c['date_confidence']}) — "
                f"**Type** : {CAMPAIGN_TYPE_LABELS.get(c['campaign_type'], c['campaign_type'])} — "
                f"**Langue** : {c['language']}"
            )
            if c["target_fiches"]:
                lines.append(f"- **Fiches ciblées** : {', '.join(c['target_fiches'])}")
            if c["notes"]:
                lines.append(f"- **Notes** : {c['notes']}")
            lines.append("")

            if c["status"] == "not_scorable":
                reason_label = NOT_SCORABLE_REASON_LABELS.get(c["not_scorable_reason"], c["not_scorable_reason"])
                lines.append(f"**Non notable** — {reason_label}.")
                lines.append("")
                continue

            matches = matches_by_campaign.get(c["id"], [])
            if matches:
                lines.append(f"**{len(matches)} anomalie(s) rapprochée(s)**")
                lines.append("")
                rows = []
                for m in matches:
                    rows.append((
                        display_term(m["term"]), m["bank"], m["date"],
                        ANOMALY_TYPE_LABELS.get(m["anomaly_type"], m["anomaly_type"]),
                        m["deviation_score"], f"+{m['delay_days']} j",
                        "Oui" if m["possible_seasonal_confound"] else "Non",
                        len(m["overlapping_campaign_ids"]) or "-",
                        round(m["contribution"], 3),
                    ))
                lines.append(md_table(
                    ["Terme", "Banque", "Date", "Type", "Score déviation", "Délai",
                     "Confusion saisonnière", "Campagnes concurrentes", "Contribution"],
                    rows,
                ))
                lines.append("")
            else:
                lines.append("Aucune anomalie rapprochée dans la fenêtre d'attribution.")
                lines.append("")

            lines.append(
                f"**Score** : {c['final_score']} "
                f"(brut {c['raw_score']} × bonus de largeur {c['breadth_multiplier']}, "
                f"{c['fiches_touched']} fiche(s) touchée(s), "
                f"{c['seasonal_confound_count']} anomalie(s) sous confusion saisonnière)"
            )
            lines.append("")

    with open(os.path.join(EXPORT_DIR, "campaign_scorecards.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info("Wrote campaign_scorecards.md")


def write_scorecards_csv(campaigns):
    path = os.path.join(EXPORT_DIR, "campaign_scorecards.csv")
    fieldnames = [
        "id", "bank", "name", "language", "start_date", "end_date", "date_confidence",
        "campaign_type", "target_fiches", "status", "not_scorable_reason",
        "anomaly_count", "fiches_touched", "seasonal_confound_count",
        "raw_score", "breadth_multiplier", "final_score",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for c in campaigns:
            row = dict(c)
            row["target_fiches"] = ";".join(c["target_fiches"]) if c["target_fiches"] else ""
            writer.writerow(row)
    log.info("Wrote campaign_scorecards.csv (%d rows)", len(campaigns))


def write_matches_csv(campaigns, matches_by_campaign):
    path = os.path.join(EXPORT_DIR, "campaign_matches.csv")
    fieldnames = [
        "campaign_id", "campaign_name", "campaign_bank", "product_id", "term", "anomaly_bank",
        "date", "anomaly_type", "deviation_score", "delay_days",
        "possible_seasonal_confound", "overlapping_campaign_ids", "contribution",
    ]
    total = 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in campaigns:
            for m in matches_by_campaign.get(c["id"], []):
                writer.writerow({
                    "campaign_id": c["id"], "campaign_name": c["name"], "campaign_bank": c["bank"],
                    "product_id": m["product_id"], "term": m["term"], "anomaly_bank": m["bank"],
                    "date": m["date"], "anomaly_type": m["anomaly_type"],
                    "deviation_score": m["deviation_score"], "delay_days": m["delay_days"],
                    "possible_seasonal_confound": m["possible_seasonal_confound"],
                    "overlapping_campaign_ids": ";".join(str(i) for i in m["overlapping_campaign_ids"]),
                    "contribution": m["contribution"],
                })
                total += 1
    log.info("Wrote campaign_matches.csv (%d rows)", total)


def aggregate_stats(scorable_campaigns):
    """Per-bank stats (KBC, CBC, ING kept fully separate - they are three
    distinct entities, not a merged camp)."""
    stats = {}
    for bank in BANK_ORDER:
        campaigns_in_group = [c for c in scorable_campaigns if c["bank"] == bank]
        total = len(campaigns_in_group)
        total_score = sum(c["final_score"] for c in campaigns_in_group)
        with_match = sum(1 for c in campaigns_in_group if c["anomaly_count"] > 0)
        type_counts = defaultdict(int)
        for c in campaigns_in_group:
            type_counts[c["campaign_type"]] += 1
        stats[bank] = {
            "total": total,
            "total_score": round(total_score, 3),
            "avg_score": round(total_score / total, 3) if total else None,
            "success_rate": round(with_match / total * 100, 1) if total else None,
            "type_counts": dict(type_counts),
        }
    return stats


def write_comparison_md(all_campaigns, scorable_campaigns):
    not_scorable = [c for c in all_campaigns if c["status"] == "not_scorable"]
    stats = aggregate_stats(scorable_campaigns)

    lines = ["# Comparatif agrégé — KBC vs CBC vs ING", ""]
    lines.append(
        f"Calculé sur les {len(scorable_campaigns)} campagnes notables (sur "
        f"{len(all_campaigns)} cataloguées ; {len(not_scorable)} non notables, voir en bas "
        "de document). KBC et CBC sont deux marques du même groupe (KBC Group) mais "
        "traitées ici comme deux entités distinctes, au même titre qu'ING."
    )
    lines.append("")

    lines.append("## Vue par banque")
    lines.append("")
    lines.append("| Banque | Campagnes notables | Score total | Score moyen | Taux de succès |")
    lines.append("|---|---|---|---|---|")
    for bank in BANK_ORDER:
        s = stats[bank]
        lines.append(
            f"| {bank} | {s['total']} | {s['total_score']} | {s['avg_score']} | {s['success_rate']}% |"
        )
    lines.append("")

    lines.append("## Répartition par type de campagne")
    lines.append("")
    lines.append("| Banque | Image de marque | Produit | Sponsoring | RSE/solidaire |")
    lines.append("|---|---|---|---|---|")
    for bank in BANK_ORDER:
        tc = stats[bank]["type_counts"]
        lines.append(
            f"| {bank} | {tc.get('brand', 0)} | {tc.get('product', 0)} | "
            f"{tc.get('sponsoring', 0)} | {tc.get('csr', 0)} |"
        )
    lines.append("")
    lines.append(
        "Une banque plus orientée sponsoring/image de marque aura structurellement moins de "
        "campagnes \"matchables\" sur une fiche produit précise (elles ne sont rapprochées "
        "qu'à `marque_generique`) — à garder en tête en comparant les scores bruts."
    )
    lines.append("")

    lines.append("## Classement des campagnes (toutes banques, notables uniquement)")
    lines.append("")
    ranked = sorted(scorable_campaigns, key=lambda c: c["final_score"], reverse=True)
    rows = [
        (i + 1, c["bank"], c["name"], c["campaign_type"], c["anomaly_count"], c["fiches_touched"], c["final_score"])
        for i, c in enumerate(ranked)
    ]
    lines.append(md_table(["#", "Banque", "Campagne", "Type", "Anomalies", "Fiches touchées", "Score"], rows))
    lines.append("")

    lines.append(f"## Campagnes non notables ({len(not_scorable)})")
    lines.append("")
    if not_scorable:
        rows = [
            (c["bank"], c["name"], c["start_date"],
             NOT_SCORABLE_REASON_LABELS.get(c["not_scorable_reason"], c["not_scorable_reason"]))
            for c in not_scorable
        ]
        lines.append(md_table(["Banque", "Campagne", "Date", "Raison"], rows))
    else:
        lines.append("Aucune.")
    lines.append("")

    with open(os.path.join(EXPORT_DIR, "campaigns_comparison.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info("Wrote campaigns_comparison.md")


def main():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    campaigns = load_campaigns_with_scores(conn)
    matches_by_campaign = {c["id"]: load_matches_for_campaign(conn, c["id"]) for c in campaigns}
    conn.close()

    scorable = [c for c in campaigns if c["status"] == "scorable"]

    write_scorecards_md(campaigns, matches_by_campaign)
    write_scorecards_csv(campaigns)
    write_matches_csv(campaigns, matches_by_campaign)
    write_comparison_md(campaigns, scorable)


if __name__ == "__main__":
    main()
