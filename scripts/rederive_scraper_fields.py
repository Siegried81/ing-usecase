#!/usr/bin/env python3
"""Re-derive the text-measured scraper columns from the stored HTML snapshots.

Several scraper rules changed how they read a page: a bare "-" or "'" is no
longer a word (word_count and everything computed from it), a nested disclaimer
block is counted once, a page with no <section>/<article> has 0 sections instead
of a missing value, and rate / deadline keywords must be whole words. This
re-measures the affected columns with the capture's own parser, from the
snapshot already on disk, so every row is measured with the same rule.

WHY THIS NEEDS NO COMPLIANCE CHECK: same reasoning as rederive_urgency_markers.py.
It re-reads a snapshot_html_path already on disk and makes no fetch, so
assert_can_fetch() does not apply. Rows whose snapshot is missing are left as
they are; no number is invented for a page that cannot be re-measured.

    python3 scripts/rederive_scraper_fields.py --dataset data/processed/campaigns.csv \
        --dataset data/processed/campaigns_scored.csv --dataset data/processed/real_captures.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
import pandas as pd

from comparator.collection.scraper import extract

COLUMNS = (
    "word_count", "word_count_band", "sentence_count", "sentence_count_band",
    "avg_sentence_length", "avg_sentence_length_band",
    "readability_score", "readability_band",
    "second_person_ratio", "second_person_ratio_band",
    "first_person_plural_count", "first_person_plural_band",
    "urgency_marker_count", "rate_shown", "rate_value_pct",
    "disclaimer_present", "disclaimer_word_share", "disclaimer_word_share_band",
    "text_to_image_ratio", "text_to_image_ratio_band", "section_count",
)


def _text(value: object) -> str:
    """How a measured value is written in the CSV: blank for None, plain str otherwise."""
    return "" if value is None else str(value)


def _same(old: str, new: object) -> bool:
    if old == "" or new is None:
        return old == "" and new is None
    try:
        return abs(float(old) - float(new)) < 1e-9
    except ValueError:
        return old == str(new)


def rederive(df: pd.DataFrame) -> pd.DataFrame:
    """Re-measure COLUMNS wherever the HTML snapshot is on disk, and print each change.

    The frame is read as text so every cell that does not change is written back
    byte for byte; only a re-measured cell is touched.
    """
    columns = [c for c in COLUMNS if c in df.columns]
    for i, row in df.iterrows():
        html_path = row.get("snapshot_html_path")
        if not html_path or not Path(html_path).is_file():
            print(f"  skip {row.get('page_id')}: no snapshot on disk ({html_path})")
            continue
        html = Path(html_path).read_text(encoding="utf-8", errors="ignore")
        measured = extract(html, language=row["language"], page_url=row.get("url", ""))
        for column in columns:
            if not _same(row[column], measured[column]):
                print(f"  {row.get('page_id')}: {column} {row[column] or 'blank'} -> {_text(measured[column]) or 'blank'}")
                df.at[i, column] = _text(measured[column])
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", action="append", required=True, type=Path)
    args = parser.parse_args()
    for path in args.dataset:
        if not path.is_file():
            print(f"skipping {path}: not found")
            continue
        print(path)
        rederive(pd.read_csv(path, dtype=str, keep_default_na=False)).to_csv(path, index=False, lineterminator="\n")


if __name__ == "__main__":
    main()
