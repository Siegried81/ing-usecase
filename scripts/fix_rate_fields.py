#!/usr/bin/env python3
"""Refresh rate_shown/rate_value_pct from stored HTML, no LLM call, no re-fetch.

New script. `scraper.py::_rate()` used to match the FIRST "N%"
anywhere on a page, so marketing copy like "100% en ligne" was reported as a
rate - verified in the wild: BNP Paribas Fortis, KBC (x3) and ING all showed
rate_value_pct=100.00 identically. Fixed in `_rate()` (now requires a rate
keyword near the match). This script re-derives ONLY `rate_shown` and
`rate_value_pct` for every row whose HTML is still on disk, using the same
purely deterministic `extract()` the initial capture used - no LLM call, so
no risk of re-rolling personas/cross-sell/imagery the way re-running
`reextract_model_fields.py` would (that script makes a fresh, non-
deterministic LLM call per row - confirmed by trying it here first).

WHY THIS NEEDS NO NEW COMPLIANCE CHECK: same reasoning as
reextract_model_fields.py - this only re-reads `snapshot_html_path` already
on disk, no new fetch, so `assert_can_fetch()` does not apply.

    python3 scripts/fix_rate_fields.py --dataset data/processed/campaigns.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd

from comparator.collection.scraper import extract
from comparator.derive import recompute_derived
from comparator.dictionary import load_dictionary
from comparator.schema import read_dataset, write_dataset


def fix_rate_fields(df: pd.DataFrame, fd) -> pd.DataFrame:
    """Return a new frame with rate_shown/rate_value_pct re-derived wherever
    the row's snapshot HTML is still on disk. Rows without it are passed
    through unchanged - never invents a value for a page it cannot re-read."""
    rows: list[dict] = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        html_path = row_dict.get("snapshot_html_path")
        if not isinstance(html_path, str) or not Path(html_path).is_file():
            print(f"  skip {row_dict.get('page_id')}: no snapshot HTML on disk ({html_path})")
            rows.append(row_dict)
            continue

        html = Path(html_path).read_text(encoding="utf-8", errors="replace")
        features = extract(html, language=str(row_dict.get("language", "fr")), page_url=str(row_dict.get("url", "")))
        before = (row_dict.get("rate_shown"), row_dict.get("rate_value_pct"))
        row_dict["rate_shown"] = features["rate_shown"]
        row_dict["rate_value_pct"] = features["rate_value_pct"]
        after = (row_dict["rate_shown"], row_dict["rate_value_pct"])
        if before != after:
            print(f"  {row_dict.get('page_id')}: {before} -> {after}")
        rows.append(row_dict)

    return recompute_derived(pd.DataFrame(rows), fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/campaigns.csv"))
    parser.add_argument("--out", type=Path, default=None, help="defaults to --dataset (overwrite in place)")
    args = parser.parse_args()

    fd = load_dictionary()
    df, _report = read_dataset(args.dataset, fd, tier="core", strict=False)
    updated_df = fix_rate_fields(df, fd)

    out = args.out or args.dataset
    write_dataset(updated_df, out, fd)
    print(f"\nwrote {len(updated_df)} row(s) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
