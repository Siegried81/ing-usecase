"""Tests for the standalone Semantic Scholar lookup.

Not wired into the pipeline - see comparator/research.py's module docstring.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import research  # noqa: E402


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_search_papers_parses_the_expected_fields():
    payload = {"data": [{"title": "Cross-selling in retail banking", "abstract": "...", "url": "https://x", "year": 2021}]}
    with patch("comparator.research.requests.get", return_value=_FakeResponse(payload)):
        papers = research.search_papers("cross-selling banking")
    assert papers == [{"title": "Cross-selling in retail banking", "abstract": "...", "url": "https://x", "year": 2021}]


def test_search_papers_returns_empty_list_on_request_failure():
    with patch("comparator.research.requests.get", side_effect=requests.RequestException("boom")):
        assert research.search_papers("anything") == []


def test_search_papers_works_without_an_api_key(monkeypatch):
    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)
    with patch("comparator.research.requests.get", return_value=_FakeResponse({"data": []})) as mock_get:
        assert research.search_papers("anything") == []
    assert "headers" in mock_get.call_args.kwargs
    assert mock_get.call_args.kwargs["headers"] == {}
