"""Bank reputation signal via NewsAPI headlines - THEME counts, never sentiment.

New module. Optional (`NEWSAPI_KEY` for newsapi.org, and/or
`NEWSAPI_AI_KEY` for newsapi.ai / Event Registry): headlines from every
configured key are merged and de-duplicated, and the whole signal degrades to
unavailable when no key is set, same pattern `trends.py` already uses when
the export is absent - this never invents a number for a bank there was no
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

`notable_headlines` now carries each headline's source URL
alongside its title, so the web UI can link out to the article. The URL is
looked up locally against what we actually fetched, never produced by the
model.

Every fetched headline is now also checked against
`_is_belgian_source()` - language alone let through a Dutch accountancy
trade site (accountancyvanmorgen.nl) writing about "ING" that had nothing
to do with ING Belgium, because Dutch is spoken well beyond Belgium too.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

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

# Language alone cannot tell "about Belgium" from "published anywhere the
# language is spoken" - a Dutch accountancy trade site (accountancyvanmorgen.nl) matched
# lang=nl and inflated a bank's theme count with a story that was never about the
# Belgian entity. Neither provider's `getArticles`/`everything` response carries a
# reliable per-article country field to check instead (Event Registry has one, but only
# via a separate source-info lookup, not worth the extra call here), so this stays a
# domain check. newsapi.org's `domains` param narrows the fetch itself; this list plus
# _is_belgian_source() below is the second, provider-independent guard that actually
# decides what stays.
BELGIAN_NEWS_DOMAINS = (
    "rtbf.be,lesoir.be,lalibre.be,dhnet.be,sudinfo.be,7sur7.be,levif.be,lecho.be,"
    "bruzz.be,brusselstimes.com,hln.be,standaard.be,nieuwsblad.be,demorgen.be,"
    "vrt.be,tijd.be,knack.be,gva.be,hbvl.be,lavenir.net"
)
# Caught by the regression test below - lavenir.net (L'Avenir, a real
# Belgian regional paper) was wrongly dropped because it isn't a .be domain. The
# allowlist is for exactly this: known Belgian outlets on a non-.be TLD.
_BELGIAN_DOMAIN_ALLOWLIST = frozenset(BELGIAN_NEWS_DOMAINS.split(","))


def _is_belgian_source(url: str | None) -> bool:
    """A .be domain, or a known Belgian outlet that isn't (lavenir.net, brusselstimes.com).
    Never a language check - see module note above. Necessarily incomplete: a legitimate
    Belgian outlet on an unlisted non-.be domain would still be dropped."""
    if not url:
        return False
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host.endswith(".be") or host in _BELGIAN_DOMAIN_ALLOWLIST


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
- "theme_headlines": object mapping each of "innovation_digital", "crisis_or_scandal",
  "financial_results", "product_launch", "esg_sustainability", "regulatory", "other" to an
  array of the headline strings, taken verbatim from the input, that belong to that theme
  (every input headline appears in exactly one theme's array, its single best fit - an empty
  array for a theme with no headlines)
- "notable_headlines": array of up to 5 headline strings, taken verbatim from the input, that
  best illustrate why this bank is in the news right now, most important first

No preamble, no markdown fences, JSON only."""


class ReputationModel(BaseModel):
    # Was theme_counts (int only) - now the full per-theme headline list, so the
    # UI can show which articles a count is made of on hover, not just the number.
    theme_headlines: dict[str, list[str]] = Field(default_factory=dict)
    notable_headlines: list[str] = Field(default_factory=list)


def _fetch_for_language(provider: str, query: str, api_key: str, language: str,
                        page_size: int, timeout: int) -> list[dict]:
    """Title + source URL pairs for one provider in one language. Empty list on any failure.

    Keep the URL alongside the title (both APIs already return it) so a
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
            # `domains` narrows the fetch to Belgian outlets - see BELGIAN_NEWS_DOMAINS.
            response = requests.get(
                NEWSAPI_URL,
                params={"q": query, "language": language, "sortBy": "publishedAt",
                        "pageSize": page_size, "searchIn": "title,description",
                        "domains": BELGIAN_NEWS_DOMAINS},
                headers={"X-Api-Key": api_key},
                timeout=timeout,
            )
            response.raise_for_status()
            articles = response.json().get("articles", [])
    except requests.HTTPError as exc:
        # A failed request and a genuine zero-result response both return []
        # here, which bank_snapshot()'s caller cannot tell apart: a rejected
        # key or an exhausted quota would otherwise read as "this bank is not
        # in the news". Neither is cached (see the CACHE_PATH note below), but
        # the failure has to be visible rather than taken for a finding.
        status = exc.response.status_code if exc.response is not None else "?"
        print(f"  [WARNING] reputation fetch failed ({provider}, {language}, HTTP {status}) "
              f"for query {query!r} - treating as no data, NOT as zero headlines")
        return []
    except (requests.RequestException, ValueError, AttributeError, TypeError):
        return []
    # Newsapi.ai has no domain filter to narrow the fetch with, so this
    # second check is the one both providers actually rely on - see _is_belgian_source().
    return [
        {"title": a["title"], "url": a.get("url")}
        for a in articles
        if isinstance(a, dict) and a.get("title") and _is_belgian_source(a.get("url"))
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

    Newsapi.ai's keyword search stems and matches substrings ("ING"
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


# Newsapi.org's free tier is 100 requests/24h (50/12h) - re-running
# export_web_report.py a handful of times in one afternoon exhausted it, and every
# bank's signal silently thinned out (bank_snapshot degrades to None on a failed
# fetch, by design - see its docstring). A same-day cache means iterating on
# unrelated code (the UI, the prompt wording) doesn't re-spend quota that was
# already spent finding this run's headlines. Only a REAL snapshot is cached -
# never a None, because bank_snapshot returns None both when a bank genuinely has
# no matching headlines and when the fetch failed (rate limit, timeout, bad key);
# caching that would freeze a quota outage into a permanent "nothing found".
CACHE_PATH = Path("data/processed/reputation_cache.json")


def _load_cache() -> dict:
    if not CACHE_PATH.is_file():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def bank_snapshot(bank_name: str, *, api_key: str | None = None) -> dict | None:
    """None when NEWSAPI_KEY is absent, or nothing could be fetched/classified.

    Reuses today's cached snapshot for this bank when there is one - see the
    CACHE_PATH note above for why only a successful snapshot is ever cached.
    """
    if not api_key and not configured_sources():
        return None
    cache = _load_cache()
    today = date.today().isoformat()
    cached = cache.get(bank_name)
    if cached and cached.get("cached_on") == today:
        return cached["snapshot"]

    matched = _mentions(fetch_headlines(f'"{_bank_token(bank_name)}"', api_key), bank_name)
    headlines = matched[:MAX_HEADLINES]
    titles = [h["title"] for h in headlines]
    classified = classify_headlines(titles, bank_name)
    if classified is None:
        return None
    # The model returns notable headlines verbatim (SYSTEM_PROMPT
    # requires it) - look each one up in what we actually fetched to attach its
    # real URL. Never let the model produce the URL itself: that is exactly the
    # kind of figure this project never lets a model invent.
    url_by_title = {h["title"]: h.get("url") for h in headlines}
    notable = [{"title": t, "url": url_by_title.get(t)} for t in classified.notable_headlines]
    # Every headline under its theme, with its URL - lets the UI show, on
    # hover over a theme's count, the full list of articles that count is made of.
    theme_headlines = {
        t: [{"title": h, "url": url_by_title.get(h)} for h in classified.theme_headlines.get(t, [])]
        for t in THEMES
    }
    snapshot = {
        "headline_count": len(headlines),
        "themes": {t: len(theme_headlines[t]) for t in THEMES},
        "theme_headlines": theme_headlines,
        "notable_headlines": notable,
    }
    cache[bank_name] = {"cached_on": today, "snapshot": snapshot}
    _save_cache(cache)
    return snapshot


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
