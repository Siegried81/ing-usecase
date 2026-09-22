"""Tests for the standalone geographic-interest module.

pytrends is deliberately not in requirements.txt (see the module docstring),
so CI does not install it - tests that need to mock it skip cleanly instead
of failing when it is absent, same as any other optional dependency in this
project's test suite would.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import geo_trends  # noqa: E402

pytest.importorskip("pytrends", reason="pytrends is an optional dependency, see requirements-geo.txt")


def _fake_pytrends(region_df: pd.DataFrame) -> MagicMock:
    instance = MagicMock()
    instance.interest_by_region.return_value = region_df
    return instance


def test_fetch_region_interest_returns_the_regional_breakdown():
    region_df = pd.DataFrame({"ING": [100, 83, 98]}, index=["Bruxelles", "Région Flamande", "Wallonie"])
    with patch("pytrends.request.TrendReq", return_value=_fake_pytrends(region_df)):
        result = geo_trends.fetch_region_interest("ING")
    assert result is not None
    assert result["ING"]["Bruxelles"] == 100


def test_fetch_region_interest_is_none_on_any_failure():
    with patch("pytrends.request.TrendReq", side_effect=Exception("rate limited")):
        assert geo_trends.fetch_region_interest("ING") is None


def test_fetch_region_interest_is_none_on_an_empty_result():
    with patch("pytrends.request.TrendReq", return_value=_fake_pytrends(pd.DataFrame())):
        assert geo_trends.fetch_region_interest("ING") is None


def test_build_geo_dashboard_covers_every_bank_and_pauses_between_calls():
    region_df = pd.DataFrame({"ING": [100, 83, 98]}, index=["Bruxelles", "Région Flamande", "Wallonie"])
    with patch("pytrends.request.TrendReq", return_value=_fake_pytrends(region_df)):
        with patch("comparator.geo_trends.time.sleep") as mock_sleep:
            results = geo_trends.build_geo_dashboard({"ing": "ING", "kbc": "KBC"}, pause_s=1.5)
    assert set(results) == {"ing", "kbc"}
    assert results["ing"]["Bruxelles"] == 100
    mock_sleep.assert_called_once_with(1.5)  # once between 2 banks, none before the first
