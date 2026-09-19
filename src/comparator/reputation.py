"""Bank reputation signal via NewsAPI headlines - THEME counts, never sentiment.

sieg 19/09, new module. Optional (`NEWSAPI_KEY`): degrades to unavailable when
the key is absent, same pattern `trends.py` already uses when Dan's export is
absent - this never invents a number for a bank there was no data for.

WHY THEMES, NOT SENTIMENT: sentiment scoring was explicitly out of scope for
this pass. Themes turn "réputation, innovations, crises" (the brief's own
framing) into a closed, countable list - the same move `persuasion_levers`
already made for "persuasive" in the feature dictionary - rather than asking a
model to grade how positively a bank is covered, a different and harder to
defend claim this project does not need to make.

ONE structured LLM call per bank (a batch of headlines in, one classification
out) - same "single call, fixed prompt + schema, no agent" rule as
`collection/llm_extractor.py`.
"""

from __future__ import annotations

import json
import os

import requests
from pydantic import BaseModel, Field, ValidationError

from comparator.collection.llm_extractor import LLMExtractionError, _call_llm

NEWSAPI_URL = "https://newsapi.org/v2/everything"

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
- "notable_headlines": array of up to 3 headline strings, taken verbatim from the input, that
  best illustrate why this bank is in the news right now

No preamble, no markdown fences, JSON only."""


class ReputationModel(BaseModel):
    theme_counts: dict[str, int] = Field(default_factory=dict)
    notable_headlines: list[str] = Field(default_factory=list)


def fetch_headlines(query: str, api_key: str, *, page_size: int = 20, timeout: int = 20) -> list[str]:
    """Recent headline titles mentioning `query`.

    Empty list on any failure - never raises. A news-API outage is a missing
    signal, not a reason to fail the whole report export.
    """
    try:
        response = requests.get(
            NEWSAPI_URL,
            params={"q": query, "language": "en", "sortBy": "publishedAt", "pageSize": page_size},
            headers={"X-Api-Key": api_key},
            timeout=timeout,
        )
        response.raise_for_status()
        articles = response.json().get("articles", [])
    except requests.RequestException:
        return []
    return [a["title"] for a in articles if a.get("title")]


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


def bank_snapshot(bank_name: str, *, api_key: str | None = None) -> dict | None:
    """None when NEWSAPI_KEY is absent, or nothing could be fetched/classified."""
    api_key = api_key or os.getenv("NEWSAPI_KEY")
    if not api_key:
        return None
    headlines = fetch_headlines(f'"{bank_name}" bank', api_key)
    classified = classify_headlines(headlines, bank_name)
    if classified is None:
        return None
    return {
        "headline_count": len(headlines),
        "themes": {t: classified.theme_counts.get(t, 0) for t in THEMES},
        "notable_headlines": classified.notable_headlines,
    }


def build_dashboard(banks: list[tuple[str, str]], *, api_key: str | None = None) -> dict:
    """`banks` is a list of (key, display_name). Always returns a dict - "available" says
    whether NEWSAPI_KEY was configured at all, so the UI can show an honest empty state
    instead of a report with every bank silently missing."""
    api_key = api_key or os.getenv("NEWSAPI_KEY")
    if not api_key:
        return {"available": False, "banks": {}}
    return {
        "available": True,
        "banks": {key: bank_snapshot(name, api_key=api_key) for key, name in banks},
    }
