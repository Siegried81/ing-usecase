#!/usr/bin/env python3
"""Fail the build when the dataset's data quality drops below threshold.

    python3 scripts/check_data_quality.py
    python3 scripts/check_data_quality.py --dataset data/processed/campaigns.csv

Scores the dataset on the standard DQ dimensions (comparator/dq.py) and exits
non-zero when a GATING dimension — completeness, validity or uniqueness — falls
under its threshold. Consistency and timeliness are reported but warn only: the
single-model fallback is a recorded limitation (NFR-02, D-09), not a regression
to block on. Accuracy is reported as not measurable here.

The companion to check_schema_freeze.py: freeze says "the contract did not
change in a breaking way", this says "the data still meets the contract".
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from comparator.dq import score_dataset

DEFAULT_DATASET = Path("data/processed/campaigns_scored.csv")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--tier", default="core")
    args = parser.parse_args()

    report = score_dataset(args.dataset, tier=args.tier)
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
