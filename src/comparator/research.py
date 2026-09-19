"""Academic paper search - a standalone utility, not a pipeline step.

sieg 19/09, new module. The brief itself calls Semantic Scholar "Optionnel"
and names no concrete per-bank metric to compute from it (unlike personas,
cross-sell, or news themes, which all have a defined output shape). Building
a report.json/UI section around "articles that exist" with no metric would be
inventing scope nobody asked for - so this stays exactly what it is: a small
lookup for whoever is writing the business narrative to pull supporting
references (e.g. "cross-selling bancaire", "comportement client") on demand.

No API key is required for Semantic Scholar's public Graph API at low volume;
SEMANTIC_SCHOLAR_API_KEY only raises the rate limit, so this degrades to
"works anyway, just slower" rather than "unavailable" when unset.
"""

from __future__ import annotations

import os

import requests

SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_papers(query: str, *, limit: int = 5, api_key: str | None = None, timeout: int = 20) -> list[dict]:
    """Up to `limit` papers matching `query` - title, abstract, url, year.

    Empty list on any failure - never raises. This is a research convenience,
    not something the pipeline depends on.
    """
    api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {"x-api-key": api_key} if api_key else {}
    try:
        response = requests.get(
            SEMANTIC_SCHOLAR_URL,
            params={"query": query, "limit": limit, "fields": "title,abstract,url,year"},
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        papers = response.json().get("data", [])
    except requests.RequestException:
        return []
    return [
        {"title": p.get("title"), "abstract": p.get("abstract"), "url": p.get("url"), "year": p.get("year")}
        for p in papers
    ]
