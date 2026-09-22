"""Stock price context for the few in-scope banks that are actually listed.

New module - deliberately thin. The brief's own assessment of
Finnhub for this project: "Principalement utile pour actualités financières,
résultats, fondamentaux. Peut servir si l'on souhaite mesurer l'impact
boursier de certaines campagnes." Most banks in this project's scope have NO
public ticker at all: Belfius (Belgian-State-owned), Argenta and Crelan are
not listed, and Revolut/N26/bunq are private fintechs. Only ING (via its
listed parent ING Groep), KBC Group and BNP Paribas (BNP Paribas Fortis's
listed parent) have one - so a stock-impact analysis here would cover 3 of 9
banks at best.

Given that coverage gap, this stays a standalone lookup - one function, gated
by `FINNHUB_API_KEY`, returning None for anything unmapped or unavailable -
rather than a pipeline step or a report.json/UI section built around mostly-
empty data. See docs/decisions.md (19/09) for the full reasoning.

TICKERS below are a best-effort mapping, unverified against Finnhub's own
symbol list - check before relying on it for anything real (same "unverified,
check before trusting" caveat this repo's llm_extractor.py already carries for
its own default model names).
"""

from __future__ import annotations

import os

import requests

FINNHUB_URL = "https://finnhub.io/api/v1/stock/candle"

TICKERS = {
    "ing": "INGA.AS",
    "kbc": "KBC.BR",
    "bnp_paribas_fortis": "BNP.PA",  # BNP Paribas SA, the listed parent
}


def daily_closes(bank: str, *, api_key: str | None = None, resolution: str = "D",
                  from_ts: int | None = None, to_ts: int | None = None,
                  timeout: int = 20) -> list[float] | None:
    """Daily close prices for `bank`, most recent last.

    None when the bank has no known ticker, FINNHUB_API_KEY is not set, or the
    request fails - never a fabricated series.
    """
    ticker = TICKERS.get(bank)
    if ticker is None:
        return None
    api_key = api_key or os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return None
    import time
    to_ts = to_ts if to_ts is not None else int(time.time())
    from_ts = from_ts if from_ts is not None else to_ts - 30 * 24 * 3600

    try:
        response = requests.get(
            FINNHUB_URL,
            params={"symbol": ticker, "resolution": resolution, "from": from_ts, "to": to_ts, "token": api_key},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return None
    if payload.get("s") != "ok":
        return None
    return list(payload.get("c", []))
