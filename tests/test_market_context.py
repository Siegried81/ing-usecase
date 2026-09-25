"""Tests for the thin, standalone Finnhub lookup.

See comparator/market_context.py's module docstring for why this stays a
single function rather than a pipeline step - most banks in scope aren't
publicly listed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import market_context  # noqa: E402


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_unknown_bank_returns_none_without_any_request(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "fake-key")
    with patch("comparator.market_context.requests.get") as mock_get:
        assert market_context.daily_closes("revolut") is None
    mock_get.assert_not_called()


def test_none_without_an_api_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    assert market_context.daily_closes("ing") is None


def test_returns_the_close_series_on_a_successful_response():
    with patch("comparator.market_context.requests.get", return_value=_FakeResponse(
        {"s": "ok", "c": [10.1, 10.4, 10.2]}
    )):
        closes = market_context.daily_closes("ing", api_key="fake-key")
    assert closes == [10.1, 10.4, 10.2]


def test_none_when_finnhub_reports_no_data():
    with patch("comparator.market_context.requests.get", return_value=_FakeResponse({"s": "no_data"})):
        assert market_context.daily_closes("kbc", api_key="fake-key") is None


def test_none_on_request_failure():
    with patch("comparator.market_context.requests.get", side_effect=requests.RequestException("boom")):
        assert market_context.daily_closes("bnp_paribas_fortis", api_key="fake-key") is None
