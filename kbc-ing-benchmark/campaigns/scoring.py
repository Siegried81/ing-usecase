"""Match campaigns to already-detected Trends anomalies and score them.

Pipeline (see module docstrings on each step for the exact rules):
1. For each campaign, resolve its attribution window (date_utils) and the
   fiches to search (target_fiches + marque_generique, or marque_generique
   alone for brand/sponsoring/csr campaigns with no target fiches).
2. Collect every anomaly of the campaign's own bank on those fiches inside
   the window as a candidate match.
3. Flag matches whose anomaly is also claimed by another campaign's window
   (overlapping_campaign_ids) and matches that coincide with a broad,
   campaign-less anomaly cluster on another bank that same week
   (possible_seasonal_confound).
4. Score: weighted, confound- and overlap-adjusted anomaly contributions,
   summed and multiplied by a breadth bonus for campaigns touching several
   fiches. Campaigns whose date cannot be windowed at all (bare year) or
   whose window falls entirely outside the Trends data range are marked
   not_scorable with a reason instead of being scored 0.

Results are persisted to campaign_anomaly_matches and campaign_scores,
fully replacing prior runs so this script is safe to re-run.
"""

import json
import logging
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH  # noqa: E402
from date_utils import DateTooImprecise, attribution_window  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUSTAINED_WEIGHT = 2
ISOLATED_WEIGHT = 1
DEVIATION_SCORE_CAP = 10
BREADTH_BONUS_PER_EXTRA_FICHE = 0.1
SEASONAL_CONFOUND_FACTOR = 0.3
SEASONAL_CONFOUND_MIN_FICHES = 2

MARQUE_GENERIQUE_FICHE = "marque_generique"


def iso_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def load_campaigns(conn):
    rows = conn.execute(
        "SELECT id, bank, name, start_date, end_date, date_confidence, campaign_type, target_fiches FROM campaigns"
    ).fetchall()
    campaigns = []
    for r in rows:
        campaigns.append({
            "id": r[0], "bank": r[1], "name": r[2], "start_date": r[3], "end_date": r[4],
            "date_confidence": r[5], "campaign_type": r[6],
            "target_fiches": json.loads(r[7]) if r[7] else None,
        })
    return campaigns


def load_anomalies(conn):
    rows = conn.execute(
        "SELECT id, product_id, term, bank, date, anomaly_type, deviation_score FROM anomalies"
    ).fetchall()
    anomalies = []
    for r in rows:
        anomalies.append({
            "id": r[0], "product_id": r[1], "term": r[2], "bank": r[3],
            "date": iso_date(r[4]), "anomaly_type": r[5], "deviation_score": r[6],
        })
    return anomalies


def get_trends_date_range(conn):
    row = conn.execute("SELECT MIN(date), MAX(date) FROM trends_data").fetchone()
    return iso_date(row[0]), iso_date(row[1])


def fiches_for_campaign(campaign):
    if campaign["target_fiches"]:
        return list(campaign["target_fiches"]) + [MARQUE_GENERIQUE_FICHE]
    return [MARQUE_GENERIQUE_FICHE]


def resolve_window(campaign, trends_min, trends_max):
    """Return (status, window_start, window_end, reason).
    status is 'ok' or 'not_scorable'; window bounds are None when not_scorable.
    """
    try:
        window_start, window_end = attribution_window(campaign["start_date"], campaign["end_date"])
    except DateTooImprecise:
        return "not_scorable", None, None, "date_too_imprecise"

    if window_end < trends_min or window_start > trends_max:
        return "not_scorable", None, None, "before_trends_window"

    # Clip to the available data range for the actual search, keeping the
    # true intended window implicit in the stored campaign dates for audit.
    clipped_start = max(window_start, trends_min)
    clipped_end = min(window_end, trends_max)
    return "ok", clipped_start, clipped_end, None


def find_matches(campaign, window_start, window_end, anomalies_by_bank_fiche):
    """KBC and CBC are the same corporate entity (KBC Group brand for
    Flanders vs. Wallonia), so a KBC/CBC campaign's *target* fiches are
    searched under both bank values - a shared-group product (e.g. the Kate
    digital assistant) can show up as a CBC-branded term even for a
    nominally KBC campaign, and vice versa. marque_generique always stays
    strict to the campaign's own bank, since it holds a real same-bank term
    to check rather than being a KBC/CBC-specific fiche. ING never blends
    with anything.
    """
    fiches = fiches_for_campaign(campaign)
    same_camp_banks = ("KBC", "CBC") if campaign["bank"] in ("KBC", "CBC") else (campaign["bank"],)

    matches = []
    for fiche in fiches:
        banks_to_check = (campaign["bank"],) if fiche == MARQUE_GENERIQUE_FICHE else same_camp_banks
        for bank in banks_to_check:
            for a in anomalies_by_bank_fiche.get((bank, fiche), []):
                if window_start <= a["date"] <= window_end:
                    matches.append(a)
    return matches


def build_week_fiche_index(anomalies):
    """(bank, iso_year, iso_week) -> set of distinct product_id with an
    anomaly that week. Used for the seasonal-confound check.
    """
    index = defaultdict(set)
    for a in anomalies:
        iso_year, iso_week, _ = a["date"].isocalendar()
        index[(a["bank"], iso_year, iso_week)].add(a["product_id"])
    return index


def bank_has_active_campaign(bank, day, campaigns_windows):
    for c in campaigns_windows:
        if c["bank"] != bank:
            continue
        if c["window_start"] <= day <= c["window_end"]:
            return True
    return False


def camp(bank):
    """KBC and CBC are the same corporate group; ING stands alone. Used so a
    sibling brand's activity is never mistaken for independent, market-wide
    seasonal noise (see find_matches for the same KBC/CBC grouping)."""
    return {"KBC", "CBC"} if bank in ("KBC", "CBC") else {"ING"}


def is_seasonal_confound(anomaly, campaign_bank, week_fiche_index, campaigns_windows, all_banks):
    iso_year, iso_week, _ = anomaly["date"].isocalendar()
    own_camp = camp(campaign_bank)
    for other_bank in all_banks:
        if other_bank in own_camp:
            continue
        if bank_has_active_campaign(other_bank, anomaly["date"], campaigns_windows):
            continue
        fiches_that_week = week_fiche_index.get((other_bank, iso_year, iso_week), set())
        if len(fiches_that_week) >= SEASONAL_CONFOUND_MIN_FICHES:
            return True
    return False


def score_campaign(matches_with_flags):
    """matches_with_flags: list of dicts with anomaly_type, deviation_score,
    possible_seasonal_confound, overlap_group_size. Returns
    (raw_score, contributions, fiches_touched, breadth_multiplier, final_score).
    """
    contributions = []
    fiches_touched = set()
    for m in matches_with_flags:
        weight = SUSTAINED_WEIGHT if m["anomaly_type"] == "sustained_trend" else ISOLATED_WEIGHT
        base = weight * min(m["deviation_score"], DEVIATION_SCORE_CAP)
        if m["possible_seasonal_confound"]:
            base *= SEASONAL_CONFOUND_FACTOR
        base /= m["overlap_group_size"]
        contributions.append(base)
        fiches_touched.add(m["product_id"])

    raw_score = sum(contributions)
    breadth_multiplier = 1 + BREADTH_BONUS_PER_EXTRA_FICHE * (len(fiches_touched) - 1) if fiches_touched else 1.0
    final_score = raw_score * breadth_multiplier
    return raw_score, contributions, len(fiches_touched), breadth_multiplier, final_score


def run_scoring(conn):
    campaigns = load_campaigns(conn)
    anomalies = load_anomalies(conn)
    trends_min, trends_max = get_trends_date_range(conn)
    all_banks = sorted({c["bank"] for c in campaigns} | {a["bank"] for a in anomalies})

    anomalies_by_bank_fiche = defaultdict(list)
    for a in anomalies:
        anomalies_by_bank_fiche[(a["bank"], a["product_id"])].append(a)

    week_fiche_index = build_week_fiche_index(anomalies)

    # First pass: resolve windows and candidate matches for every campaign.
    campaigns_windows = []
    candidate_matches = {}  # campaign_id -> list of anomaly dicts
    not_scorable = {}  # campaign_id -> reason
    for c in campaigns:
        status, window_start, window_end, reason = resolve_window(c, trends_min, trends_max)
        if status == "not_scorable":
            not_scorable[c["id"]] = reason
            continue
        campaigns_windows.append({"bank": c["bank"], "window_start": window_start, "window_end": window_end})
        candidate_matches[c["id"]] = find_matches(c, window_start, window_end, anomalies_by_bank_fiche)

    # Second pass: which campaigns claim each anomaly (for overlap sharing).
    claims_by_anomaly = defaultdict(list)
    for campaign_id, matches in candidate_matches.items():
        for a in matches:
            claims_by_anomaly[a["id"]].append(campaign_id)

    campaigns_by_id = {c["id"]: c for c in campaigns}

    # Third pass: flag confound/overlap and score each campaign.
    match_rows = []
    score_rows = []
    for c in campaigns:
        if c["id"] in not_scorable:
            score_rows.append({
                "campaign_id": c["id"], "status": "not_scorable",
                "not_scorable_reason": not_scorable[c["id"]],
                "anomaly_count": None, "fiches_touched": None, "seasonal_confound_count": None,
                "raw_score": None, "breadth_multiplier": None, "final_score": None,
            })
            continue

        # Window bounds were already used to build candidate_matches above;
        # only the period start is needed here, as the delay_days reference.
        period_start = attribution_window(c["start_date"], c["end_date"])[0]

        matches_with_flags = []
        confound_count = 0
        for a in candidate_matches[c["id"]]:
            overlapping = [cid for cid in claims_by_anomaly[a["id"]] if cid != c["id"]]
            group_size = len(overlapping) + 1
            confound = is_seasonal_confound(a, c["bank"], week_fiche_index, campaigns_windows, all_banks)
            if confound:
                confound_count += 1
            matches_with_flags.append({
                "anomaly": a, "anomaly_type": a["anomaly_type"], "deviation_score": a["deviation_score"],
                "product_id": a["product_id"], "possible_seasonal_confound": confound,
                "overlap_group_size": group_size, "overlapping_campaign_ids": overlapping,
                "delay_days": (a["date"] - period_start).days,
            })

        raw_score, contributions, fiches_touched, breadth_multiplier, final_score = score_campaign(matches_with_flags)

        for m, contribution in zip(matches_with_flags, contributions):
            match_rows.append((
                c["id"], m["anomaly"]["id"], m["delay_days"], int(m["possible_seasonal_confound"]),
                json.dumps(m["overlapping_campaign_ids"]) if m["overlapping_campaign_ids"] else None,
                round(contribution, 4),
            ))

        score_rows.append({
            "campaign_id": c["id"], "status": "scorable", "not_scorable_reason": None,
            "anomaly_count": len(matches_with_flags), "fiches_touched": fiches_touched,
            "seasonal_confound_count": confound_count,
            "raw_score": round(raw_score, 4), "breadth_multiplier": round(breadth_multiplier, 4),
            "final_score": round(final_score, 4),
        })

    persist(conn, match_rows, score_rows)
    log.info(
        "Scored %d campaigns: %d scorable, %d not_scorable.",
        len(campaigns), sum(1 for s in score_rows if s["status"] == "scorable"), len(not_scorable),
    )
    return score_rows


def persist(conn, match_rows, score_rows):
    conn.execute("DELETE FROM campaign_anomaly_matches")
    conn.execute("DELETE FROM campaign_scores")

    conn.executemany(
        """
        INSERT INTO campaign_anomaly_matches
            (campaign_id, anomaly_id, delay_days, possible_seasonal_confound, overlapping_campaign_ids, contribution)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        match_rows,
    )
    conn.executemany(
        """
        INSERT INTO campaign_scores
            (campaign_id, status, not_scorable_reason, anomaly_count, fiches_touched,
             seasonal_confound_count, raw_score, breadth_multiplier, final_score)
        VALUES (:campaign_id, :status, :not_scorable_reason, :anomaly_count, :fiches_touched,
                :seasonal_confound_count, :raw_score, :breadth_multiplier, :final_score)
        """,
        score_rows,
    )
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    run_scoring(conn)
    conn.close()


if __name__ == "__main__":
    main()
