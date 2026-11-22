"""Tests for the search_interest benchmark (Streamlit views, export prose, retry policy).

search_interest/ is a standalone sub-project with bare imports (`from config
import ...`), so its modules are loaded by path with its folders on sys.path for
the duration of the import only. Nothing here touches the network: the pytrends
client is a stub and time.sleep is replaced.
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

SI = Path(__file__).resolve().parents[1] / "search_interest"


def _load(name: str, rel: str, monkeypatch):
    """Import search_interest/<rel> under a private name, restoring sys.path/modules."""
    monkeypatch.syspath_prepend(str(SI))
    monkeypatch.syspath_prepend(str(SI / "collectors"))
    spec = importlib.util.spec_from_file_location(name, SI / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # config is imported under its bare name; drop it so it cannot leak into
    # another test that imports a different `config`.
    for bare in ("config", "config_candidates", "pytrends_network"):
        monkeypatch.delitem(sys.modules, bare, raising=False)
    return module


@pytest.fixture()
def app(monkeypatch):
    """The Streamlit app module, with plotly stubbed when it is not installed."""
    try:
        import plotly.graph_objects  # noqa: F401
    except ImportError:
        monkeypatch.setitem(sys.modules, "plotly", MagicMock())
        monkeypatch.setitem(sys.modules, "plotly.graph_objects", MagicMock())
    pytest.importorskip("streamlit")
    return _load("si_app", "app.py", monkeypatch)


@pytest.fixture()
def cfg(monkeypatch):
    return _load("si_config", "config.py", monkeypatch)


# --- the sidebar views -------------------------------------------------------
def test_every_comparison_view_shows_at_least_one_sheet(app):
    """Seven of the eight bank views used to be empty (st.stop), and the five
    banks added after the first nine had no view at all."""
    for label in app.COMPARISON_VIEWS:
        assert app.fiches_for_view(label), f"view {label!r} has no sheet"


def test_every_bank_of_the_config_has_a_view_except_the_anchor(app, cfg):
    banks_with_a_view = {b for b in app.COMPARISON_VIEWS.values() if b}
    assert banks_with_a_view == set(cfg.BANK_DISPLAY_LABELS) - {"ING"}


def test_a_bank_view_only_holds_sheets_where_the_bank_has_a_term(app):
    for label, bank in app.COMPARISON_VIEWS.items():
        if bank is None:
            continue
        for sheet in app.fiches_for_view(label):
            assert any(t["bank"] == bank for t in sheet["terms"]), (label, sheet["product_id"])


def test_the_all_sheets_view_holds_every_sheet(app, cfg):
    all_view = app.fiches_for_view(app.BRAND_CONTEXT_VIEW)
    assert [p["product_id"] for p in all_view] == [p["product_id"] for p in cfg.PRODUCTS]


def test_two_banks_of_one_sheet_never_share_a_line_style(app, cfg):
    """BANK_DASH reuses styles on purpose; that is only safe inside one chart."""
    assert set(app.BANK_DASH) == set(cfg.BANK_DISPLAY_LABELS)
    for sheet in cfg.PRODUCTS:
        dashes = [app.BANK_DASH[t["bank"]] for t in sheet["terms"]]
        assert len(dashes) == len(set(dashes)), sheet["product_id"]


# --- the exported methodology text -------------------------------------------
def test_export_prose_counts_banks_and_sheets_from_the_config(monkeypatch, cfg):
    """The text said "9 banques" and "3 fiches" whatever the config held."""
    export = _load("si_export", "export/export_common.py", monkeypatch)
    conn = sqlite3.connect(":memory:")
    conn.executescript((SI / "db" / "schema.sql").read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO trends_data VALUES ('marque_generique', 'Marque', 'ING', 'ING', 'en', '2026-01-04', 50)"
    )
    conn.execute("INSERT INTO brand_share_of_search VALUES ('ING', '2026-01-04', 'marque_generique', 50, 1.0, 50.0, 1.0)")

    text = export.build_markdown(conn, "t.csv", "s.csv", 1, 1)

    panel_banks = {t["bank"] for p in cfg.PRODUCTS for t in p["terms"]}
    assert f"des {len(panel_banks)} banques du panel" in text
    assert f"réparties sur {len(cfg.PRODUCTS)} fiches" in text
    assert f"somme_{len(panel_banks)}_banques" in text
    assert "9 banques" not in text and "3 fiches" not in text
    for sheet in cfg.PRODUCTS:
        assert f"`{sheet['product_id']}`" in text


# --- retry policy ------------------------------------------------------------
class _FlakyTrends:
    """A pytrends stand-in whose first `failures` calls raise."""

    def __init__(self, failures):
        self.failures = failures
        self.calls = 0

    def build_payload(self, *args, **kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("429")

    def interest_over_time(self):
        return "frame"

    def suggestions(self, keyword):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("429")
        return [{"mid": "/m/1"}]


@pytest.fixture()
def network(monkeypatch):
    module = _load("si_network", "collectors/pytrends_network.py", monkeypatch)
    sleeps = []
    monkeypatch.setattr(module.time, "sleep", sleeps.append)
    monkeypatch.setattr(module.random, "uniform", lambda lo, hi: 0.0)
    return module, sleeps


def test_a_failed_request_is_retried_with_a_doubling_backoff(network):
    module, sleeps = network
    client = _FlakyTrends(failures=2)
    assert module.fetch_with_retry(client, ["ING"], "today 5-y", "BE") == "frame"
    assert client.calls == 3
    assert sleeps == [module.INITIAL_BACKOFF_SECONDS, 2 * module.INITIAL_BACKOFF_SECONDS]


def test_suggestions_share_the_same_policy(network):
    module, sleeps = network
    client = _FlakyTrends(failures=1)
    assert module.suggestions_with_retry(client, "ING") == [{"mid": "/m/1"}]
    assert sleeps == [module.INITIAL_BACKOFF_SECONDS]


def test_the_request_gives_up_after_max_retries(network):
    module, sleeps = network
    client = _FlakyTrends(failures=99)
    with pytest.raises(RuntimeError):
        module.fetch_with_retry(client, ["ING"], "today 5-y", "BE")
    assert client.calls == module.MAX_RETRIES + 1
    assert len(sleeps) == module.MAX_RETRIES


# --- term resolution ---------------------------------------------------------
@pytest.fixture()
def resolver(monkeypatch):
    return _load("si_resolver", "collectors/term_resolver.py", monkeypatch)


def test_strings_survive_when_many_topics_match(resolver):
    """Cutting topics + strings at 5 terms dropped every string once 5 topics
    matched, and decide_brand_winner then raised IndexError on strings[0]."""
    topics = [{"term": f"/m/{i}", "kind": "topic"} for i in range(6)]
    strings = [{"term": "Argenta", "kind": "string"}]
    candidates = resolver.candidates_within_request_limit(topics, strings)
    assert len(candidates) == 5
    assert candidates[-1] == strings[0]
    assert [c["term"] for c in candidates[:-1]] == ["/m/0", "/m/1", "/m/2", "/m/3"]


def test_a_brand_with_no_valid_topic_falls_back_to_its_string(resolver):
    results = [
        {"kind": "topic", "term": "/m/1", "coverage": 0.1},
        {"kind": "string", "term": "Argenta", "coverage": 0.2},
    ]
    winner, flags = resolver.decide_brand_winner({"topic_required": True}, results)
    assert winner["term"] == "Argenta" and flags == ["ambiguous_string"]


def test_the_product_phase_is_gone(resolver):
    """PRODUCTS only holds brand sheets, so product resolution could only raise KeyError."""
    assert not hasattr(resolver, "resolve_product_fiche")
    assert hasattr(resolver, "resolve_brand")


def test_the_schema_has_no_campaign_or_anomaly_tables(cfg):
    """The anomaly detector and the campaign scoring built on it are gone."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(Path(cfg.SCHEMA_PATH).read_text(encoding="utf-8"))
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert names
    assert not [n for n in names if "campaign" in n or "anomal" in n]
    assert not (SI / "campaigns").exists()


# --- collection --------------------------------------------------------------
def test_the_unfinished_last_week_is_not_stored(monkeypatch):
    import pandas as pd

    collector = _load("si_collector", "collectors/trends_collector.py", monkeypatch)
    conn = sqlite3.connect(":memory:")
    conn.executescript((SI / "db" / "schema.sql").read_text(encoding="utf-8"))
    df = pd.DataFrame(
        {"ING": [50, 60, 5], "isPartial": [False, False, True]},
        index=pd.to_datetime(["2026-01-04", "2026-01-11", "2026-01-18"]),
    )
    product = {"product_id": "p", "product_label": "P", "terms": [{"term": "ING", "bank": "ING", "language": "en"}]}

    collector.store_long_format(conn, product, df)

    assert conn.execute("SELECT date, value FROM trends_data ORDER BY date").fetchall() == [
        ("2026-01-04", 50), ("2026-01-11", 60),
    ]
