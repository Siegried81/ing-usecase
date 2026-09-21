"""Bank reputation signal via NewsAPI headlines - THEME counts, never sentiment.

sieg 19/09, new module. Optional (`NEWSAPI_KEY` for newsapi.org, and/or
`NEWSAPI_AI_KEY` for newsapi.ai / Event Registry): headlines from every
configured key are merged and de-duplicated, and the whole signal degrades to
unavailable when no key is set, same pattern `trends.py` already uses when
Dan's export is absent - this never invents a number for a bank there was no
data for.

WHY THEMES, NOT SENTIMENT: sentiment scoring was explicitly out of scope for
this pass. Themes turn "réputation, innovations, crises" (the brief's own
framing) into a closed, countable list - the same move `persuasion_levers`
already made for "persuasive" in the feature dictionary - rather than asking a
model to grade how positively a bank is covered, a different and harder to
defend claim this project does not need to make.

ONE structured LLM call per bank (a batch of headlines in, one classification
out) - same "single call, fixed prompt + schema, no agent" rule as
`collection/llm_extractor.py`.

sieg 21/09: `notable_headlines` now carries each headline's source URL
alongside its title, so the web UI can link out to the article. The URL is
looked up locally against what we actually fetched, never produced by the
model.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta

import requests
from pydantic import BaseModel, Field, ValidationError

from comparator.collection.llm_extractor import LLMExtractionError, _call_llm

# Two different companies share a confusingly similar name, and their keys are
# NOT interchangeable. Both may be configured at once; headlines are merged and
# de-duplicated, so one provider's outage or thin coverage does not blank a bank.
#   newsapi.org  - 32-hex key, GET /v2/everything, X-Api-Key header
#                  (NEWSAPI_KEY)
#   newsapi.ai   - UUID key (Event Registry), POST /api/v1/article/getArticles
#                  (NEWSAPI_AI_KEY)
NEWSAPI_URL = "https://newsapi.org/v2/everything"
NEWSAPI_AI_URL = "https://newsapi.ai/api/v1/article/getArticles"
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
# How far back a headline may be and still count as "what is being said now".
RECENT_DAYS = 90
# Belgian banking news is mostly not in English: measured on Event Registry,
# "Belfius" gave 0 English title matches against 22 French and 11 Dutch, and
# Crelan/Beobank only appeared in French or Dutch. Query every language the
# country actually publishes in, per provider's codes.
PROVIDER_LANGUAGES = {
    "newsapi.ai": ("eng", "fra", "nld"),
    "newsapi.org": ("en", "fr", "nl"),
}
# Bound on what one bank sends to the classifier, after de-duplication.
MAX_HEADLINES = 30


def _bank_token(bank_name: str) -> str:
    """The distinctive part of a bank name, used for both the query and the check.

    Querying the full name plus "bank" was measured returning nothing on Event
    Registry ("KBC" alone -> 24 title matches, "KBC bank" -> 0), so the token is
    the first word: ING, KBC, N26, BNP, ...
    """
    return (bank_name.split() or [bank_name])[0]


def _is_newsapi_ai_key(key: str) -> bool:
    return bool(_UUID.fullmatch(key.strip()))


def configured_sources() -> list[tuple[str, str]]:
    """Every (provider, key) pair present in the environment, in priority order."""
    sources: list[tuple[str, str]] = []
    primary = (os.getenv("NEWSAPI_KEY") or "").strip()
    second = (os.getenv("NEWSAPI_AI_KEY") or "").strip()
    if primary:
        # Tolerate a newsapi.ai key sitting in NEWSAPI_KEY, which is how it
        # briefly was configured before the second slot existed.
        sources.append(("newsapi.ai" if _is_newsapi_ai_key(primary) else "newsapi.org", primary))
    if second:
        sources.append(("newsapi.ai", second))
    return sources

THEMES = (
    "innovation_digital", "crisis_or_scandal", "financial_results",
    "product_launch", "esg_sustainability", "regulatory", "other",
)

SYSTEM_PROMPT = """You classify news headlines about a bank into topical themes - never
sentiment or opinion, only what each headline is ABOUT. Apply the same criteria to every
headline.

Return ONLY a JSON object with exactly these keys:
- "theme_counts": object mapping each of "innovation_digital", "crisis_or_scandal",
  "financial_results", "product_launch", "esg_sustainability", "regulatory", "other" to an
  integer count of how many of the given headlines belong to that theme (every headline
  counted exactly once, into its single best-fitting theme)
- "notable_headlines": array of up to 5 headline strings, taken verbatim from the input, that
  best illustrate why this bank is in the news right now, most important first

No preamble, no markdown fences, JSON only."""


class ReputationModel(BaseModel):
    theme_counts: dict[str, int] = Field(default_factory=dict)
    notable_headlines: list[str] = Field(default_factory=list)


def _fetch_for_language(provider: str, query: str, api_key: str, language: str,
                        page_size: int, timeout: int) -> list[dict]:
    """Title + source URL pairs for one provider in one language. Empty list on any failure.

    sieg 21/09: keep the URL alongside the title (both APIs already return it) so a
    notable headline can link back to its source - was title-only before, which left
    the web UI with no way to open the article.
    """
    try:
        if provider == "newsapi.ai":
            # Relevance, not date: Event Registry matches the whole article, so
            # "ING" sorted by date returned mostly stories that merely mention
            # it, while by relevance it returns the ones ABOUT ING (4 -> 17
            # title matches in a measured probe). dateStart keeps it recent.
            start = (date.today() - timedelta(days=RECENT_DAYS)).isoformat()
            response = requests.post(
                NEWSAPI_AI_URL,
                json={"action": "getArticles", "keyword": query, "lang": language,
                      "articlesCount": page_size, "articlesSortBy": "rel",
                      "dateStart": start,
                      "resultType": "articles", "apiKey": api_key},
                timeout=timeout,
            )
            response.raise_for_status()
            articles = response.json().get("articles", {}).get("results", [])
        else:
            # newsapi.org searches the whole article body by default, which
            # returned football and politics stories for the word "bank". Keep
            # the match in the title/description, where the bank is named.
            response = requests.get(
                NEWSAPI_URL,
                params={"q": query, "language": language, "sortBy": "publishedAt",
                        "pageSize": page_size, "searchIn": "title,description"},
                headers={"X-Api-Key": api_key},
                timeout=timeout,
            )
            response.raise_for_status()
            articles = response.json().get("articles", [])
    except (requests.RequestException, ValueError, AttributeError, TypeError):
        return []
    return [
        {"title": a["title"], "url": a.get("url")}
        for a in articles if isinstance(a, dict) and a.get("title")
    ]


def _fetch_from(provider: str, query: str, api_key: str, page_size: int, timeout: int) -> list[dict]:
    """Title/URL pairs from one provider, across every language it publishes in.

    One language failing (or hitting a rate limit) leaves the others intact, so
    a bank still gets whatever was returned rather than nothing.
    """
    headlines: list[dict] = []
    for language in PROVIDER_LANGUAGES[provider]:
        headlines.extend(_fetch_for_language(provider, query, api_key, language, page_size, timeout))
    return headlines


def fetch_headlines(query: str, api_key: str | None = None, *,
                    page_size: int = 20, timeout: int = 20) -> list[dict]:
    """Recent {"title", "url"} headlines mentioning `query`, merged across configured keys.

    Passing `api_key` pins the query to that one key (and picks the provider from
    the key's shape); leaving it out uses every key in the environment.
    """
    if api_key:
        provider = "newsapi.ai" if _is_newsapi_ai_key(api_key) else "newsapi.org"
        headlines = _fetch_from(provider, query, api_key, page_size, timeout)
    else:
        headlines = []
        for provider, key in configured_sources():
            headlines.extend(_fetch_from(provider, query, key, page_size, timeout))

    # De-duplicate across languages and across providers: the same story arrives
    # translated (fr + nl) and syndicated (both APIs), and counting it twice
    # would inflate one bank's themes against another's.
    seen: set[str] = set()
    merged: list[dict] = []
    for headline in headlines:
        marker = headline["title"].strip().lower()
        if marker and marker not in seen:
            seen.add(marker)
            merged.append(headline)
    return merged


def classify_headlines(headlines: list[str], bank_name: str) -> ReputationModel | None:
    """One structured call, themes only. None when there is nothing to classify, or the
    call/parse fails - never a fabricated all-zero classification."""
    if not headlines:
        return None
    prompt = f"Bank: {bank_name}\nHeadlines:\n" + "\n".join(f"- {h}" for h in headlines)
    try:
        raw, _model = _call_llm(prompt, system_prompt=SYSTEM_PROMPT, timeout=60)
    except LLMExtractionError:
        return None
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return ReputationModel.model_validate(json.loads(cleaned))
    except (json.JSONDecodeError, ValidationError):
        return None


def _mentions(headlines: list[dict], bank_name: str) -> list[dict]:
    """Keep only headlines where the bank's name appears as a whole word.

    steve 21/09: newsapi.ai's keyword search stems and matches substrings ("ING"
    matched "bruising"), which put unrelated politics stories in ING's batch and
    inflated its "other" count. A word-boundary check on the first name token is
    the cheapest honest fix; it runs on both providers so a month of counts is
    comparable regardless of which one is configured.
    """
    token = _bank_token(bank_name)
    # Not just \b: "f—ing", "f-ing" and "f***ing" all contain a word-boundary
    # "ing", and pulled swearing-heavy tabloid stories into ING's batch. Require
    # the character before the token to be neither a word character nor the
    # punctuation that glues a suffix onto one.
    pattern = re.compile(rf"(?<![\w\u2010-\u2015*'’\-])\b{re.escape(token)}\b", re.IGNORECASE)
    return [h for h in headlines if pattern.search(h["title"])]


def bank_snapshot(bank_name: str, *, api_key: str | None = None) -> dict | None:
    """None when NEWSAPI_KEY is absent, or nothing could be fetched/classified."""
    if not api_key and not configured_sources():
        return None
    matched = _mentions(fetch_headlines(f'"{_bank_token(bank_name)}"', api_key), bank_name)
    headlines = matched[:MAX_HEADLINES]
    titles = [h["title"] for h in headlines]
    classified = classify_headlines(titles, bank_name)
    if classified is None:
        return None
    # sieg 21/09: the model returns notable headlines verbatim (SYSTEM_PROMPT
    # requires it) - look each one up in what we actually fetched to attach its
    # real URL. Never let the model produce the URL itself: that is exactly the
    # kind of figure this project never lets a model invent.
    url_by_title = {h["title"]: h.get("url") for h in headlines}
    notable = [{"title": t, "url": url_by_title.get(t)} for t in classified.notable_headlines]
    return {
        "headline_count": len(headlines),
        "themes": {t: classified.theme_counts.get(t, 0) for t in THEMES},
        "notable_headlines": notable,
    }


def build_dashboard(banks: list[tuple[str, str]], *, api_key: str | None = None) -> dict:
    """`banks` is a list of (key, display_name). Always returns a dict - "available" says
    whether NEWSAPI_KEY was configured at all, so the UI can show an honest empty state
    instead of a report with every bank silently missing."""
    if not api_key and not configured_sources():
        return {"available": False, "banks": {}}
    return {
        "available": True,
        "banks": {key: bank_snapshot(name, api_key=api_key) for key, name in banks},
    }
