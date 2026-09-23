#!/usr/bin/env python3
"""Re-derive background_luminance from the first screen of stored screenshots.

sieg 23/09, new script. background_luminance was the count-weighted mean
luminance of the WHOLE page strip. On a long page that measures how much white
body copy the page has, not how dark it is: ING's expat page has a black hero
over a long white body and scored 0.916 (near white) on a 14,516px capture,
where its first screen reads 0.521. The feature fed a D06 claim - "ING is
measurably darker than its peers" - that the current data had already
inverted, which is how the wrong measurement surfaced.

The fix is in visual_features.extract_colours_from_image(first_screen_px=...)
so new captures are measured correctly; this re-derives the column for rows
collected before it, from the screenshot already on disk.

Only background_luminance is rewritten. brand_colour_share, palette_hex,
dominant_colour_hex and accent_colour_count deliberately keep their full-page
basis (steph 16/09: a brand accent is a few percent of a page, and cropping
would re-break the fix that stopped every bank scoring 0.000).

WHY THIS NEEDS NO COMPLIANCE CHECK: same reasoning as fix_cta_count.py and
fix_rate_fields.py - it re-reads a screenshot_path already on disk, makes no
fetch, so assert_can_fetch() does not apply.

    python3 scripts/fix_background_luminance.py --dataset data/processed/campaigns.csv \
                                                --dataset data/processed/campaigns_scored.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd
from PIL import Image

from comparator.collection.render import VIEWPORT_HEIGHT
from comparator.collection.visual_features import extract_colours_from_image

COLUMN = "background_luminance"


def fix_luminance(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    """Re-derive COLUMN wherever the screenshot is on disk.

    Rows whose screenshot is missing or unreadable are passed through
    unchanged - never invents a number for a page it cannot re-measure.
    """
    for i, row in df.iterrows():
        shot_path = row.get("screenshot_path")
        if not isinstance(shot_path, str) or not Path(shot_path).is_file():
            print(f"  skip {row.get('page_id')}: no screenshot on disk ({shot_path})")
            continue

        try:
            with Image.open(shot_path) as img:
                measured = extract_colours_from_image(
                    img, bank=str(row.get("bank", "")), first_screen_px=VIEWPORT_HEIGHT
                )
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the run
            print(f"  skip {row.get('page_id')}: unreadable screenshot ({exc})")
            continue

        new = measured[COLUMN]
        if new is None:
            print(f"  skip {row.get('page_id')}: measurement returned nothing")
            continue

        before = row.get(COLUMN)
        if pd.isna(before) or round(float(before), 3) != new:
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
        fix_luminance(df, path).to_csv(path, index=False)


if __name__ == "__main__":
    main()
