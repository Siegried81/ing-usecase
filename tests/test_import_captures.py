"""Tests for importing manually saved captures (steph 16/09)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("import_captures", ROOT / "scripts" / "import_captures.py")
import_captures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_captures)


def test_url_is_recovered_from_the_browser_save_comment():
    html = '<!-- saved from url=(0043)https://www.ing.be/fr/particuliers/epargner -->\n<html></html>'
    assert import_captures.recover_url(html) == "https://www.ing.be/fr/particuliers/epargner"


def test_url_falls_back_to_the_canonical_link():
    html = '<html><head><link rel="canonical" href="https://www.revolut.com/fr-BE/bank-account/"></head></html>'
    assert import_captures.recover_url(html) == "https://www.revolut.com/fr-BE/bank-account/"


def test_no_url_means_no_row_rather_than_a_guessed_one():
    assert import_captures.recover_url("<html><body>nothing</body></html>") is None


@pytest.mark.parametrize("name,expected", [
    ("current_account_pack_fr_02", ("current_account_pack", "fr", 2)),
    ("savings_account_nl_01", ("savings_account", "nl", 1)),
    ("mortgage_en_10", ("mortgage", "en", 10)),
])
def test_filename_parsing(name, expected):
    m = import_captures.NAME_RE.match(name)
    assert m and (m["family"], m["language"], int(m["index"])) == expected


def test_a_badly_named_file_is_rejected():
    assert import_captures.NAME_RE.match("random-page") is None


def test_robots_is_rechecked_not_taken_on_trust(tmp_path, monkeypatch):
    """Siegried confirmed all five paths were allowed. 'We checked earlier' is
    exactly the assumption that rots, so the importer checks again (LC-01)."""
    from comparator.collection.compliance import ScrapingNotAllowed

    page = tmp_path / "ing" / "savings_account_fr_01.html"
    page.parent.mkdir(parents=True)
    page.write_text('<!-- saved from url=(0043)https://www.ing.be/x -->\n<html><body>'
                    + "word " * 400 + "</body></html>", encoding="utf-8")

    called = {}

    def deny(url):
        called["url"] = url
        raise ScrapingNotAllowed("disallowed")

    monkeypatch.setattr(import_captures, "assert_can_fetch", deny)
    row = import_captures.import_one(page, "ing", raw_dir=tmp_path / "raw", fd=None)
    assert row is None, "a disallowed path must not produce a row"
    assert called["url"] == "https://www.ing.be/x"


def test_manual_rows_carry_no_invented_http_status(tmp_path, monkeypatch):
    """We made no request, so there is no status of ours. 200 would be a lie."""
    page = tmp_path / "ing" / "savings_account_fr_01.html"
    page.parent.mkdir(parents=True)
    page.write_text('<!-- saved from url=(0043)https://www.ing.be/x -->\n<html><body>'
                    + "mot " * 400 + "</body></html>", encoding="utf-8")

    monkeypatch.setattr(import_captures, "assert_can_fetch", lambda url: None)
    monkeypatch.setattr(import_captures, "extract_model_assisted_with_provenance",
                        lambda *a, **k: (_ for _ in ()).throw(import_captures.LLMExtractionError("skip")))

    row = import_captures.import_one(page, "ing", raw_dir=tmp_path / "raw", fd=None)
    assert row is not None
    assert row["http_status"] is None
    assert row["collection_method"] == "manual_capture"
    assert row["bank_category"] == "traditional"
