"""Shared pytrends network policy: strict sequential calls, a fixed pause
after each success, exponential backoff with jitter on failure.

Lives in its own module so trends_collector.py and term_resolver.py throttle
exactly the same way.
"""

import logging
import random
import time

log = logging.getLogger(__name__)

MIN_DELAY_SECONDS = 60
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 30


def _with_retry(call, what):
    """Run call() until it succeeds, backing off exponentially with jitter.

    Gives up and re-raises after MAX_RETRIES retries. what only labels the
    log lines.
    """
    attempt = 0
    backoff = INITIAL_BACKOFF_SECONDS
    while True:
        try:
            return call()
        except Exception as exc:
            attempt += 1
            if attempt > MAX_RETRIES:
                log.error("Giving up on %s after %d attempts: %s", what, attempt - 1, exc)
                raise
            wait = backoff + random.uniform(0, backoff * 0.3)
            log.warning(
                "Request failed for %s (attempt %d/%d): %s. Retrying in %.1fs.",
                what, attempt, MAX_RETRIES, exc, wait,
            )
            time.sleep(wait)
            backoff *= 2


def fetch_with_retry(pytrends, kw_list, timeframe, geo):
    def call():
        pytrends.build_payload(kw_list, cat=0, timeframe=timeframe, geo=geo, gprop="")
        return pytrends.interest_over_time()

    return _with_retry(call, kw_list)


def suggestions_with_retry(pytrends, keyword):
    return _with_retry(lambda: pytrends.suggestions(keyword=keyword), f"suggestions({keyword!r})")


def pause_between_calls():
    time.sleep(MIN_DELAY_SECONDS)
