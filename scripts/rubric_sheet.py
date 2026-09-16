#!/usr/bin/env python3
"""Emit, merge and check the human rubric scores.

    python3 scripts/rubric_sheet.py emit  --raters siegried stephane
    python3 scripts/rubric_sheet.py merge --sheets data/rubric/*_scored.csv
    python3 scripts/rubric_sheet.py agreement --sheets data/rubric/*_scored.csv

steph 16/09. 13 core features are scored by a person, so a collected dataset can
never pass strict validation on its own - this is the missing step between
collection and analysis, and what the Day 5 scoring session actually fills in.
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import _bootstrap  # noqa: F401

from comparator import load_dictionary
from comparator.rubric import (
    agreement,
    disagreement_table,
    make_sheet,
    merge_scores,
    read_sheets,
    sheet_guide,
)
from comparator.schema import read_dataset, validate, write_dataset

DEFAULT_DATASET = Path("data/processed/campaigns.csv")
DEFAULT_DIR = Path("data/rubric")


def _expand(patterns: list[str]) -> list[Path]:
    out: list[Path] = []
    for pattern in patterns:
        out.extend(Path(p) for p in sorted(glob.glob(pattern)))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    emit = sub.add_parser("emit", help="write one empty scoring sheet per rater")
    emit.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    emit.add_argument("--outdir", type=Path, default=DEFAULT_DIR)
    emit.add_argument("--raters", nargs="+", default=["siegried", "dan", "stephane"])
    emit.add_argument("--include-unusable", action="store_true",
                      help="also list captures flagged unusable (normally a waste of a rater's time)")

    merge = sub.add_parser("merge", help="fold completed sheets into the dataset")
    merge.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    merge.add_argument("--sheets", nargs="+", required=True)
    merge.add_argument("--out", type=Path, default=Path("data/processed/campaigns_scored.csv"))

    agree = sub.add_parser("agreement", help="report inter-rater disagreement (NFR-05)")
    agree.add_argument("--sheets", nargs="+", required=True)

    # steph 16/09: renders Sieg's docs/day5_scoring_disagreement_template.md from
    # the sheets, so the number that goes in the deck is computed, not retyped.
    report = sub.add_parser("report", help="render the Day 5 disagreement table from the sheets")
    report.add_argument("--sheets", nargs="+", required=True)
    report.add_argument("--out", type=Path, default=Path("docs/day5_scoring_disagreement.md"))

    args = parser.parse_args()
    fd = load_dictionary()

    if args.command == "emit":
        df, report = read_dataset(args.dataset, fd, tier="core", strict=False)
        print(report.render())
        args.outdir.mkdir(parents=True, exist_ok=True)

        for rater in args.raters:
            sheet = make_sheet(df, fd, rater=rater, skip_unusable=not args.include_unusable)
            path = args.outdir / f"{rater}_scores.csv"
            sheet.to_csv(path, index=False)
            print(f"  {len(sheet)} page(s) to score -> {path}")

        guide = args.outdir / "SCORING_GUIDE.md"
        guide.write_text(sheet_guide(fd), encoding="utf-8")
        print(f"  guide -> {guide}")
        print("\nScore independently, do not confer - the agreement number only means "
              "something if the scores are independent.")
        return 0

    sheets = read_sheets(_expand(args.sheets))
    if not sheets:
        print("no sheets matched")
        return 2

    if args.command == "agreement":
        print(agreement(sheets, fd).render())
        return 0

    if args.command == "report":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(disagreement_table(sheets, fd), encoding="utf-8")
        print(f"wrote {args.out}")
        return 0

    df, _ = read_dataset(args.dataset, fd, tier="core", strict=False)
    merged = merge_scores(df, sheets, fd)
    write_dataset(merged, args.out, fd)
    print(f"merged {len(sheets)} sheet(s) -> {args.out}\n")
    print(validate(merged, fd, tier="core").render())
    print()
    print(agreement(sheets, fd).render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
