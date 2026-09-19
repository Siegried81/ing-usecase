#!/usr/bin/env python3
"""Google Trends regional breakdown (Brussels/Flanders/Wallonia) per bank.

sieg 20/09, new script - regional Google Trends breakdown (see
comparator/geo_trends.py docstring for the full picture). Requires pytrends:
pip install -r requirements-geo.txt

    python3 scripts/geo_trends.py
"""

from __future__ import annotations

import json
from pathlib import Path

import _bootstrap  # noqa: F401

from comparator.geo_trends import build_geo_dashboard

DEFAULT_OUT = Path("outputs/geo_trends.json")


def main() -> int:
    results = build_geo_dashboard()
    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    for bank, regions in results.items():
        rendered = ", ".join(f"{r}={v}" for r, v in regions.items()) if regions else "no data (rate-limited, no pytrends, or no signal)"
        print(f"  {bank:<20} {rendered}")
    print(f"\nwrote {DEFAULT_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
