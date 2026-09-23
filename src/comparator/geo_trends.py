"""Google Trends geographic breakdown, by Belgian region.

The kickoff brief's "intérêt géographique" (geographic
interest) axis was never built: the existing Google Trends work pulls search
interest for geo=BE as a whole and never breaks it down by region, so there is
no view of whether a bank's search interest concentrates in Brussels, Flanders
or Wallonia. This makes its own pytrends calls directly, alongside the
existing Trends work, to cover that gap.

WHY A SEPARATE REQUIREMENTS FILE, NOT requirements.txt: pytrends is an
unofficial, rate-limited Google Trends client this project has deliberately
kept out of the main pipeline's pinned dependencies (see requirements.txt,
Note, for the same reasoning applied to the existing Trends work).
See requirements-geo.txt; CI does not install it, so every test here either
mocks pytrends or skips when it is not installed.

Degrades gracefully like every other optional data source in this project
(reputation.py, market_context.py): a rate limit, timeout or missing pytrends
install never crashes the run, and returns None rather than a fabricated
number. pytrends is also unofficial and rate-limits aggressively when hit
back to back, hence the pause between banks in build_geo_dashboard().
"""

from __future__ import annotations

import time

import pandas as pd

BANK_DISPLAY_NAMES: dict[str, str] = {
    "ing": "ING", "kbc": "KBC", "bnp_paribas_fortis": "BNP Paribas Fortis",
    "argenta": "Argenta", "crelan": "Crelan", "belfius": "Belfius",
    "revolut": "Revolut", "n26": "N26", "bunq": "bunq",
}


def fetch_region_interest(
    query: str, *, geo: str = "BE", timeframe: str = "today 12-m", timeout: int = 20
) -> pd.DataFrame | None:
    """Search interest for `query`, broken down by Belgian region (Brussels/
    Flanders/Wallonia). None when pytrends is not installed or the call fails
    for any reason (rate limit, timeout, no signal) - never a fabricated 0.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return None
    try:
        pytrends = TrendReq(hl="fr-BE", tz=60, timeout=(timeout, timeout))
        pytrends.build_payload([query], cat=0, timeframe=timeframe, geo=geo, gprop="")
        region = pytrends.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=False)
    except Exception:  # noqa: BLE001 - pytrends raises several undocumented exception types
        return None
    if region is None or region.empty or query not in region.columns:
        return None
    return region


def build_geo_dashboard(
    banks: dict[str, str] | None = None, *, pause_s: float = 1.5
) -> dict[str, dict[str, int] | None]:
    """Regional interest per bank, keyed by bank. `pause_s` spaces requests out -
    pytrends is unofficial and starts rate-limiting after only a few rapid calls.
    """
    banks = banks or BANK_DISPLAY_NAMES
    results: dict[str, dict[str, int] | None] = {}
    for i, (key, name) in enumerate(banks.items()):
        if i > 0:
            time.sleep(pause_s)
        region = fetch_region_interest(name)
        results[key] = region[name].to_dict() if region is not None else None
    return results
