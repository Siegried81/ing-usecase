#!/usr/bin/env python3
"""Re-derive urgency_marker_count from the stored HTML snapshots.

urgency_marker_count used to be a per-language term list only. The dictionary
defines the feature as "scarcity or DEADLINE language", and a term list cannot
catch a deadline that lives in a date rather than in a word: "Déposez 50 € ...
avant le 11/10/2026" carries none of the listed terms and scored 0, while a
page saying "offre temporaire" with no date at all scored several.

scraper._count_urgency_markers() now also counts a deadline preposition with a
date close behind it; this re-derives the column for rows collected before that,
from the snapshot already on disk. Every row is re-measured with the same rule,
so no bank is scored on a different basis from another.

WHY THIS NEEDS NO COMPLIANCE CHECK: same reasoning as fix_background_luminance.py
and fix_cta_count.py - it re-reads a snapshot_html_path already on disk, makes
no fetch, so assert_can_fetch() does not apply.

    python3 scripts/rederive_urgency_markers.py --dataset data/processed/campaigns.csv \
                                                --dataset data/processed/campaigns_scored.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd
from bs4 import BeautifulSoup

from comparator.collection.scraper import _count_urgency_markers

COLUMN = "urgency_marker_count"


def rederive(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    """Re-derive COLUMN wherever the HTML snapshot is on disk.

    Rows whose snapshot is missing or unreadable are passed through unchanged -
    never invents a number for a page it cannot re-measure.
    """
    for i, row in df.iterrows():
        html_path = row.get("snapshot_html_path")
        if not isinstance(html_path, str) or not Path(html_path).is_file():
            print(f"  skip {row.get('page_id')}: no snapshot on disk ({html_path})")
            continue

        try:
            html = Path(html_path).read_text(encoding="utf-8", errors="ignore")
            text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the run
            print(f"  skip {row.get('page_id')}: unreadable snapshot ({exc})")
            continue

        new = _count_urgency_markers(text, str(row.get("language", "en")))
        before = row.get(COLUMN)
        if pd.isna(before) or int(before) != new:
            print(f"  {row.get('page_id')}: {COLUMN} {before} -> {new}")
            df.at[i, COLUMN] = new

    print(f"wrote {len(df)} row(s) -> {path}\n")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", action="append", required=True, type=Path)
    args = parser.parse_args()

    for path in args.dataset:
        if not path.is_file():
            print(f"skipping {path}: not found")
            continue
        print(f"{path}")
        df = pd.read_csv(path)
        if COLUMN not in df.columns:
            print(f"  skipping: no {COLUMN} column\n")
            continue
        rederive(df, path).to_csv(path, index=False)


if __name__ == "__main__":
    main()
