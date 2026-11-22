"""Fetch Google Trends interest-over-time data for each KBC vs ING product
sheet and store it in SQLite, plus one CSV export per sheet.

Strictly sequential (no parallel requests): one pytrends call per product
sheet, a fixed pause of at least MIN_DELAY_SECONDS after every sheet, and
exponential backoff with jitter on 429 responses. Resumable: a sheet already
present in trends_data is skipped, so an interrupted run can be restarted
without re-downloading completed sheets.
"""

import logging
import os
import sqlite3
import sys
import time

from pytrends.request import TrendReq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pytrends_network import MIN_DELAY_SECONDS, fetch_with_retry

from config import CSV_DIR, DB_PATH, GEO, PRODUCTS, SCHEMA_PATH, TIMEFRAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def init_db(conn):
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def sync_products_table(conn):
    rows = [(p["product_id"], p["product_label"], len(p["terms"])) for p in PRODUCTS]
    conn.executemany(
        """
        INSERT INTO products (product_id, product_label, term_count)
        VALUES (?, ?, ?)
        ON CONFLICT (product_id) DO UPDATE SET
            product_label = excluded.product_label,
            term_count = excluded.term_count
        """,
        rows,
    )
    conn.commit()


def already_collected(conn, product_id):
    row = conn.execute(
        "SELECT 1 FROM trends_data WHERE product_id = ? LIMIT 1", (product_id,)
    ).fetchone()
    return row is not None


def export_csv(product_id, df):
    os.makedirs(CSV_DIR, exist_ok=True)
    out = df.drop(columns=["isPartial"], errors="ignore").copy()
    out.index.name = "Time"
    out_path = os.path.join(CSV_DIR, f"{product_id}.csv")
    out.to_csv(out_path)
    log.info("Wrote CSV: %s", out_path)


def store_long_format(conn, product, df):
    """Store the series in long format, minus Google's still-incomplete last period.

    pytrends flags the current, unfinished week with isPartial=True; its value
    is built from a few days and sits well below the finished weeks, so storing
    it would show up as a fake drop (term_resolver's coverage already ignores
    partial points for the same reason).
    """
    if "isPartial" in df.columns:
        df = df[~df["isPartial"].astype(bool)]
    term_meta = {t["term"]: (t["bank"], t["language"]) for t in product["terms"]}
    rows = []
    for term in df.columns:
        if term == "isPartial":
            continue
        bank, language = term_meta[term]
        for date, value in df[term].items():
            rows.append((
                product["product_id"], product["product_label"], term, bank, language,
                date.strftime("%Y-%m-%d"), int(value),
            ))

    conn.executemany(
        """
        INSERT INTO trends_data (product_id, product_label, term, bank, language, date, value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (product_id, term, date) DO UPDATE SET value = excluded.value
        """,
        rows,
    )
    conn.commit()
    log.info("Stored %d rows for product_id=%s.", len(rows), product["product_id"])


def main():
    pytrends = TrendReq(hl="fr-BE", tz=60)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    sync_products_table(conn)

    total = len(PRODUCTS)
    for i, product in enumerate(PRODUCTS, start=1):
        pid = product["product_id"]

        if already_collected(conn, pid):
            log.info("[%d/%d] Skipping '%s' — already collected.", i, total, pid)
            continue

        kw_list = [t["term"] for t in product["terms"]]
        if len(kw_list) > 5:
            raise ValueError(f"Product sheet '{pid}' has {len(kw_list)} terms, pytrends allows at most 5.")

        log.info("[%d/%d] Fetching '%s' (%d terms): %s", i, total, pid, len(kw_list), kw_list)
        try:
            df = fetch_with_retry(pytrends, kw_list, TIMEFRAME, GEO)
        except Exception:
            log.error("Skipping '%s' after repeated failures; will retry on next run.", pid)
            continue

        if df is None or df.empty:
            log.warning("Empty result for product_id=%s, skipping.", pid)
            continue

        export_csv(pid, df)
        store_long_format(conn, product, df)

        if i < total:
            log.info("Pausing %ds before the next sheet.", MIN_DELAY_SECONDS)
            time.sleep(MIN_DELAY_SECONDS)

    conn.close()
    log.info("Collection complete. Database at %s", DB_PATH)


if __name__ == "__main__":
    main()
