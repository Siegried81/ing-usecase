"""Tests for the NewsAPI reputation signal (sieg 19/09).

All network calls are mocked - requests.get for NewsAPI, _call_llm for the
single theme-classification call - per this repo's rule against real HTTP in
tests.

sieg 21/09: fetch_headlines/_mentions now carry {"title", "url"} pairs instead
of bare title strings, so a notable headline can link back to its source -
tests updated for the new shape, plus new coverage for the title->url lookup.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import reputation  # noqa: E402


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_headlines_extracts_titles_and_urls():
    with patch("comparator.reputation.requests.get", return_value=_FakeResponse(
        {"articles": [
            {"title": "ING launches new app", "url": "https://news.example/1"},
            {"title": "ING reports Q3 results", "url": "https://news.example/2"},
        ]}
    )):
        headlines = reputation.fetch_headlines("ING bank", "fake-key")
    assert headlines == [
        {"title": "ING launches new app", "url": "https://news.example/1"},
        {"title": "ING reports Q3 results", "url": "https://news.example/2"},
    ]


def test_fetch_headlines_keeps_the_first_url_seen_when_deduplicating():
    # sieg 21/09: the same story arrives translated/syndicated - dedup by
    # title (case/whitespace-insensitive) must not drop the URL that came
    # with the first occurrence.
    with patch("comparator.reputation.requests.get", return_value=_FakeResponse(
        {"articles": [
            {"title": "ING launches new app", "url": "https://news.example/first"},
            {"title": "  ing launches new app  ", "url": "https://news.example/dupe"},
        ]}
    )):
        headlines = reputation.fetch_headlines("ING bank", "fake-key")
    assert headlines == [{"title": "ING launches new app", "url": "https://news.example/first"}]


def test_fetch_headlines_returns_empty_list_on_request_failure():
    with patch("comparator.reputation.requests.get", side_effect=requests.RequestException("boom")):
        assert reputation.fetch_headlines("ING bank", "fake-key") == []


def test_classify_headlines_returns_none_for_an_empty_list():
    assert reputation.classify_headlines([], "ING") is None


def test_classify_headlines_parses_a_valid_response():
    payload = '{"theme_counts": {"innovation_digital": 2, "crisis_or_scandal": 0}, "notable_headlines": ["ING launches new app"]}'
    with patch("comparator.reputation._call_llm", return_value=(payload, "test/model")):
        result = reputation.classify_headlines(["ING launches new app"], "ING")
    assert result is not None
    assert result.theme_counts["innovation_digital"] == 2
    assert result.notable_headlines == ["ING launches new app"]


def test_classify_headlines_returns_none_on_bad_json():
    with patch("comparator.reputation._call_llm", return_value=("not json", "test/model")):
        assert reputation.classify_headlines(["ING launches new app"], "ING") is None


def test_bank_snapshot_is_none_without_an_api_key(monkeypatch):
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    monkeypatch.delenv("NEWSAPI_AI_KEY", raising=False)
    assert reputation.bank_snapshot("ING") is None


def test_bank_snapshot_fills_every_theme_even_when_the_model_only_named_some():
    with patch("comparator.reputation.fetch_headlines",
               return_value=[{"title": "ING launches new app", "url": "https://news.example/1"}]):
        with patch("comparator.reputation.classify_headlines", return_value=reputation.ReputationModel(
            theme_counts={"innovation_digital": 1}, notable_headlines=["ING launches new app"],
        )):
            snapshot = reputation.bank_snapshot("ING", api_key="fake-key")
    assert snapshot["headline_count"] == 1
    assert set(snapshot["themes"]) == set(reputation.THEMES)
    assert snapshot["themes"]["innovation_digital"] == 1
    assert snapshot["themes"]["crisis_or_scandal"] == 0


def test_bank_snapshot_attaches_the_source_url_to_each_notable_headline():
    # sieg 21/09: the URL is looked up locally against what was fetched, never
    # produced by the model.
    with patch("comparator.reputation.fetch_headlines",
               return_value=[{"title": "ING launches new app", "url": "https://news.example/1"}]):
        with patch("comparator.reputation.classify_headlines", return_value=reputation.ReputationModel(
            theme_counts={}, notable_headlines=["ING launches new app"],
        )):
            snapshot = reputation.bank_snapshot("ING", api_key="fake-key")
    assert snapshot["notable_headlines"] == [
        {"title": "ING launches new app", "url": "https://news.example/1"}
    ]


def test_bank_snapshot_gives_a_null_url_when_the_model_did_not_copy_verbatim():
    # The model is instructed to copy headlines verbatim, but is never trusted
    # to - a near-miss must not invent or drop the headline, just its link.
    with patch("comparator.reputation.fetch_headlines",
               return_value=[{"title": "ING launches new app", "url": "https://news.example/1"}]):
        with patch("comparator.reputation.classify_headlines", return_value=reputation.ReputationModel(
            theme_counts={}, notable_headlines=["ing launches a new app"],
        )):
            snapshot = reputation.bank_snapshot("ING", api_key="fake-key")
    assert snapshot["notable_headlines"] == [{"title": "ing launches a new app", "url": None}]


def test_build_dashboard_is_unavailable_without_a_key(monkeypatch):
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    monkeypatch.delenv("NEWSAPI_AI_KEY", raising=False)
    dashboard = reputation.build_dashboard([("ing", "ING")])
    assert dashboard == {"available": False, "banks": {}}


def test_build_dashboard_covers_every_bank_when_a_key_is_present():
    with patch("comparator.reputation.bank_snapshot", return_value={"headline_count": 0, "themes": {}, "notable_headlines": []}):
        dashboard = reputation.build_dashboard([("ing", "ING"), ("kbc", "KBC")], api_key="fake-key")
    assert dashboard["available"] is True
    assert set(dashboard["banks"]) == {"ing", "kbc"}
