"""Legal/compliance gate for collection.

PRD: LC-01, LC-02, LC-04. The schema's own validator (schema.validate) already
hard-fails any row with robots_allowed=False, so this module's job is to make
sure that check happens BEFORE a fetch, not to catch it after the fact.

Fails closed: if robots.txt can't be read at all, the URL is treated as NOT
allowed rather than assumed fine.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

USER_AGENT = "BeCode-ING-CampaignComparator/0.2 (student POC, contact: team)"
ROBOTS_TIMEOUT_S = 15

# One robots.txt per domain per process. We check before every page AND before
# every hero-image fetch, so without this a six-page run re-downloads the same
# file a dozen times - rude to the sites we are asking permission from (LC-05).
_CACHE: dict[str, "ComplianceCheck | RobotFileParser | None"] = {}


@dataclass
class ComplianceCheck:
    url: str
    allowed: bool
    reason: str


class ScrapingNotAllowed(Exception):
    """Raised when robots.txt disallows fetching a URL. Never bypassed."""


def _robots_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def _fetch_robots(robots_url: str) -> RobotFileParser:
    """Read robots.txt with the SAME HTTP stack that will fetch the page.

    RobotFileParser.read() uses urllib, which on a stock macOS Python has no CA
    bundle: every HTTPS robots.txt raises CERTIFICATE_VERIFY_FAILED, the gate
    fails closed as designed, and every target is skipped - while the pages
    themselves stay perfectly fetchable, because scraper.py uses requests,
    which ships certifi.

    That makes the gate refuse permission it could in fact obtain, which is
    worse than a false negative: a team hitting it concludes the sites block
    us, when nothing of the sort is true. Using one stack for both means "we
    can read the rules" and "we can fetch the page" can no longer disagree.

    Status handling follows RobotFileParser.read()'s own semantics, so behaviour
    is unchanged from the standard library where it worked:
      401 / 403          -> treat the whole site as disallowed
      other 4xx (404...) -> no robots.txt published, nothing is disallowed
      2xx                -> parse it
      5xx / network fail -> raise, and the caller fails closed
    """
    parser = RobotFileParser()
    parser.set_url(robots_url)

    response = requests.get(
        robots_url, headers={"User-Agent": USER_AGENT}, timeout=ROBOTS_TIMEOUT_S
    )
    if response.status_code in (401, 403):
        parser.disallow_all = True
    elif 400 <= response.status_code < 500:
        parser.allow_all = True
    else:
        response.raise_for_status()
        parser.parse(response.text.splitlines())
    return parser


def check_robots(url: str, *, use_cache: bool = True) -> ComplianceCheck:
    robots_url = _robots_url(url)

    cached = _CACHE.get(robots_url) if use_cache else None
    if cached is None:
        try:
            cached = _fetch_robots(robots_url)
        except Exception as exc:  # noqa: BLE001 - any failure to read -> fail closed
            return ComplianceCheck(url, allowed=False, reason=f"could not read {robots_url}: {exc}")
        if use_cache:
            _CACHE[robots_url] = cached

    allowed = cached.can_fetch(USER_AGENT, url)
    reason = "allowed by robots.txt" if allowed else f"disallowed by {robots_url}"
    return ComplianceCheck(url, allowed=allowed, reason=reason)


def clear_cache() -> None:
    """Drop the per-process robots.txt cache. For tests and long-running jobs."""
    _CACHE.clear()


def assert_can_fetch(url: str) -> None:
    result = check_robots(url)
    if not result.allowed:
        raise ScrapingNotAllowed(f"{url}: {result.reason}")
