"""Load the campaign catalog (campaigns/seed_data.py) into benchmark.db.

Idempotent: fully replaces the campaigns table with the current seed_data
content on every run, so removing an entry from seed_data.py actually
removes it from the database instead of leaving a stale row behind.
Dependent tables (campaign_anomaly_matches, campaign_scores) are rebuilt
from scratch by campaigns/scoring.py regardless, so this is safe.
"""

import json
import logging
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH, SCHEMA_PATH  # noqa: E402
from seed_data import CAMPAIGNS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def ensure_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def load(conn):
    rows = [
        (
            c["bank"], c["name"], c["language"], c["start_date"], c.get("end_date"),
            c["date_confidence"], c.get("agency"), c["campaign_type"],
            json.dumps(c["target_fiches"]) if c.get("target_fiches") else None,
            c.get("channels"), c.get("source_url"), c.get("notes"),
        )
        for c in CAMPAIGNS
    ]

    conn.execute("DELETE FROM campaign_anomaly_matches")
    conn.execute("DELETE FROM campaign_scores")
    conn.execute("DELETE FROM campaigns")
    conn.executemany(
        """
        INSERT INTO campaigns
            (bank, name, language, start_date, end_date, date_confidence,
             agency, campaign_type, target_fiches, channels, source_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    log.info("Loaded %d campaigns (%d KBC, %d CBC, %d ING).", len(rows),
              sum(1 for c in CAMPAIGNS if c["bank"] == "KBC"),
              sum(1 for c in CAMPAIGNS if c["bank"] == "CBC"),
              sum(1 for c in CAMPAIGNS if c["bank"] == "ING"))


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    load(conn)
    conn.close()


if __name__ == "__main__":
    main()
