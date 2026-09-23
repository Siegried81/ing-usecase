#!/usr/bin/env python3
"""Write the synthetic fixture dataset.

    python3 scripts/make_fixture.py

Unblocks analysis work before the scraper exists (Project Plan, Day 2). Replaced
by the real rows - never merged with them.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from comparator.dictionary import load_dictionary
from comparator.fixtures import build_fixture
from comparator.schema import validate, write_dataset

DEFAULT_OUT = Path("data/fixtures/synthetic_sample.csv")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pages-per-bank", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260914)
    args = parser.parse_args()

    fd = load_dictionary()
    df = build_fixture(fd, pages_per_bank=args.pages_per_bank, seed=args.seed)

    report = validate(df, fd, tier="core")
    print(report.render())
    report.raise_if_failed()

    path = write_dataset(df, args.out, fd)
    print(f"\nwrote {len(df)} synthetic rows x {len(df.columns)} columns -> {path}")
    print("REMINDER: every value in this file is invented. Results from it are not findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
