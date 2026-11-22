"""Regression tests for the scripts/, services/ and streamlit_app.py review.

Each test failed on the code it was written against; the comment says how.
Modules that need an optional dependency (aiohttp, playwright) are loaded with
a stub of that dependency, since nothing here may touch the network or a browser.
"""

from __future__ import annotations

import asyncio
import importlib.util
import io
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# import_captures
# ---------------------------------------------------------------------------

import_captures = _load("import_captures_c", ROOT / "scripts" / "import_captures.py")


def test_merge_accepts_an_existing_dataset_without_capture_quality():
    # Used to raise KeyError: True, because existing.get("capture_quality", "ok")
    # returned the string "ok" and the comparison became a scalar mask.
    existing = pd.DataFrame({"page_id": ["a_1", "b_1"], "bank": ["a", "b"]})
    imported = pd.DataFrame({"page_id": ["a_1", "c_1"], "bank": ["a", "c"], "extraction_model": ["m", "m"]})
    merged = import_captures.merge_with_existing(imported, existing)
    # a_1 is "ok" by default, so the live row stays and only c_1 is added.
    assert sorted(merged["page_id"]) == ["a_1", "b_1", "c_1"]
    assert merged.loc[merged["page_id"] == "a_1", "extraction_model"].isna().all()


def test_merge_replaces_a_live_row_only_when_it_is_not_ok():
    existing = pd.DataFrame({"page_id": ["a_1", "b_1"], "bank": ["a", "b"],
                             "capture_quality": ["unusable", "ok"]})
    imported = pd.DataFrame({"page_id": ["a_1", "b_1"], "bank": ["a", "b"],
                             "capture_quality": ["ok", "ok"], "http_status": [None, None]})
    merged = import_captures.merge_with_existing(imported, existing).set_index("page_id")
    assert len(merged) == 2
    assert merged.loc["a_1", "capture_quality"] == "ok"
    assert "http_status" in merged.columns


def test_manual_capture_colours_use_the_first_screen(tmp_path, monkeypatch):
    # background_luminance was measured on the whole page strip for manual
    # captures (no first_screen_px), unlike the live path.
    from PIL import Image

    from comparator.collection.render import VIEWPORT_HEIGHT

    html = ('<!-- saved from url=(0030)https://www.ing.be/fr/epargner -->'
            "<html><body><h1>Epargner</h1><p>Ouvrez un compte.</p></body></html>")
    page = tmp_path / "caps" / "ing" / "savings_account_fr_01.html"
    page.parent.mkdir(parents=True)
    page.write_text(html, encoding="utf-8")
    Image.new("RGB", (50, 50), "white").save(page.with_suffix(".png"))

    seen: dict = {}

    def fake_colours(image, *, bank=None, n_colours=5, first_screen_px=None):
        seen["first_screen_px"] = first_screen_px
        return {}

    monkeypatch.setattr(import_captures, "assert_can_fetch", lambda url: None)
    monkeypatch.setattr(import_captures, "extract_colours_from_image", fake_colours)
    monkeypatch.setattr(import_captures, "extract_model_assisted_with_provenance",
                        lambda *a, **k: (None, None))
    row = import_captures.import_one(page, "ing", raw_dir=tmp_path / "raw")
    assert row is not None
    assert seen["first_screen_px"] == VIEWPORT_HEIGHT


# ---------------------------------------------------------------------------
# rederive_* scripts read the page the way the capture did
# ---------------------------------------------------------------------------

# <noscript> text is dropped by extract() but kept by a plain get_text().
NOSCRIPT_ONLY_URGENCY = (
    "<html><body><noscript>offre limitée, jusqu'au 31/12/2030</noscript>"
    "<p>Ouvrez un compte d'épargne.</p></body></html>"
)


def _frame_for(tmp_path, html):
    snap = tmp_path / "snap.html"
    snap.write_text(html, encoding="utf-8")
    return pd.DataFrame([{
        "page_id": "p1", "snapshot_html_path": str(snap), "language": "fr",
        "url": "https://x.example/", "product_family": "savings_account",
        "urgency_marker_count": 99, "cross_sold_products": "",
    }])


def test_rederive_urgency_ignores_noscript_text(tmp_path):
    # Used to count terms inside <noscript>, which extract() drops: the same page
    # scored differently depending on which path measured it.
    rederive = _load("rederive_urgency_c", ROOT / "scripts" / "rederive_urgency_markers.py")
    df = rederive.rederive(_frame_for(tmp_path, NOSCRIPT_ONLY_URGENCY), tmp_path / "x.csv")
    assert df.loc[0, "urgency_marker_count"] == 0


def test_rederive_cross_sold_sends_the_capture_text_not_the_noscript_block(tmp_path, monkeypatch):
    rederive = _load("rederive_cross_sold_c", ROOT / "scripts" / "rederive_cross_sold_products.py")
    sent: dict = {}

    def fake_extract(*, page_text, image_count, has_animation, product_family):
        sent["text"] = page_text
        return types.SimpleNamespace(cross_sold_products=[])

    monkeypatch.setattr(rederive, "extract_model_assisted", fake_extract)
    rederive.rederive(_frame_for(tmp_path, NOSCRIPT_ONLY_URGENCY), tmp_path / "x.csv")
    assert "offre limitée" not in sent["text"]
    assert "compte d'épargne" in sent["text"]


# ---------------------------------------------------------------------------
# health_dashboard
# ---------------------------------------------------------------------------


def _health_module(status: int):
    """Load services/health_dashboard.py with an aiohttp stub answering `status`."""
    class Response:
        def __init__(self, code):
            self.status = code

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    class Session:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        def get(self, url, raise_for_status=False):
            if raise_for_status and status >= 400:
                raise RuntimeError(f"HTTP {status}")
            return Response(status)

    stub = types.ModuleType("aiohttp")
    stub.ClientSession = Session
    stub.ClientTimeout = lambda total: None
    sys.modules["aiohttp"] = stub
    try:
        return _load("health_dashboard_c", ROOT / "services" / "health_dashboard.py")
    finally:
        del sys.modules["aiohttp"]


CONFIG = {"url": "http://svc/health", "name": "Svc"}


@pytest.mark.parametrize("code", [200, 204])
def test_any_success_status_is_healthy(code):
    # A 204 used to fall through both branches and return None, which then
    # crashed the dashboard page on status["color"].
    health = _health_module(code)
    result = asyncio.run(health.check_service_health(CONFIG))
    assert result is not None and "Healthy" in result["status"]


def test_an_error_status_is_reported_not_raised():
    health = _health_module(503)
    result = asyncio.run(health.check_service_health(CONFIG))
    assert "Unreachable" in result["status"]


def test_dashboard_is_not_green_before_the_first_check():
    # With no statuses yet, overall_healthy stayed True and the page said
    # "All Systems Healthy" about nothing.
    health = _health_module(200)
    health.service_statuses.clear()
    page = asyncio.run(health.dashboard())
    assert "All Systems Healthy" not in page
    assert "Waiting for the first check" in page


# ---------------------------------------------------------------------------
# browser_audit
# ---------------------------------------------------------------------------


def _browser_audit():
    stubs = {"playwright": types.ModuleType("playwright"),
             "playwright.sync_api": types.ModuleType("playwright.sync_api")}
    stubs["playwright.sync_api"].TimeoutError = TimeoutError
    stubs["playwright.sync_api"].sync_playwright = lambda: None
    saved = {k: sys.modules.get(k) for k in stubs}
    sys.modules.update(stubs)
    try:
        return _load("browser_audit_c", ROOT / "scripts" / "browser_audit.py")
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def test_only_uses_the_same_numbering_as_the_output_files():
    # --only 1 used to run MATRIX[1] and label it iteration 1, and --only 10
    # raised IndexError, while a full run numbers MATRIX[0] as iteration 1.
    audit = _browser_audit()
    full = audit.select_matrix(None)
    assert [i for i, _ in full] == list(range(1, len(audit.MATRIX) + 1))
    assert audit.select_matrix(1) == [(1, audit.MATRIX[0])]
    assert audit.select_matrix(len(audit.MATRIX)) == [(len(audit.MATRIX), audit.MATRIX[-1])]
    with pytest.raises(SystemExit):
        audit.select_matrix(0)
    with pytest.raises(SystemExit):
        audit.select_matrix(len(audit.MATRIX) + 1)


# ---------------------------------------------------------------------------
# export_web_report._clean
# ---------------------------------------------------------------------------


def test_clean_turns_every_missing_value_into_none():
    export = _load("export_web_report_c", ROOT / "scripts" / "export_web_report.py")
    assert export._clean(float("nan")) is None
    assert export._clean(pd.NA) is None
    assert export._clean(None) is None
    assert export._clean(3) == 3
    assert export._clean(pd.Series([1.5]).iloc[0]) == 1.5
    assert export._clean(pd.Timestamp("2026-01-02")) == "2026-01-02T00:00:00"


# ---------------------------------------------------------------------------
# run_analysis prints must survive a Windows cp1252 console
# ---------------------------------------------------------------------------


def test_run_analysis_runs_on_a_cp1252_console(tmp_path, monkeypatch):
    # The step 4 header held an arrow that cp1252 cannot encode, so the run died
    # with UnicodeEncodeError half way through on a console without UTF-8.
    run_analysis = _load("run_analysis_c", ROOT / "scripts" / "run_analysis.py")
    monkeypatch.setattr(run_analysis.reputation, "build_dashboard",
                        lambda banks: {"available": False})
    monkeypatch.setattr(run_analysis, "context_or_none", lambda *a, **k: None)
    out = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "argv", ["run_analysis.py", "--dataset",
                                      str(ROOT / "data" / "fixtures" / "synthetic_sample.csv"),
                                      "--outdir", str(tmp_path), "--no-strict"])
    assert run_analysis.main() == 0
