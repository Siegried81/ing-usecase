"""Share-of-search analysis: chains every generic-brand sheet in
config.PRODUCTS onto one common weekly scale via their shared ING/KBC
anchor terms, then derives each bank's share of the whole panel.

Google Trends values are only comparable within one request (max 5 terms),
so with more banks than fit in one request, ING and KBC (present, unchanged,
in every sheet) are used as a bridge: for each non-reference sheet, a single
scale factor is computed from the ratio of anchor-term means against the
reference sheet, then applied to that sheet's other terms. This assumes the
scale ratio between two pytrends requests is stable over the period, which
is the standard (if approximate) assumption behind this chaining technique.
The sheet count is never hardcoded here: bridge_fiches() loops over
whatever config.PRODUCTS holds besides the reference sheet, so adding a new
bridge sheet needs no code change.

Run as a separate pipeline step (python analysis/share_of_search.py),
sourced only from trends_data - never recomputed at display time; app.py
and export/ only read the resulting brand_share_of_search table.
"""

import logging
import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (  # noqa: E402
    DB_PATH, PRODUCTS, SCHEMA_PATH, SHARE_OF_SEARCH_ANCHOR_BANKS,
    SHARE_OF_SEARCH_REFERENCE_FICHE,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def ensure_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def load_trends_data(conn):
    return pd.read_sql_query("SELECT * FROM trends_data", conn, parse_dates=["date"])


def bridge_fiches():
    return [p for p in PRODUCTS if p["product_id"] != SHARE_OF_SEARCH_REFERENCE_FICHE]


def anchor_mean(data, product_id, bank):
    subset = data[(data["product_id"] == product_id) & (data["bank"] == bank)]
    if subset.empty:
        raise ValueError(f"No trends_data for bank={bank} in fiche={product_id}.")
    return subset["value"].mean()


def compute_scale_factor(data, reference_fiche, bridge_fiche):
    ref_sum = sum(anchor_mean(data, reference_fiche, bank) for bank in SHARE_OF_SEARCH_ANCHOR_BANKS)
    bridge_sum = sum(anchor_mean(data, bridge_fiche, bank) for bank in SHARE_OF_SEARCH_ANCHOR_BANKS)
    if bridge_sum == 0:
        raise ValueError(f"Anchor terms are flat at zero in fiche={bridge_fiche}, cannot chain.")
    return ref_sum / bridge_sum


def build_rows(data):
    reference = SHARE_OF_SEARCH_REFERENCE_FICHE
    rows = []

    ref_data = data[data["product_id"] == reference]
    for r in ref_data.itertuples():
        rows.append((r.bank, r.date, reference, r.value, 1.0, float(r.value)))

    for fiche in bridge_fiches():
        pid = fiche["product_id"]
        factor = compute_scale_factor(data, reference, pid)
        log.info("Scale factor %s -> %s: %.4f", pid, reference, factor)

        non_anchor_banks = {t["bank"] for t in fiche["terms"]} - set(SHARE_OF_SEARCH_ANCHOR_BANKS)
        fiche_data = data[(data["product_id"] == pid) & (data["bank"].isin(non_anchor_banks))]
        for r in fiche_data.itertuples():
            rows.append((r.bank, r.date, pid, r.value, factor, r.value * factor))

    df = pd.DataFrame(
        rows, columns=["bank", "date", "source_fiche", "raw_value", "scale_factor", "rescaled_value"]
    )
    totals = df.groupby("date")["rescaled_value"].transform("sum")
    df["share_pct"] = (df["rescaled_value"] / totals).where(totals > 0, 0.0)
    return df


def store(conn, df):
    conn.execute("DELETE FROM brand_share_of_search")
    rows = [
        (
            r.bank, r.date.strftime("%Y-%m-%d"), r.source_fiche, int(r.raw_value),
            float(r.scale_factor), float(r.rescaled_value), float(r.share_pct),
        )
        for r in df.itertuples()
    ]
    conn.executemany(
        """
        INSERT INTO brand_share_of_search
            (bank, date, source_fiche, raw_value, scale_factor, rescaled_value, share_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (bank, date) DO UPDATE SET
            source_fiche = excluded.source_fiche,
            raw_value = excluded.raw_value,
            scale_factor = excluded.scale_factor,
            rescaled_value = excluded.rescaled_value,
            share_pct = excluded.share_pct
        """,
        rows,
    )
    conn.commit()
    log.info("Stored %d rows in brand_share_of_search.", len(rows))


def aggregate_share(conn):
    """One row per bank: its share of total search volume over the whole
    window (sum of values, not a mean of weekly shares, so weeks with
    near-zero total volume do not get over-weighted).
    """
    df = pd.read_sql_query("SELECT bank, rescaled_value FROM brand_share_of_search", conn)
    totals = df.groupby("bank")["rescaled_value"].sum()
    grand_total = totals.sum()
    return (totals / grand_total).sort_values(ascending=False)


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)

    data = load_trends_data(conn)
    if data.empty:
        log.warning("trends_data is empty, nothing to analyze.")
        conn.close()
        return

    df = build_rows(data)
    store(conn, df)

    for bank, share in aggregate_share(conn).items():
        log.info("%s: %.2f%% share of search", bank, share * 100)

    conn.close()


if __name__ == "__main__":
    main()
