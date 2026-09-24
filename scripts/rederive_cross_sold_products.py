#!/usr/bin/env python3
"""Re-derive ONLY cross_sold_products, from the stored HTML snapshots.

cross_sold_products could name a product_family and nothing else, and the
taxonomy was the six banking families plus `other`. Insurance, credit cards and
partner perks are none of those, so every one of them collapsed into a single
`other` token counted once - which inverts the cross-sell score on exactly the
pages that cross-sell hardest. ING's pack pages name 8, 13 and 14 distinct
add-ons and scored 1/6, while pages naming 3 or 4 scored 2/6.

The dictionary now carries `insurance`, `credit_card` and `partner_perk`
(a pure addition, which the freeze rule allows), and the extraction prompt lists
them. This re-derives the column for rows collected before that.

ONE COLUMN, DELIBERATELY. The model call returns all 27 model_assisted fields,
and every other one is discarded. Six of them are quoted on presentation slides;
re-rolling those to fix an unrelated feature would trade a known problem for an
unknown one. `reextract_model_fields.py` is the script that rewrites them all,
and it is not this one.

WHY THIS NEEDS NO COMPLIANCE CHECK: same reasoning as rederive_urgency_markers.py
and fix_background_luminance.py - it re-reads a snapshot_html_path already on
disk, makes no fetch, so assert_can_fetch() does not apply.

    python3 scripts/rederive_cross_sold_products.py --dataset data/processed/campaigns.csv \
                                                    --dataset data/processed/campaigns_scored.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd
from bs4 import BeautifulSoup

from comparator.collection.llm_extractor import extract_model_assisted
from comparator.schema import format_list

COLUMN = "cross_sold_products"


def rederive(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    """Re-derive COLUMN wherever the HTML snapshot is on disk.

    Rows whose snapshot is missing, unreadable, or whose model call fails are
    passed through unchanged - never blanks a value it could not re-measure.
    """
    for i, row in df.iterrows():
        html_path = row.get("snapshot_html_path")
        if not isinstance(html_path, str) or not Path(html_path).is_file():
            print(f"  skip {row.get('page_id')}: no snapshot on disk ({html_path})")
            continue

        try:
            html = Path(html_path).read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)
            fields = extract_model_assisted(
                page_text=text,
                image_count=len(soup.find_all("img")),
                has_animation=False,
                product_family=str(row.get("product_family", "")),
            )
        except Exception as exc:  # noqa: BLE001 - one bad page must not stop the run
            print(f"  skip {row.get('page_id')}: {type(exc).__name__} {exc}")
            continue

        new = format_list(sorted(set(fields.cross_sold_products)))
        before = row.get(COLUMN)
        before_s = "" if pd.isna(before) else str(before)
        if new != before_s:
            print(f"  {row.get('page_id')}: {before_s or '(vide)'} -> {new or '(vide)'}")
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
