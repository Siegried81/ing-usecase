"""Capture quality gate - is this row a campaign page, or an accident?

steph 16/09, new module. Written immediately after the first real collection
run, because the first real collection run produced two rows that were worse
than useless and nothing anywhere noticed:

  ing                 16 words, 0 images, 0 CTAs, page 5730px tall
                      -> captured text was the <title> twice. A JavaScript
                         shell that never rendered its content.

  bnp_paribas_fortis  87 words, page 925px tall
                      -> "Oops! The website is now unavailable. We are
                         currently doing maintenance work."

Both passed collection, both passed every numeric range in the schema, and both
would have gone straight into the comparison. The consequence is not a slightly
noisy average: ING is the bank the entire project exists to position, and it
would have been characterised as the most minimal communicator in the market on
the strength of an empty page. BNP would have been characterised from a
maintenance notice.

A validator that checks a number is in range cannot catch this. The values ARE
in range - they are honestly measured properties of a page that isn't the page
we meant to collect. So the check has to ask a different question: does this
look like a bank campaign page at all?

DELIBERATELY CONSERVATIVE. A short page is not automatically broken - a
challenger bank landing page really can carry 150 words. The thresholds below
flag for a human, and only the unambiguous cases (an explicit maintenance
notice, a page with essentially no text) are called unusable. Better to make
someone look at six rows than to silently drop a real one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# A real campaign page in any language clears this comfortably. Below it, the
# capture is almost always a shell, a consent wall, or an error page.
MIN_PLAUSIBLE_WORDS = 120
# Below this, there is no argument to have.
UNUSABLE_WORDS = 40

# An outage or error page, in the three languages in scope plus English.
ERROR_PHRASES = (
    "currently doing maintenance", "under maintenance", "site is now unavailable",
    "temporarily unavailable", "service temporarily", "page not found",
    "onderhoud", "tijdelijk niet beschikbaar", "pagina niet gevonden",
    "en maintenance", "temporairement indisponible", "page introuvable",
    "site est actuellement", "nous effectuons une maintenance",
)

# Consent walls are wordy in a recognisable way; used only as a hint, never alone.
CONSENT_PHRASES = (
    "accept all cookies", "accepter tous les cookies", "alle cookies accepteren",
    "manage your preferences", "gérer vos préférences", "cookiebeleid",
    "we use cookies", "nous utilisons des cookies",
)

OK, SUSPECT, UNUSABLE = "ok", "suspect", "unusable"


@dataclass
class QualityReport:
    verdict: str
    reasons: list[str] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        return self.verdict != UNUSABLE

    def note(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "looks like a campaign page"


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _title_only(page_text: str, meta_title: str | None) -> bool:
    """The ING case: the body text is nothing but the <title>, repeated."""
    body, title = _normalise(page_text), _normalise(meta_title or "")
    if not body or not title:
        return False
    return body.replace(title, "").strip(" -|–—") == ""


def assess_capture(row: dict, page_text: str = "") -> QualityReport:
    """Judge whether one collected row is a usable campaign page."""
    reasons: list[str] = []
    verdict = OK

    text = _normalise(page_text or row.get("_page_text", ""))
    words = row.get("word_count") or 0
    images = row.get("image_count") or 0
    ctas = row.get("cta_count") or 0
    height = row.get("page_height_px") or 0

    hit = next((p for p in ERROR_PHRASES if p in text), None)
    if hit:
        verdict = UNUSABLE
        reasons.append(f"error or maintenance page - matched {hit!r}")

    if _title_only(text, row.get("meta_title")):
        verdict = UNUSABLE
        reasons.append("body text is only the page title - content never rendered")

    if words < UNUSABLE_WORDS:
        verdict = UNUSABLE
        reasons.append(f"only {words} words - not a campaign page")
    elif words < MIN_PLAUSIBLE_WORDS:
        verdict = UNUSABLE if verdict == UNUSABLE else SUSPECT
        reasons.append(f"only {words} words, below the {MIN_PLAUSIBLE_WORDS}-word plausibility floor")

    # A tall page carrying almost nothing is the signature of a consent wall or
    # a shell: the layout rendered, the content did not.
    if height > 1500 and words < MIN_PLAUSIBLE_WORDS:
        verdict = UNUSABLE if verdict == UNUSABLE else SUSPECT
        reasons.append(f"page is {height}px tall but carries only {words} words - shell or consent wall")

    if images == 0 and ctas == 0:
        verdict = UNUSABLE if verdict == UNUSABLE else SUSPECT
        reasons.append("no images and no calls to action - unlikely to be a campaign page")

    if any(p in text for p in CONSENT_PHRASES) and words < MIN_PLAUSIBLE_WORDS:
        verdict = UNUSABLE if verdict == UNUSABLE else SUSPECT
        reasons.append("consent-banner wording dominates the captured text")

    return QualityReport(verdict=verdict, reasons=reasons)
