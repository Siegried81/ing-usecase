#!/usr/bin/env python3
"""Re-run model-assisted extraction on already-captured pages, no re-fetch.

sieg 19/09, new script. `target_personas` and `cross_sold_products` were added
to `llm_extractor.py`'s structured call AFTER every real page in
`campaigns.csv` was already collected - so every real row has these two
fields blank, not because no bank targets anyone or cross-sells anything, but
because the model was never asked. This backfills them (and refreshes every
other model_assisted field at the same time, since the extractor is the same
single call either way) from the HTML already saved on disk.

NOTE: every re-run makes a fresh LLM call, so it is NOT a no-op on rows that
already have values - re-running this after the 19/09 backfill measurably
changed personas/cross-sell/imagery on several rows (LLM non-determinism).
Don't run this again just to fix an unrelated deterministic field - see
scripts/fix_rate_fields.py for that (no LLM call, touches only two columns).

WHY THIS NEEDS NO NEW COMPLIANCE CHECK: `compliance.py::assert_can_fetch()`
gates a FETCH of a bank's site, and there is none here - the page was already
lawfully collected (its `robots_allowed=True` already travels with the row),
and this only re-reads the stored `snapshot_html_path` from local disk and
calls the model on the text. Re-reading a file we already have is not a new
fetch, so this deliberately does not call `assert_can_fetch()` again.

    python3 scripts/reextract_model_fields.py --dataset data/processed/campaigns.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd

from comparator.collection.llm_extractor import LLMExtractionError, extract_model_assisted_with_provenance
from comparator.collection.scraper import extract
from comparator.derive import recompute_derived
from comparator.dictionary import load_dictionary
from comparator.schema import read_dataset, write_dataset


def reextract(df: pd.DataFrame, fd) -> pd.DataFrame:
    """Return a new frame with model_assisted fields refreshed wherever the
    row's snapshot HTML is still on disk. Rows without it are passed through
    unchanged - never invents a value for a page it cannot re-read."""
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
        try:
            model_fields, extraction_model = extract_model_assisted_with_provenance(
                features.get("_page_text", ""),
                image_count=features["image_count"],
                has_animation=features["has_animation"],
                product_family=str(row_dict["product_family"]),
            )
        except LLMExtractionError as exc:
            print(f"  FAILED {row_dict.get('page_id')}: {exc}")
            rows.append(row_dict)
            continue

        row_dict.update(model_fields.model_dump())
        row_dict["extraction_model"] = extraction_model
        print(f"  updated {row_dict.get('page_id')} ({extraction_model}) - "
              f"personas={model_fields.target_personas}, cross_sold={model_fields.cross_sold_products}")
        rows.append(row_dict)

    return recompute_derived(pd.DataFrame(rows), fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/campaigns.csv"))
    parser.add_argument("--out", type=Path, default=None, help="defaults to --dataset (overwrite in place)")
    args = parser.parse_args()

    fd = load_dictionary()
    df, _report = read_dataset(args.dataset, fd, tier="core", strict=False)
    updated_df = reextract(df, fd)

    out = args.out or args.dataset
    write_dataset(updated_df, out, fd)
    print(f"\nwrote {len(updated_df)} row(s) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
