"""Standalone anomaly detection over trends_data.

For each (product_id, term) series, flags data points that exceed both the
term's overall baseline and its normal seasonal level for that calendar
month. Consecutive flagged points are grouped: a single flagged week is an
isolated spike, two or more consecutive flagged weeks are a sustained
trend. Run separately from the Streamlit app so detection is not
recomputed on every page load.
"""

import logging
import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH, SCHEMA_PATH, SEASONAL_RATIO_THRESHOLD, Z_SCORE_THRESHOLD  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def ensure_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def load_trends_data(conn):
    return pd.read_sql_query("SELECT * FROM trends_data", conn, parse_dates=["date"])


def detect_for_series(series):
    """series: DataFrame with columns date, value, sorted by date.
    Returns a list of dicts: date, value, anomaly_type, deviation_score.
    """
    series = series.sort_values("date").reset_index(drop=True)
    values = series["value"]

    overall_mean = values.mean()
    overall_std = values.std(ddof=0)
    if overall_std == 0 or overall_mean == 0:
        return []

    months = series["date"].dt.month
    seasonal_mean = values.groupby(months).transform("mean")

    z_scores = (values - overall_mean) / overall_std
    seasonal_ratio = values / seasonal_mean.replace(0, pd.NA)

    is_candidate = (z_scores >= Z_SCORE_THRESHOLD) & (seasonal_ratio >= SEASONAL_RATIO_THRESHOLD)
    is_candidate = is_candidate.fillna(False)

    results = []
    run_start = None
    for i in range(len(series) + 1):
        flagged = bool(is_candidate.iloc[i]) if i < len(series) else False
        if flagged and run_start is None:
            run_start = i
        elif not flagged and run_start is not None:
            run_indices = list(range(run_start, i))
            anomaly_type = "isolated_spike" if len(run_indices) == 1 else "sustained_trend"
            for idx in run_indices:
                results.append({
                    "date": series.loc[idx, "date"].strftime("%Y-%m-%d"),
                    "value": int(series.loc[idx, "value"]),
                    "anomaly_type": anomaly_type,
                    "deviation_score": round(float(z_scores.iloc[idx]), 3),
                })
            run_start = None

    return results


def run_detection(conn):
    conn.execute("DELETE FROM anomalies")

    data = load_trends_data(conn)
    if data.empty:
        log.warning("trends_data is empty, nothing to analyze.")
        return

    rows = []
    grouped = data.groupby(["product_id", "term", "bank"])
    for (product_id, term, bank), group in grouped:
        anomalies = detect_for_series(group[["date", "value"]])
        for a in anomalies:
            rows.append((
                product_id, term, bank,
                a["date"], a["value"], a["anomaly_type"], a["deviation_score"],
            ))
        if anomalies:
            log.info("product=%s term=%s: %d anomalies detected", product_id, term, len(anomalies))

    conn.executemany(
        """
        INSERT INTO anomalies (product_id, term, bank, date, value, anomaly_type, deviation_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (product_id, term, date) DO UPDATE SET
            value = excluded.value,
            anomaly_type = excluded.anomaly_type,
            deviation_score = excluded.deviation_score
        """,
        rows,
    )
    conn.commit()
    log.info("Anomaly detection complete: %d anomalies stored.", len(rows))


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    run_detection(conn)
    conn.close()


if __name__ == "__main__":
    main()
