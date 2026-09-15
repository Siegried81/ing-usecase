"""Legal/compliance gate for collection - sieg 14/09, new module.

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

USER_AGENT = "BeCode-ING-CampaignComparator/0.2 (student POC, contact: team)"


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


def check_robots(url: str) -> ComplianceCheck:
    robots_url = _robots_url(url)
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception as exc:  # noqa: BLE001 - any failure to read -> fail closed
        return ComplianceCheck(url, allowed=False, reason=f"could not read {robots_url}: {exc}")

    allowed = parser.can_fetch(USER_AGENT, url)
    reason = "allowed by robots.txt" if allowed else f"disallowed by {robots_url}"
    return ComplianceCheck(url, allowed=allowed, reason=reason)


def assert_can_fetch(url: str) -> None:
    result = check_robots(url)
    if not result.allowed:
        raise ScrapingNotAllowed(f"{url}: {result.reason}")
