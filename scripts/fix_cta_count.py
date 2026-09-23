#!/usr/bin/env python3
"""Refresh cta_count/cta_above_fold from stored HTML, no LLM call, no re-fetch.

New script. `scraper.py::_count_ctas()` counted every <a>/<button>
whose label matched a keyword list, chrome included, duplicates included. That
made the feature a count of how often a page repeats "En savoir plus"-style
links rather than a count of calls to action:

    Crelan  42 hits, 20 distinct labels, "en savoir plus sur X" repeated up to 4x
    BNP     23 hits, mostly "en savoir plus" x6 and repeated product links
    ING      4 hits ("profitez de notre cashback" x2, ouvrir un compte, decouvrir plus)

Slide 12 read ING 3.0 vs peers 13.75 as "ING is behind on calls to action". The
detector now excludes navigation/footer chrome, drops hidden elements and counts
distinct (label, href) pairs - which is what the dictionary says the feature is,
"number of distinct call-to-action buttons or links".

This re-derives ONLY those two columns for every row whose HTML is still on
disk, using the same purely deterministic `extract()` the capture used. No LLM
call, so personas/cross-sell/imagery are not re-rolled (unlike
reextract_model_fields.py). cta_count feeds no derived feature, so nothing else
needs recomputing.

WHY THIS NEEDS NO NEW COMPLIANCE CHECK: same reasoning as fix_rate_fields.py -
it only re-reads `snapshot_html_path` already on disk, no new fetch, so
`assert_can_fetch()` does not apply.

    python3 scripts/fix_cta_count.py --dataset data/processed/campaigns.csv \
                                     --dataset data/processed/campaigns_scored.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd

from comparator.collection.scraper import extract


def fix_cta_count(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    """Re-derive cta_count/cta_above_fold wherever the snapshot HTML is on disk.

    Column order is preserved and only these two columns are written back: the
    scored dataset carries rubric columns the dictionary does not know about,
    and write_dataset() would move them to the end and bury the real diff.
    Rows without a readable snapshot are passed through unchanged - never
    invents a number for a page it cannot re-read."""
    before_order = list(df.columns)
    for i, row in df.iterrows():
        html_path = row.get("snapshot_html_path")
        if not isinstance(html_path, str) or not Path(html_path).is_file():
            print(f"  skip {row.get('page_id')}: no snapshot HTML on disk ({html_path})")
            continue

        html = Path(html_path).read_text(encoding="utf-8", errors="replace")
        features = extract(html, language=str(row.get("language", "fr")), page_url=str(row.get("url", "")))
        before = (row.get("cta_count"), row.get("cta_above_fold"))
        df.at[i, "cta_count"] = features["cta_count"]
        df.at[i, "cta_above_fold"] = features["cta_above_fold"]
        after = (features["cta_count"], features["cta_above_fold"])
        if before != after:
            print(f"  {row.get('page_id')}: cta_count {before[0]} -> {after[0]}, "
                  f"above_fold {before[1]} -> {after[1]}")
    return df[before_order]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, action="append", required=True,
                        help="dataset CSV to update in place; repeatable")
    args = parser.parse_args()

    for path in args.dataset:
        print(f"\n{path}")
        df = pd.read_csv(path, keep_default_na=True)
        updated = fix_cta_count(df, path)
        updated.to_csv(path, index=False)
        print(f"wrote {len(updated)} row(s) -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
