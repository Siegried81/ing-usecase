#!/usr/bin/env python3
"""Check the working feature dictionary against the frozen one.

    python3 scripts/check_schema_freeze.py

Exits non-zero on a breaking change. Additions are reported and allowed - that
is the rule the plan states (section 3.2), not "nothing may change".
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from comparator.dictionary import DEFAULT_DICTIONARY
from comparator.freeze import DEFAULT_FROZEN, check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--frozen", type=Path, default=DEFAULT_FROZEN)
    args = parser.parse_args()

    report = check(args.current, args.frozen)
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
