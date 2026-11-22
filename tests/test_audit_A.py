"""Regression tests for comparator/trends.py found while re-reading it line by line.

Only trends.py is covered here: the analysis, schema, dictionary and collection
modules are restricted, so what was found in them is reported, not tested.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from comparator import banks, trends  # noqa: E402


def _rows(bank: str, product: str, weeks: int = 60) -> list[dict]:
    return [
        {
            "product_id": product, "product_label": product, "term": f"{bank} x",
            "bank": bank, "language": "fr",
            "date": (pd.Timestamp("2023-01-01") + pd.Timedelta(weeks=w)).date(),
            "value": 10,
        }
        for w in range(weeks)
    ]


def test_combined_export_is_not_counted_twice(tmp_path):
    """all_trends_data.csv also matches *_trends_data.csv, so a folder holding the
    combined file next to the per-bank ones used to load every row twice."""
    ing, kbc = _rows("ING", "compte_epargne"), _rows("KBC", "compte_a_vue")
    pd.DataFrame(ing + kbc).to_csv(tmp_path / "all_trends_data.csv", index=False)
    pd.DataFrame(ing).to_csv(tmp_path / "ing_trends_data.csv", index=False)
    pd.DataFrame(kbc).to_csv(tmp_path / "kbc_trends_data.csv", index=False)

    loaded = trends.load_trends(tmp_path)

    assert len(loaded) == 120
    assert len(trends.load_series(tmp_path)) == 120


def test_load_trends_falls_back_to_per_bank_files(tmp_path):
    pd.DataFrame(_rows("ING", "compte_epargne")).to_csv(tmp_path / "ing_trends_data.csv", index=False)
    pd.DataFrame(_rows("KBC", "compte_a_vue")).to_csv(tmp_path / "kbc_trends_data.csv", index=False)

    assert len(trends.load_trends(tmp_path)) == 120


def test_bank_display_matches_the_canonical_bank_names():
    """trends.BANK_DISPLAY is derived from comparator.banks, never retyped."""
    assert trends.BANK_DISPLAY == {
        "ING": "ING", "KBC": "KBC", "CBC": "CBC", "BNPPF": "BNP Paribas Fortis",
        "ARGENTA": "Argenta", "CRELAN": "Crelan", "REVOLUT": "Revolut",
        "N26": "N26", "BUNQ": "bunq", "BELFIUS": "Belfius", "BEOBANK": "Beobank",
        "VDK": "VDK Bank", "HELLOBANK": "Hello bank!", "KEYTRADE": "Keytrade Bank",
    }
    for code, key in trends.BANK_MAP.items():
        assert trends.BANK_DISPLAY[code] == banks.display_name(key)


# --- the mirrors of the upstream benchmark config ------------------------------
def _upstream_config():
    path = ROOT / "search_interest" / "config.py"
    if not path.is_file():
        pytest.skip("search_interest/config.py is not checked out")
    spec = importlib.util.spec_from_file_location("_upstream_search_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mirrored_constants_match_the_upstream_config():
    config = _upstream_config()
    assert trends.TERM_DISPLAY == config.TERM_DISPLAY_LABELS
    assert trends.SHARE_REFERENCE_SHEET == config.SHARE_OF_SEARCH_REFERENCE_FICHE
    assert trends.SHARE_ANCHOR_BANKS == tuple(config.SHARE_OF_SEARCH_ANCHOR_BANKS)
    # Labels are translated here, so only the facts that place an event are compared.
    place = lambda events: [(e["bank"], e["date"]) for e in events]  # noqa: E731
    assert place(trends.KNOWN_EVENTS) == place(config.KNOWN_EVENTS)


def test_brand_sheets_are_the_sheets_of_the_exported_share_table():
    path = trends.DEFAULT_EXPORT_DIR / "brand_share_of_search.csv"
    if not path.is_file():
        pytest.skip("share-of-search export is not checked out")
    exported = set(pd.read_csv(path, usecols=["source_fiche"])["source_fiche"])
    assert exported == set(trends.BRAND_SHEETS)
    assert trends.SHARE_REFERENCE_SHEET in trends.BRAND_SHEETS


# =============================================================================
# Fixes in the analysis, schema and collection modules.
# =============================================================================
import http.server  # noqa: E402
import threading  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from unittest.mock import patch  # noqa: E402

from comparator import analysis, schema  # noqa: E402
from comparator.collection import compliance, quality, render, scraper, visual_features  # noqa: E402
from comparator.collection.compliance import ScrapingNotAllowed, get_checked  # noqa: E402
from comparator.dictionary import load_dictionary  # noqa: E402


def _response(status: int, location: str | None = None, text: str = "ok"):
    headers = {"Location": location} if location else {}
    return SimpleNamespace(status_code=status, headers=headers, text=text, content=b"")


def _gate_for(blocked_host: str):
    def gate(url: str) -> None:
        if blocked_host in url:
            raise ScrapingNotAllowed(f"{url}: disallowed")
    return gate


# --- redirects are gated hop by hop ---------------------------------------------
def test_get_checked_refuses_a_redirect_to_a_disallowed_page():
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        assert kwargs["allow_redirects"] is False
        return _response(302, "https://other.example/page") if "start" in url else _response(200)

    with patch("comparator.collection.compliance.requests.get", side_effect=fake_get):
        with pytest.raises(ScrapingNotAllowed):
            get_checked("https://ok.example/start", gate=_gate_for("other.example"))
    assert calls == ["https://ok.example/start"]


def test_get_checked_follows_allowed_redirects_and_resolves_relative_ones():
    seen = []

    def fake_get(url, **kwargs):
        seen.append(url)
        return _response(301, "/final") if url.endswith("/start") else _response(200, text="done")

    with patch("comparator.collection.compliance.requests.get", side_effect=fake_get):
        result = get_checked("https://ok.example/start", gate=lambda url: None)
    assert result.text == "done"
    assert seen == ["https://ok.example/start", "https://ok.example/final"]


def test_get_checked_gives_up_on_a_redirect_loop():
    with patch("comparator.collection.compliance.requests.get",
               side_effect=lambda url, **kw: _response(302, "https://ok.example/again")):
        with pytest.raises(compliance.requests.TooManyRedirects):
            get_checked("https://ok.example/start", gate=lambda url: None)


def test_static_fetch_does_not_land_on_a_disallowed_redirect_target():
    def fake_check(url):
        return compliance.ComplianceCheck(url, allowed="blocked" not in url, reason="test")

    def fake_get(url, **kwargs):
        return _response(302, "https://blocked.example/page") if "ok.example" in url else _response(200, text="SECRET")

    with patch("comparator.collection.compliance.check_robots", side_effect=fake_check), \
         patch("comparator.collection.compliance.requests.get", side_effect=fake_get):
        with pytest.raises(ScrapingNotAllowed):
            scraper._fetch_html("https://ok.example/start")


def test_hero_image_redirect_to_a_disallowed_path_gives_no_colours():
    gated = []

    def gate(url):
        gated.append(url)
        _gate_for("blocked.example")(url)

    def fake_get(url, **kwargs):
        return _response(302, "https://blocked.example/hero.jpg") if "ok.example" in url else _response(200)

    with patch("comparator.collection.visual_features.assert_can_fetch", side_effect=gate),          patch("comparator.collection.compliance.requests.get", side_effect=fake_get) as get:
        result = visual_features.extract_colours("https://ok.example/hero.jpg", bank="ing")
    assert result["dominant_colour_hex"] is None
    assert gated == ["https://ok.example/hero.jpg", "https://blocked.example/hero.jpg"]
    assert get.call_count == 1


def test_static_fetch_decodes_a_page_that_declares_no_charset():
    response = SimpleNamespace(status_code=200, headers={"Content-Type": "text/html"},
                               encoding="ISO-8859-1", apparent_encoding="utf-8",
                               text="x", raise_for_status=lambda: None)
    with patch("comparator.collection.scraper.get_checked", return_value=response):
        scraper._fetch_html("https://ok.example/")
    assert response.encoding == "utf-8"


# --- the render path: a redirect to another host is gated -------------------------
def test_main_frame_navigation_is_gated_whatever_its_origin():
    with patch("comparator.collection.render.check_robots",
               return_value=compliance.ComplianceCheck("u", allowed=False, reason="no")):
        assert render._blocks_same_origin_asset("https://www.n26.com/", "n26.com", main_navigation=True) is True
        assert render._blocks_same_origin_asset("https://cdn.example/a.js", "n26.com") is False


def _serve(handler) -> http.server.HTTPServer:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _chrome():
    sync_api = pytest.importorskip("playwright.sync_api")
    manager = sync_api.sync_playwright().start()
    try:
        browser = manager.chromium.launch(channel="chrome")
    except Exception:
        manager.stop()
        pytest.skip("no local Chrome to drive")
    return manager, browser


def _redirecting_servers(target_robots: bytes):
    """Loopback servers, no internet: A allows everything and redirects to B,
    whose robots.txt is `target_robots`."""

    def handler(routes):
        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def do_GET(self):
                status, headers, body = routes(self.path)
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        return Handler

    page = b"<html><body><p>FINAL PAGE</p></body></html>"
    server_b = _serve(handler(lambda path: (200, {}, target_robots if path == "/robots.txt" else page)))

    def a_routes(path):
        if path == "/robots.txt":
            return 200, {}, b"User-agent: *\nAllow: /\n"
        return 302, {"Location": f"http://127.0.0.1:{server_b.server_port}/page"}, b""

    return _serve(handler(a_routes)), server_b


def test_render_refuses_a_redirect_whose_target_disallows_robots(monkeypatch):
    manager, browser = _chrome()
    browser.close()
    manager.stop()
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    compliance.clear_cache()
    server_a, server_b = _redirecting_servers(b"User-agent: *\nDisallow: /\n")
    try:
        with pytest.raises(ScrapingNotAllowed):
            render.render(f"http://127.0.0.1:{server_a.server_port}/start", channel="chrome",
                          timeout_ms=10_000)
    finally:
        server_a.shutdown()
        server_b.shutdown()
        compliance.clear_cache()


def test_render_still_follows_a_redirect_whose_target_allows_robots(monkeypatch):
    manager, browser = _chrome()
    browser.close()
    manager.stop()
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    compliance.clear_cache()
    server_a, server_b = _redirecting_servers(b"User-agent: *\nAllow: /\n")
    try:
        result = render.render(f"http://127.0.0.1:{server_a.server_port}/start", channel="chrome",
                               timeout_ms=10_000)
    finally:
        server_a.shutdown()
        server_b.shutdown()
        compliance.clear_cache()
    assert "FINAL PAGE" in result.html
    assert result.http_status == 200


def test_measurement_counts_visible_hero_area_and_each_picture_once():
    manager, browser = _chrome()
    try:
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        gif = "data:image/gif;base64,R0lGODlhAQABAAAAACw="
        page.set_content(
            '<body style="margin:0"><div style="height:600px"></div>'
            f'<img style="display:block;width:1440px;height:600px" src="{gif}">'
            '<div style="height:3000px"></div>'
            f'<picture><img style="display:block;width:720px;height:500px" src="{gif}"></picture></body>'
        )
        measured = page.evaluate(render._MEASURE_JS, render.MIN_IMAGE_EDGE_PX)
    finally:
        browser.close()
        manager.stop()
    assert measured["hero_image_area"] == 1440 * 300
    assert measured["total_image_area"] == 1440 * 600 + 720 * 500


# --- word counting ----------------------------------------------------------------
def test_stray_hyphens_and_apostrophes_are_not_words():
    out = scraper.extract("<p>Open - your - account - today ' now -- ok</p>", language="en")
    assert out["word_count"] == 6


def test_hyphenated_and_elided_words_still_count_once():
    out = scraper.extract("<p>L'offre est e-banking, peer-to-peer et d'ici peu.</p>", language="fr")
    assert out["word_count"] == 7


def test_readability_of_an_empty_page_is_missing_not_invented():
    assert scraper._readability("", "fr") == (None, "kandel_moles_fr", None)
    out = scraper.extract("<html><body></body></html>", language="fr")
    assert out["readability_score"] is None and out["readability_band"] is None


def test_a_page_with_no_section_tags_has_zero_sections():
    assert scraper.extract("<p>no sections here</p>", language="en")["section_count"] == 0
    assert scraper.extract("<section>a</section><article>b</article>", language="en")["section_count"] == 2


def test_nested_disclaimer_blocks_are_counted_once():
    html = ("<p>" + "word " * 100 + "</p><div class='legal'><p class='legal-note'>"
            + "fine print here " * 5 + "</p></div>")
    out = scraper.extract(html, language="en")
    assert out["disclaimer_word_share"] == round(15 / out["word_count"], 3)


# --- keyword matching on whole words ----------------------------------------------
def test_a_deadline_preposition_inside_a_longer_word_is_not_a_deadline():
    assert scraper._count_urgency_markers("Cute baby 12/10/2026 shop", "en") == 0
    assert scraper._count_urgency_markers("Apply until 12/10/2026", "en") == 1
    assert scraper._count_urgency_markers("Déposez avant le 11/10/2026", "fr") == 1
    assert scraper._count_urgency_markers("Voorwaarden 12/10/2026", "nl") == 0


def test_a_rate_keyword_inside_a_longer_word_is_not_a_rate():
    assert scraper._rate("Open your account 100% online with a corporate bank", "en") == (False, None)
    assert scraper._rate("Savings rate of 2.5% a year", "en") == (True, 2.5)
    assert scraper._rate("Taux d'intérêts de 3,5% par an", "fr") == (True, 3.5)


# --- capture quality ---------------------------------------------------------------
def test_error_wording_inside_a_full_page_does_not_condemn_it():
    row = {"word_count": 600, "image_count": 5, "cta_count": 3, "page_height_px": 4000,
           "http_status": 200, "meta_title": "Hypotheek"}
    long_text = "Vraag een onderhoud aan met uw adviseur. " + "woord " * 600
    assert quality.assess_capture(row, long_text).verdict == "ok"
    assert quality.assess_capture(row, "Onderhoud bezig, tijdelijk niet beschikbaar").verdict == "unusable"


# --- analysis ----------------------------------------------------------------------
def test_direction_is_above_when_peers_have_no_spread_and_focus_is_higher():
    rows = [{"bank": b, "bank_category": c, "page_id": b, "product_family": "x",
             "urgency_marker_count": 5.0 if b == "ing" else 0.0}
            for b, c in [("ing", "traditional")] + [(f"p{i}", "challenger") for i in range(4)]]
    gaps = analysis.ing_vs_peers(pd.DataFrame(rows), load_dictionary())
    row = gaps[gaps["feature"] == "urgency_marker_count"].iloc[0]
    assert row["direction"] == "above peers" and not row["reportable"]


# --- schema ------------------------------------------------------------------------
def test_a_missing_cell_parses_to_an_empty_list():
    assert schema.parse_list(pd.NA) == []
    assert schema.format_list(schema.parse_list(pd.NA)) == ""


def test_unreadable_values_are_reported_when_they_become_missing():
    fd = load_dictionary()
    frame = pd.DataFrame({"rate_value_pct": ["3,5", "2.0", None], "has_animation": ["True", "maybe", "False"]})
    coerced = schema.coerce_types(frame, fd)
    assert coerced.attrs["coerced_to_missing"] == {"rate_value_pct": 1, "has_animation": 1}
    warnings = schema.validate(coerced, fd).warnings
    assert any(w.startswith("rate_value_pct: 1 value(s)") for w in warnings)
    assert any(w.startswith("has_animation: 1 value(s)") for w in warnings)
