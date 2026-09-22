#!/usr/bin/env python3
"""Emit the scoring sheet and merge it back into the dataset.

    python3 scripts/rubric_sheet.py emit  --rater siegried
    python3 scripts/rubric_sheet.py merge --sheet data/rubric/siegried_scores.csv

13 core features are scored by a person, so a collected dataset can
never pass strict validation on its own - this is the missing step between
collection and analysis.

The project runs on ONE judged sheet by one named person. The
`agreement`, `report` and `model` subcommands are gone with the inter-rater
layer: no second rater, no Cohen's kappa, no disagreement table, no
model-written sheet to compare against. Single-judge bias is out of scope for
this proof of concept and is listed as future work by limitations.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from comparator import load_dictionary
from comparator.rubric import make_sheet, merge_scores, read_sheets, rubric_features, sheet_guide
from comparator.schema import read_dataset, validate, write_dataset

DEFAULT_DATASET = Path("data/processed/campaigns.csv")
DEFAULT_DIR = Path("data/rubric")


def _coverage(sheet, df, fd) -> None:
    """Say what the merge actually joined, instead of leaving it to be assumed.

    A sheet row whose page_id is not in the dataset is dropped by the
    join without a word. That is how 13 of the scored pages went missing once
    already - their captures were never imported, so the ids matched nothing.
    A silent drop is the one failure this step must not have.
    """
    known = set(df["page_id"])
    scored = set(sheet["page_id"].dropna())
    unmatched = sorted(scored - known)
    print(f"  {len(sheet)} row(s) read, {len(scored & known)} matched a page in the dataset")
    if unmatched:
        print(f"  {len(unmatched)} row(s) matched NO page and were ignored:")
        for pid in unmatched:
            print(f"      {pid}")
    missing = sorted(known - scored)
    if missing:
        print(f"  {len(missing)} page(s) of the dataset carry no score at all")

    present = [f.name for f in rubric_features(fd) if f.name in sheet.columns]
    absent = [f.name for f in rubric_features(fd) if f.name not in sheet.columns]
    if absent:
        print(f"  judged columns missing from the sheet: {', '.join(absent)}")
    for name in present:
        filled = sheet[name].notna().sum()
        if filled < len(sheet):
            print(f"      {name}: {filled}/{len(sheet)} filled")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    emit = sub.add_parser("emit", help="write an empty scoring sheet")
    emit.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    emit.add_argument("--outdir", type=Path, default=DEFAULT_DIR)
    emit.add_argument("--rater", default="siegried")
    emit.add_argument("--include-unusable", action="store_true",
                      help="also emit rows whose capture is unusable")

    merge = sub.add_parser("merge", help="fold the completed sheet into the dataset")
    merge.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    merge.add_argument("--sheet", type=Path, required=True)
    merge.add_argument("--out", type=Path, default=Path("data/processed/campaigns_scored.csv"))

    args = parser.parse_args()
    fd = load_dictionary()

    if args.command == "emit":
        df, report = read_dataset(args.dataset, fd, tier="core", strict=False)
        print(report.render())
        args.outdir.mkdir(parents=True, exist_ok=True)

        sheet = make_sheet(df, fd, rater=args.rater, skip_unusable=not args.include_unusable)
        path = args.outdir / f"{args.rater}_scores.csv"
        sheet.to_csv(path, index=False)
        print(f"  {len(sheet)} page(s) to score -> {path}")

        guide = args.outdir / "SCORING_GUIDE.md"
        guide.write_text(sheet_guide(fd), encoding="utf-8")
        print(f"  guide -> {guide}")
        print("\nLeave a cell blank rather than guessing - a missing score is reported "
              "honestly, an invented one is not.")
        return 0

    sheets = read_sheets([args.sheet])
    df, _ = read_dataset(args.dataset, fd, tier="core", strict=False)

    print(f"Merging {args.sheet}")
    _coverage(sheets[0], df, fd)

    merged = merge_scores(df, sheets, fd)
    write_dataset(merged, args.out, fd)
    print(f"\nwrote {args.out}\n")
    print(validate(merged, fd, tier="core").render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
