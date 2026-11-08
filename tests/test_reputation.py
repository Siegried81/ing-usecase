"""Tests for the NewsAPI reputation signal.

All network calls are mocked - requests.get for NewsAPI, _call_llm for the
single theme-classification call - per this repo's rule against real HTTP in
tests.

Fetch_headlines/_mentions now carry {"title", "url"} pairs instead
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


@pytest.fixture(autouse=True)
def _isolated_cache(monkeypatch, tmp_path):
    """Bank_snapshot() now reads/writes a same-day cache file - point every
    test at a throwaway path so none of them touch the real data/processed/ cache."""
    monkeypatch.setattr(reputation, "CACHE_PATH", tmp_path / "reputation_cache.json")


def test_fetch_headlines_extracts_titles_and_urls():
    with patch("comparator.reputation.requests.get", return_value=_FakeResponse(
        {"articles": [
            {"title": "ING launches new app", "url": "https://www.lesoir.be/1"},
            {"title": "ING reports Q3 results", "url": "https://www.rtbf.be/2"},
        ]}
    )):
        headlines = reputation.fetch_headlines("ING bank", "fake-key")
    assert headlines == [
        {"title": "ING launches new app", "url": "https://www.lesoir.be/1"},
        {"title": "ING reports Q3 results", "url": "https://www.rtbf.be/2"},
    ]


def test_fetch_headlines_keeps_the_first_url_seen_when_deduplicating():
    # The same story arrives translated/syndicated - dedup by
    # title (case/whitespace-insensitive) must not drop the URL that came
    # with the first occurrence.
    with patch("comparator.reputation.requests.get", return_value=_FakeResponse(
        {"articles": [
            {"title": "ING launches new app", "url": "https://www.lesoir.be/first"},
            {"title": "  ing launches new app  ", "url": "https://www.lesoir.be/dupe"},
        ]}
    )):
        headlines = reputation.fetch_headlines("ING bank", "fake-key")
    assert headlines == [{"title": "ING launches new app", "url": "https://www.lesoir.be/first"}]


def test_fetch_headlines_drops_non_belgian_sources_even_when_the_language_matches():
    # Regression test - a Dutch accountancy trade site
    # (accountancyvanmorgen.nl) matched language=nl and inflated a bank's theme
    # count with a story that was never about the Belgian entity.
    with patch("comparator.reputation.requests.get", return_value=_FakeResponse(
        {"articles": [
            {"title": "ING tarieven stijgen", "url": "https://www.accountancyvanmorgen.nl/1"},
            {"title": "ING Belgique augmente ses tarifs", "url": "https://www.lesoir.be/1"},
        ]}
    )):
        headlines = reputation.fetch_headlines("ING bank", "fake-key")
    assert headlines == [{"title": "ING Belgique augmente ses tarifs", "url": "https://www.lesoir.be/1"}]


def test_is_belgian_source():
    assert reputation._is_belgian_source("https://www.lesoir.be/some-article") is True
    assert reputation._is_belgian_source("https://www.brusselstimes.com/some-article") is True
    # Regression - lavenir.net (L'Avenir, a real Belgian regional paper) was
    # wrongly dropped for not being a .be domain before it was added to the allowlist.
    assert reputation._is_belgian_source("https://www.lavenir.net/regions/huy-waremme/1") is True
    assert reputation._is_belgian_source("https://www.accountancyvanmorgen.nl/1") is False
    assert reputation._is_belgian_source(None) is False


def test_fetch_headlines_returns_empty_list_on_request_failure():
    with patch("comparator.reputation.requests.get", side_effect=requests.RequestException("boom")):
        assert reputation.fetch_headlines("ING bank", "fake-key") == []


def test_classify_headlines_returns_none_for_an_empty_list():
    assert reputation.classify_headlines([], "ING") is None


def test_classify_headlines_parses_a_valid_response():
    payload = '{"theme_headlines": {"innovation_digital": ["ING launches new app"], "crisis_or_scandal": []}, "notable_headlines": ["ING launches new app"]}'
    with patch("comparator.reputation._call_llm", return_value=(payload, "test/model")):
        result = reputation.classify_headlines(["ING launches new app"], "ING")
    assert result is not None
    assert result.theme_headlines["innovation_digital"] == ["ING launches new app"]
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
            theme_headlines={"innovation_digital": ["ING launches new app"]},
            notable_headlines=["ING launches new app"],
        )):
            snapshot = reputation.bank_snapshot("ING", api_key="fake-key")
    assert snapshot["headline_count"] == 1
    assert set(snapshot["themes"]) == set(reputation.THEMES)
    assert snapshot["themes"]["innovation_digital"] == 1
    assert snapshot["themes"]["crisis_or_scandal"] == 0


def test_bank_snapshot_theme_headlines_carry_their_url_and_cover_every_theme():
    # The hover popup needs the full per-theme article list, not just a count.
    with patch("comparator.reputation.fetch_headlines",
               return_value=[{"title": "ING launches new app", "url": "https://news.example/1"}]):
        with patch("comparator.reputation.classify_headlines", return_value=reputation.ReputationModel(
            theme_headlines={"innovation_digital": ["ING launches new app"]},
            notable_headlines=["ING launches new app"],
        )):
            snapshot = reputation.bank_snapshot("ING", api_key="fake-key")
    assert set(snapshot["theme_headlines"]) == set(reputation.THEMES)
    assert snapshot["theme_headlines"]["innovation_digital"] == [
        {"title": "ING launches new app", "url": "https://news.example/1"}
    ]
    assert snapshot["theme_headlines"]["crisis_or_scandal"] == []


def test_bank_snapshot_attaches_the_source_url_to_each_notable_headline():
    # The URL is looked up locally against what was fetched, never
    # produced by the model.
    with patch("comparator.reputation.fetch_headlines",
               return_value=[{"title": "ING launches new app", "url": "https://news.example/1"}]):
        with patch("comparator.reputation.classify_headlines", return_value=reputation.ReputationModel(
            theme_headlines={}, notable_headlines=["ING launches new app"],
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
            theme_headlines={}, notable_headlines=["ing launches a new app"],
        )):
            snapshot = reputation.bank_snapshot("ING", api_key="fake-key")
    assert snapshot["notable_headlines"] == [{"title": "ing launches a new app", "url": None}]


def test_bank_snapshot_reuses_a_same_day_cached_result_without_refetching():
    # Newsapi.org's free tier is 100 req/24h - iterating on unrelated
    # code within the same day must not re-spend it on banks already fetched.
    fetch = patch("comparator.reputation.fetch_headlines",
                  return_value=[{"title": "ING launches new app", "url": "https://news.example/1"}])
    classify = patch("comparator.reputation.classify_headlines", return_value=reputation.ReputationModel(
        theme_headlines={}, notable_headlines=["ING launches new app"],
    ))
    with fetch as fetch_mock, classify as classify_mock:
        first = reputation.bank_snapshot("ING", api_key="fake-key")
        second = reputation.bank_snapshot("ING", api_key="fake-key")
    assert first == second
    assert fetch_mock.call_count == 1
    assert classify_mock.call_count == 1


def _failing_fetch(*_args, errors=None, **_kwargs):
    """A fetch_headlines stand-in whose every request failed."""
    errors.append("newsapi.org/en: HTTP 401")
    return []


def test_bank_snapshot_does_not_cache_a_failed_fetch():
    # Caching a failed fetch would freeze a quota outage into a permanent
    # "nothing found" for the rest of the day.
    errors: list[str] = []
    with patch("comparator.reputation.fetch_headlines", side_effect=_failing_fetch):
        assert reputation.bank_snapshot("ING", api_key="fake-key", errors=errors) is None
    assert errors == ["newsapi.org/en: HTTP 401"]
    assert reputation._load_cache() == {}


class _StatusResponse(_FakeResponse):
    def __init__(self, status, payload=None):
        super().__init__(payload or {"articles": []})
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


def test_a_rejected_key_and_a_real_zero_no_longer_look_the_same():
    with patch("comparator.reputation.requests.get", return_value=_StatusResponse(401)):
        failed = reputation.build_dashboard([("ing", "ING")], api_key="0" * 32)
    with patch("comparator.reputation.requests.get", return_value=_StatusResponse(200)):
        quiet = reputation.build_dashboard([("ing", "ING")], api_key="0" * 32)
    assert failed["banks"]["ing"] is None
    assert failed["failures"]["ing"] == [f"newsapi.org/{lang}: HTTP 401" for lang in ("en", "fr", "nl")]
    assert quiet["failures"] == {}
    assert quiet["banks"]["ing"]["headline_count"] == 0
    assert set(quiet["banks"]["ing"]["themes"].values()) == {0}
    assert quiet["banks"]["ing"]["fetch_errors"] == []


def test_a_connection_error_is_recorded_too():
    errors: list[str] = []
    with patch("comparator.reputation.requests.get", side_effect=requests.ConnectionError("down")):
        assert reputation.fetch_headlines("ING", "0" * 32, errors=errors) == []
    assert errors == [f"newsapi.org/{lang}: ConnectionError" for lang in ("en", "fr", "nl")]


def test_a_real_zero_skips_the_classifier_and_is_cached():
    with patch("comparator.reputation.requests.get", return_value=_StatusResponse(200)),          patch("comparator.reputation._call_llm") as llm:
        snapshot = reputation.bank_snapshot("ING", api_key="0" * 32)
    llm.assert_not_called()
    assert snapshot["headline_count"] == 0
    assert reputation._load_cache()["ING"]["snapshot"] == snapshot


def test_a_partial_failure_is_flagged_and_not_cached():
    # en answers, fr and nl hit the rate limit: the counts are a lower bound,
    # and caching them would serve the thinned numbers all day.
    def get(_url, params, **_kwargs):
        if params["language"] == "en":
            return _StatusResponse(200, {"articles": [
                {"title": "ING opens office", "url": "https://www.lesoir.be/1"}]})
        return _StatusResponse(429)

    payload = '{"theme_headlines": {"other": ["ING opens office"]}, "notable_headlines": []}'
    with patch("comparator.reputation.requests.get", side_effect=get),          patch("comparator.reputation._call_llm", return_value=(payload, "test/model")):
        dashboard = reputation.build_dashboard([("ing", "ING")], api_key="0" * 32)
    snapshot = dashboard["banks"]["ing"]
    assert snapshot["headline_count"] == 1
    assert snapshot["fetch_errors"] == ["newsapi.org/fr: HTTP 429", "newsapi.org/nl: HTTP 429"]
    assert dashboard["failures"]["ing"] == snapshot["fetch_errors"]
    assert reputation._load_cache() == {}


def test_a_failed_classification_is_named_as_such():
    errors: list[str] = []
    with patch("comparator.reputation.fetch_headlines",
               return_value=[{"title": "ING launches new app", "url": "https://www.lesoir.be/1"}]),          patch("comparator.reputation.classify_headlines", return_value=None):
        assert reputation.bank_snapshot("ING", api_key="fake-key", errors=errors) is None
    assert errors == ["classification failed"]


def test_build_dashboard_is_unavailable_without_a_key(monkeypatch):
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    monkeypatch.delenv("NEWSAPI_AI_KEY", raising=False)
    dashboard = reputation.build_dashboard([("ing", "ING")])
    assert dashboard == {"available": False, "banks": {}, "failures": {}}


def test_build_dashboard_covers_every_bank_when_a_key_is_present():
    with patch("comparator.reputation.bank_snapshot", return_value={"headline_count": 0, "themes": {}, "notable_headlines": []}):
        dashboard = reputation.build_dashboard([("ing", "ING"), ("kbc", "KBC")], api_key="fake-key")
    assert dashboard["available"] is True
    assert set(dashboard["banks"]) == {"ing", "kbc"}


def test_bank_snapshot_finds_the_url_of_a_re_cased_headline():
    # a title the model only re-cased is still the fetched article.
    with patch("comparator.reputation.fetch_headlines",
               return_value=[{"title": "ING launches new app", "url": "https://news.example/1"}]):
        with patch("comparator.reputation.classify_headlines", return_value=reputation.ReputationModel(
            theme_headlines={"product_launch": ["ing  launches NEW app"]},
            notable_headlines=["ing launches new app"],
        )):
            snapshot = reputation.bank_snapshot("ING", api_key="fake-key")
    assert snapshot["notable_headlines"][0]["url"] == "https://news.example/1"
    assert snapshot["theme_headlines"]["product_launch"][0]["url"] == "https://news.example/1"


def test_hello_bank_is_searched_as_a_brand_not_as_the_word_hello():
    # "Hello" alone matches countless unrelated headlines.
    assert reputation._bank_token("Hello bank!") == "Hello bank"
    kept = reputation._mentions(
        [{"title": "Hello bank! lance une offre"}, {"title": "Hello world, says a startup"}],
        "Hello bank!",
    )
    assert [h["title"] for h in kept] == ["Hello bank! lance une offre"]


def test_cache_path_does_not_depend_on_the_current_directory():
    # The autouse fixture swaps CACHE_PATH for a temp file, so reload the
    # module in a fresh namespace to read the real, repository-anchored value.
    import importlib.util

    spec = importlib.util.spec_from_file_location("_rep_fresh", reputation.__file__)
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    repo_root = Path(reputation.__file__).resolve().parents[2]
    assert fresh.CACHE_PATH == repo_root / "data" / "processed" / "reputation_cache.json"


# The keys this module reads used to arrive only because the llm_extractor
# import calls load_dotenv() at module load. That is an import-order
# dependency and a silent one: move _call_llm and every fetch loses its key,
# which the UI renders as the same "no data" a quota outage produces. Pin that
# reputation.py loads the file itself, so the failure cannot come back quietly.
def test_module_loads_the_env_file_itself_not_via_another_import():
    import importlib.util

    from comparator import reputation

    with patch("dotenv.load_dotenv") as loader:
        spec = importlib.util.spec_from_file_location("_rep_env", reputation.__file__)
        fresh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fresh)

    assert loader.called, "reputation.py must call load_dotenv() at import, not rely on another module"
