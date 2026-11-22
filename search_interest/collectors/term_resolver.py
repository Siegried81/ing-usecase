"""Brand term resolution (BNP Paribas Fortis, Argenta, Crelan, Revolut, N26,
bunq).

Tests the candidate terms declared in config_candidates.py against live
Google Trends data and records every observation in the term_validation
table, plus a human-readable summary in data/term_validation_report.md.
Never writes to config.PRODUCTS: the winning terms are copied there by hand
after human review of the report. Product-level resolution is gone, since the
pipeline only measures brand notoriety.

Resumable: a fiche (brand, brand_fiche or context_fiche) whose
"__done__" marker row already exists in term_validation is skipped, so an
interrupted run can be restarted without re-testing finished fiches.
Network calls reuse the exact throttling policy of
collectors/trends_collector.py via pytrends_network.py: strict sequential
calls, a fixed pause after each success, exponential backoff with jitter
on failure.
"""

import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

from pytrends.request import TrendReq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BASE_DIR, BRAND_MIN_COVERAGE, DB_PATH, GEO, SCHEMA_PATH, TIMEFRAME
import config_candidates as cc
from pytrends_network import fetch_with_retry, pause_between_calls, suggestions_with_retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Section 2.3: no existing neutral language convention was found (the
# current CBC topic and app_mobile terms are all mislabeled "en" rather
# than carrying a genuine neutral value), so per the brief's fallback rule
# this pipeline introduces "multi" for terms that are not tied to one
# search language (topics, app names, brand terms).
LANGUAGE_NEUTRAL = "multi"

VALIDATION_DIR = os.path.join(BASE_DIR, "data", "validation")
REPORT_PATH = os.path.join(BASE_DIR, "data", "term_validation_report.md")

DONE_MARKER = "__done__"

# Names used to check "title contains the brand name" for topic validity.
BRAND_MATCH_NAME = {
    "BNPPF": "BNP Paribas Fortis",
    "ARGENTA": "Argenta",
    "CRELAN": "Crelan",
    "REVOLUT": "Revolut",
    "N26": "N26",
    "BUNQ": "bunq",
    "ING": "ING",
    "KBC": "KBC",
}

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def dump_call_csv(pid, call_index, df):
    os.makedirs(VALIDATION_DIR, exist_ok=True)
    out = df.copy()
    out.index.name = "Time"
    out.to_csv(os.path.join(VALIDATION_DIR, f"{pid}_call{call_index}.csv"))


def compute_coverage(df, term_col):
    clean = df[df["isPartial"] == False] if "isPartial" in df.columns else df
    total = len(clean)
    if total == 0:
        return 0, 0, 0.0, 0.0
    nonzero = int((clean[term_col] != 0).sum())
    coverage = nonzero / total
    mean_value = float(clean[term_col].mean())
    return nonzero, total, coverage, mean_value


def term_kind_of(term):
    return "topic" if term.startswith("/m/") or term.startswith("/g/") else "string"


def upsert_validation_row(conn, **row):
    conn.execute(
        """
        INSERT INTO term_validation (
            scope, product_id, bank, slot_language, candidate_rank, term, term_kind,
            topic_title, topic_type, call_index, nonzero_points, total_points,
            coverage, mean_value, verdict, flags, tested_at
        ) VALUES (
            :scope, :product_id, :bank, :slot_language, :candidate_rank, :term, :term_kind,
            :topic_title, :topic_type, :call_index, :nonzero_points, :total_points,
            :coverage, :mean_value, :verdict, :flags, :tested_at
        )
        ON CONFLICT (scope, product_id, bank, slot_language, term, call_index) DO UPDATE SET
            candidate_rank = excluded.candidate_rank,
            term_kind = excluded.term_kind,
            topic_title = excluded.topic_title,
            topic_type = excluded.topic_type,
            nonzero_points = excluded.nonzero_points,
            total_points = excluded.total_points,
            coverage = excluded.coverage,
            mean_value = excluded.mean_value,
            verdict = excluded.verdict,
            flags = excluded.flags,
            tested_at = excluded.tested_at
        """,
        row,
    )
    conn.commit()


def is_fiche_done(conn, scope, product_id, bank):
    row = conn.execute(
        "SELECT 1 FROM term_validation WHERE scope = ? AND product_id = ? AND bank = ? "
        "AND slot_language = ? AND call_index = 0",
        (scope, product_id, bank, DONE_MARKER),
    ).fetchone()
    return row is not None


def mark_fiche_done(conn, scope, product_id, bank, verdict):
    upsert_validation_row(
        conn, scope=scope, product_id=product_id, bank=bank, slot_language=DONE_MARKER,
        candidate_rank=0, term=DONE_MARKER, term_kind="string", topic_title=None, topic_type=None,
        call_index=0, nonzero_points=0, total_points=0, coverage=0.0, mean_value=0.0,
        verdict=verdict, flags=None, tested_at=now_iso(),
    )


def get_final_brand(conn, bank):
    row = conn.execute(
        "SELECT term, term_kind, coverage, mean_value, verdict, flags FROM term_validation "
        "WHERE scope = 'brand' AND product_id = ? AND bank = ? AND call_index = 0 AND slot_language != ?",
        (f"__brand__{bank}", bank, DONE_MARKER),
    ).fetchone()
    if row is None:
        return None
    return {"term": row[0], "kind": row[1], "coverage": row[2], "mean": row[3], "verdict": row[4], "flags": row[5]}


# --------------------------------------------------------------------------
# Phase 1A: brand terms (section 3.3)
# --------------------------------------------------------------------------

def brand_name_in_title(name, title):
    return name.lower() in (title or "").lower()


def type_matches(ttype):
    t = (ttype or "").lower()
    return any(k in t for k in cc.TOPIC_TYPE_KEYWORDS)


def gather_topic_candidates(pytrends, bank, keywords):
    topics = []
    seen_mids = set()
    for kw in keywords:
        suggestions = suggestions_with_retry(pytrends, kw)
        pause_between_calls()
        for s in suggestions:
            mid = s.get("mid")
            if not mid or mid in seen_mids:
                continue
            seen_mids.add(mid)
            topics.append((mid, s.get("title", ""), s.get("type", "")))
    name = BRAND_MATCH_NAME[bank]
    return [(mid, title, ttype) for mid, title, ttype in topics if brand_name_in_title(name, title) and type_matches(ttype)]


def candidates_within_request_limit(topics, strings, limit=5):
    """Topics first, but never at the cost of every string.

    A request carries at most `limit` terms. Cutting topics + strings at the
    limit dropped all the strings when enough topics matched, and then
    decide_brand_winner had no string to fall back on.
    """
    strings = strings[:limit]
    return topics[:limit - len(strings)] + strings


def decide_brand_winner(spec, results):
    flags = []
    if spec["topic_required"]:
        valid_topics = [r for r in results if r["kind"] == "topic" and r["coverage"] >= BRAND_MIN_COVERAGE]
        if valid_topics:
            return valid_topics[0], flags
        valid_strings = [r for r in results if r["kind"] == "string" and r["coverage"] >= BRAND_MIN_COVERAGE]
        if valid_strings:
            flags.append("ambiguous_string")
            return valid_strings[0], flags
        strings = [r for r in results if r["kind"] == "string"]
        flags.append("ambiguous_string")
        return strings[0], flags
    strings = [r for r in results if r["kind"] == "string"]
    return strings[0], flags


def resolve_brand(conn, pytrends, bank, spec, informational=False):
    fiche_pid = f"__brand__{bank}"
    scope = "brand"
    if is_fiche_done(conn, scope, fiche_pid, bank):
        log.info("Skipping brand %s - already resolved.", bank)
        return get_final_brand(conn, bank)

    valid_topics = gather_topic_candidates(pytrends, bank, spec["suggestion_keywords"])

    topics = [{"term": mid, "kind": "topic", "title": title, "type": ttype} for mid, title, ttype in valid_topics]
    strings = [{"term": t, "kind": "string", "title": None, "type": None} for t in spec["string_candidates"]]
    candidates = candidates_within_request_limit(topics, strings)

    kw_list = [c["term"] for c in candidates]
    log.info("Brand %s: testing %s", bank, kw_list)
    df = fetch_with_retry(pytrends, kw_list, TIMEFRAME, GEO)
    dump_call_csv(fiche_pid, 1, df)
    pause_between_calls()

    results = []
    for rank, c in enumerate(candidates, start=1):
        nz, tot, cov, mean = compute_coverage(df, c["term"])
        result = {**c, "rank": rank, "coverage": cov, "mean": mean, "nonzero": nz, "total": tot}
        results.append(result)
        upsert_validation_row(
            conn, scope=scope, product_id=fiche_pid, bank=bank, slot_language=LANGUAGE_NEUTRAL,
            candidate_rank=rank, term=c["term"], term_kind=c["kind"], topic_title=c["title"],
            topic_type=c["type"], call_index=1, nonzero_points=nz, total_points=tot,
            coverage=cov, mean_value=mean, verdict="info_only", flags=None, tested_at=now_iso(),
        )

    if informational:
        mark_fiche_done(conn, scope, fiche_pid, bank, "info_only")
        return None

    winner, flags = decide_brand_winner(spec, results)
    upsert_validation_row(
        conn, scope=scope, product_id=fiche_pid, bank=bank, slot_language=LANGUAGE_NEUTRAL,
        candidate_rank=winner["rank"], term=winner["term"], term_kind=winner["kind"],
        topic_title=winner["title"], topic_type=winner["type"], call_index=0,
        nonzero_points=winner["nonzero"], total_points=winner["total"], coverage=winner["coverage"],
        mean_value=winner["mean"], verdict="selected", flags=",".join(flags) if flags else None,
        tested_at=now_iso(),
    )
    mark_fiche_done(conn, scope, fiche_pid, bank, "selected")
    return get_final_brand(conn, bank)


# --------------------------------------------------------------------------
# Section 4.3: brand and context fiches (control calls, no selection)
# --------------------------------------------------------------------------

def resolve_brand_fiche(conn, pytrends, fiche):
    pid = fiche["product_id"]
    scope = "brand_fiche"
    if is_fiche_done(conn, scope, pid, "ALL"):
        log.info("Skipping brand fiche %s - already resolved.", pid)
        return

    terms = list(cc.ING_KBC_ANCHOR_TERMS)
    for bank in fiche["brand_banks"]:
        winner = get_final_brand(conn, bank)
        if winner is None:
            log.warning("No resolved brand term for %s yet - run brand resolution first.", bank)
            return
        terms.append({"term": winner["term"], "bank": bank, "language": LANGUAGE_NEUTRAL})

    kw_list = [t["term"] for t in terms]
    log.info("Brand fiche %s: %s", pid, kw_list)
    df = fetch_with_retry(pytrends, kw_list, TIMEFRAME, GEO)
    dump_call_csv(pid, 1, df)
    pause_between_calls()

    for t in terms:
        nz, tot, cov, mean = compute_coverage(df, t["term"])
        upsert_validation_row(
            conn, scope=scope, product_id=pid, bank=t["bank"], slot_language=t["language"],
            candidate_rank=1, term=t["term"], term_kind=term_kind_of(t["term"]), topic_title=None,
            topic_type=None, call_index=1, nonzero_points=nz, total_points=tot, coverage=cov,
            mean_value=mean, verdict="info_only", flags=None, tested_at=now_iso(),
        )

    mark_fiche_done(conn, scope, pid, "ALL", "info_only")


def resolve_context_fiche(conn, pytrends, fiche):
    pid = fiche["product_id"]
    scope = "context_fiche"
    if is_fiche_done(conn, scope, pid, "ALL"):
        log.info("Skipping context fiche %s - already resolved.", pid)
        return

    bank = fiche["brand_bank"]
    winner = get_final_brand(conn, bank)
    if winner is None:
        log.warning("No resolved brand term for %s yet - run brand resolution first.", bank)
        return

    terms = [{"term": "ING", "bank": "ING", "language": "en"}]
    terms.append({"term": winner["term"], "bank": bank, "language": LANGUAGE_NEUTRAL})
    terms += fiche["extra_terms"]

    kw_list = [t["term"] for t in terms]
    log.info("Context fiche %s: %s", pid, kw_list)
    df = fetch_with_retry(pytrends, kw_list, TIMEFRAME, GEO)
    dump_call_csv(pid, 1, df)
    pause_between_calls()

    for t in terms:
        nz, tot, cov, mean = compute_coverage(df, t["term"])
        upsert_validation_row(
            conn, scope=scope, product_id=pid, bank=t["bank"], slot_language=t["language"],
            candidate_rank=1, term=t["term"], term_kind=term_kind_of(t["term"]), topic_title=None,
            topic_type=None, call_index=1, nonzero_points=nz, total_points=tot, coverage=cov,
            mean_value=mean, verdict="info_only", flags=None, tested_at=now_iso(),
        )

    mark_fiche_done(conn, scope, pid, "ALL", "info_only")


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def md_table(columns, rows):
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        cells = ["" if v is None else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(conn, timings):
    lines = []
    lines.append("# Rapport de validation des termes — extension six banques")
    lines.append("")
    lines.append(
        "Genere par collectors/term_resolver.py. Ne modifie jamais config.PRODUCTS - "
        "sert de base a la revue humaine avant mise a jour manuelle (phase 2)."
    )
    lines.append("")

    lines.append("## Convention de langue neutre")
    lines.append("")
    lines.append(
        f"Aucune convention neutre existante n'a ete trouvee (les termes CBC/app_mobile "
        f"existants sont tous étiquetés `en` par defaut). Valeur retenue pour les nouveaux "
        f"termes neutres (topics de marque, noms d'application) : `{LANGUAGE_NEUTRAL}`."
    )
    lines.append("")

    lines.append("## Marques (phase 1A)")
    lines.append("")
    brand_cols = ["Banque", "Rang", "Terme", "Type", "Titre topic", "Type topic", "Couverture", "Moyenne", "Verdict"]
    brand_rows = conn.execute(
        "SELECT bank, candidate_rank, term, term_kind, topic_title, topic_type, coverage, mean_value, verdict "
        "FROM term_validation WHERE scope = 'brand' AND slot_language != ? AND call_index IN (0, 1) "
        "ORDER BY bank, call_index DESC, candidate_rank",
        (DONE_MARKER,),
    ).fetchall()
    formatted = [(r[0], r[1], r[2], r[3], r[4] or "", r[5] or "", f"{r[6]:.3f}", f"{r[7]:.2f}", r[8]) for r in brand_rows]
    lines.append(md_table(brand_cols, formatted))
    lines.append("")

    lines.append("## Controle informatif ING / KBC (chaine brute vs topic)")
    lines.append("")
    control_rows = conn.execute(
        "SELECT bank, candidate_rank, term, term_kind, topic_title, topic_type, coverage, mean_value "
        "FROM term_validation WHERE scope = 'brand' AND bank IN ('ING', 'KBC') AND call_index = 1 "
        "ORDER BY bank, candidate_rank",
    ).fetchall()
    formatted = [(r[0], r[1], r[2], r[3], r[4] or "", r[5] or "", f"{r[6]:.3f}", f"{r[7]:.2f}") for r in control_rows]
    lines.append(md_table(brand_cols[:-1], formatted))
    lines.append("")

    lines.append("## Fiches marque et contexte (section 4.3, appels de controle)")
    lines.append("")
    fiche_cols = ["Fiche", "Banque", "Langue", "Terme", "Couverture", "Moyenne"]
    fiche_rows = conn.execute(
        "SELECT product_id, bank, slot_language, term, coverage, mean_value FROM term_validation "
        "WHERE scope IN ('brand_fiche', 'context_fiche') AND call_index = 1 "
        "ORDER BY product_id, slot_language",
    ).fetchall()
    formatted = [(r[0], r[1], r[2], r[3], f"{r[4]:.3f}", f"{r[5]:.2f}") for r in fiche_rows]
    lines.append(md_table(fiche_cols, formatted))
    lines.append("")

    lines.append("## Duree observee")
    lines.append("")
    for label, seconds in timings.items():
        lines.append(f"- {label} : {seconds / 60:.1f} min")
    lines.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info("Wrote report: %s", REPORT_PATH)


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    pytrends = TrendReq(hl="fr-BE", tz=60)

    t0 = time.time()

    for bank, spec in cc.CONTROL_BRANDS.items():
        resolve_brand(conn, pytrends, bank, spec, informational=True)
    for bank, spec in cc.BRAND_CANDIDATES.items():
        resolve_brand(conn, pytrends, bank, spec, informational=False)

    t1 = time.time()

    for fiche in cc.BRAND_FICHES:
        resolve_brand_fiche(conn, pytrends, fiche)
    for fiche in cc.CONTEXT_FICHES:
        resolve_context_fiche(conn, pytrends, fiche)

    t2 = time.time()

    timings = {
        "Phase 1A (marques)": t1 - t0,
        "Fiches marque/contexte": t2 - t1,
        "Total": t2 - t0,
    }
    write_report(conn, timings)

    conn.close()
    log.info("Term resolution complete.")


if __name__ == "__main__":
    main()
