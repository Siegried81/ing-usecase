"""Shared pytrends network policy: strict sequential calls, fixed pause
after each success, exponential backoff with jitter on failure.

Extracted from trends_collector.py so collectors/term_resolver.py can reuse
the exact same throttling behavior without duplicating it. Values and
control flow are unchanged from the original collector.
"""

import logging
import random
import time

log = logging.getLogger(__name__)

MIN_DELAY_SECONDS = 60
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 30


def fetch_with_retry(pytrends, kw_list, timeframe, geo):
    attempt = 0
    backoff = INITIAL_BACKOFF_SECONDS
    while True:
        try:
            pytrends.build_payload(kw_list, cat=0, timeframe=timeframe, geo=geo, gprop="")
            return pytrends.interest_over_time()
        except Exception as exc:
            attempt += 1
            if attempt > MAX_RETRIES:
                log.error("Giving up on %s after %d attempts: %s", kw_list, attempt - 1, exc)
                raise
            jitter = random.uniform(0, backoff * 0.3)
            wait = backoff + jitter
            log.warning(
                "Request failed for %s (attempt %d/%d): %s. Retrying in %.1fs.",
                kw_list, attempt, MAX_RETRIES, exc, wait,
            )
            time.sleep(wait)
            backoff *= 2


def suggestions_with_retry(pytrends, keyword):
    attempt = 0
    backoff = INITIAL_BACKOFF_SECONDS
    while True:
        try:
            return pytrends.suggestions(keyword=keyword)
        except Exception as exc:
            attempt += 1
            if attempt > MAX_RETRIES:
                log.error("Giving up on suggestions(%r) after %d attempts: %s", keyword, attempt - 1, exc)
                raise
            jitter = random.uniform(0, backoff * 0.3)
            wait = backoff + jitter
            log.warning(
                "suggestions(%r) failed (attempt %d/%d): %s. Retrying in %.1fs.",
                keyword, attempt, MAX_RETRIES, exc, wait,
            )
            time.sleep(wait)
            backoff *= 2


def pause_between_calls():
    time.sleep(MIN_DELAY_SECONDS)
