"""Tests for the web backend's own logic (scripts/serve_web.py).

The endpoint functions are called directly rather than through an HTTP client,
so no extra test dependency is needed and no model is ever called.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import serve_web  # noqa: E402
from fastapi import HTTPException  # noqa: E402


def test_a_missing_report_does_not_leave_the_site_stuck_generating(monkeypatch, tmp_path):
    # the 503 used to fire after the state was set to
    # "generating", and nothing reset it - every later request got a 409.
    monkeypatch.setattr(serve_web, "REPORT_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(serve_web, "_load_recommendations", lambda: {
        "recommendations": [{"id": "R1", "title": "t", "priority": "high",
                             "finding": "f", "recommendation": "r"}],
    })
    monkeypatch.setitem(serve_web._site_state, "status", "idle")

    with pytest.raises(HTTPException) as err:
        serve_web.post_site_generate(serve_web.SiteRequest())
    assert err.value.status_code == 503
    assert serve_web._site_state["status"] == "idle"


def test_a_download_name_cannot_leave_outputs():
    with pytest.raises(HTTPException) as err:
        serve_web.get_download("../README.md")
    assert err.value.status_code == 400


def test_the_ui_mount_never_shadows_the_api():
    """A StaticFiles mount at the root matches everything under it, and
    Starlette matches routes in registration order. Declared before the API it
    would swallow every /api call.

    Matched on the mount's NAME, not its path: Starlette normalises a root
    mount to "", so looking for "/" skips this test instead of running it.
    """
    names = [getattr(r, "name", None) for r in serve_web.app.routes]
    paths = [getattr(r, "path", "") for r in serve_web.app.routes]
    if "ui" not in names:
        pytest.skip("web/dist not built in this tree")

    root = names.index("ui")
    assert paths[root] in ("", "/"), "the UI is not mounted at the root"

    api = [i for i, p in enumerate(paths) if p.startswith("/api")]
    assert api, "no /api routes found - this test would be checking nothing"
    assert max(api) < root, "the UI mount is registered before an /api route"
    assert names.index("site") < root, "the UI mount is registered before /site"


def test_the_ui_mount_stays_optional():
    """In development the UI is served by Vite on :5173 and web/dist does not
    exist. An unbuilt bundle must not be a startup failure, so the mount stays
    behind an is_dir() guard rather than being registered unconditionally.
    """
    src = Path(serve_web.__file__).read_text(encoding="utf-8")
    assert "if UI_DIR.is_dir():" in src, "the UI mount must stay conditional"


def test_no_generated_site_is_reported_cleanly(monkeypatch, tmp_path):
    # The demo site is not versioned: a fresh clone has no pages, and a stray
    # manifest must not pretend otherwise.
    monkeypatch.setattr(serve_web, "SITE_DIR", tmp_path)
    (tmp_path / "manifest.json").write_text('{"pages": []}', encoding="utf-8")
    monkeypatch.setitem(serve_web._site_state, "status", "idle")
    monkeypatch.setitem(serve_web._site_state, "manifest", None)

    assert serve_web.health()["site"] is False
    status = serve_web.get_site_status()
    assert status["ready"] is False
    assert status["site_url"] is None
    assert status["manifest"] is None
    assert status["status"] == "idle"


# ---------------------------------------------------------------------------
# The two POST routes spend LLM credit. With API_TOKEN set they need the
# X-API-Token header; without it (local development) nothing changes.
# ---------------------------------------------------------------------------

LLM_ROUTES = {"/api/recommendations/generate", "/api/site/generate"}


def test_a_configured_token_is_required(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "s3cret")
    for sent in (None, "", "wrong"):
        with pytest.raises(HTTPException) as err:
            serve_web.require_token(sent)
        assert err.value.status_code == 401
    assert serve_web.require_token("s3cret") is None


def test_no_configured_token_keeps_local_use_open(monkeypatch):
    monkeypatch.delenv("API_TOKEN", raising=False)
    assert serve_web.require_token(None) is None


def test_only_the_llm_routes_carry_the_token_check():
    guarded = set()
    for route in serve_web.app.routes:
        dependant = getattr(route, "dependant", None)
        if dependant and any(d.call is serve_web.require_token for d in dependant.dependencies):
            guarded.add(route.path)
    assert guarded == LLM_ROUTES


# ---------------------------------------------------------------------------
# A failed model call is logged in full on the server; the browser only gets a
# generic message, because provider errors can carry URLs, key prefixes or
# local paths.
# ---------------------------------------------------------------------------

LEAKY = "groq 401 for key gsk_abc123 at /home/someone/Users/.env"


def test_a_failed_recommendation_call_does_not_leak_its_detail(monkeypatch):
    def boom(*_args, **_kwargs):
        raise serve_web.LLMExtractionError(LEAKY)

    monkeypatch.setattr(serve_web, "_read_report", lambda: {})
    monkeypatch.setattr(serve_web, "build_recommendations", boom)

    with pytest.raises(HTTPException) as err:
        serve_web.post_recommendations(serve_web.RecommendationRequest())
    assert err.value.status_code == 502
    assert "gsk_abc123" not in err.value.detail
    assert "Users" not in err.value.detail


def test_a_failed_site_run_does_not_leak_its_detail(monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError(LEAKY)

    monkeypatch.setattr(serve_web, "_read_report", lambda: {})
    monkeypatch.setattr(serve_web, "_load_recommendations", lambda: {
        "recommendations": [{"id": "R1", "title": "t", "priority": "high",
                             "finding": "f", "recommendation": "r"}],
    })
    monkeypatch.setattr(serve_web, "generate_site", boom)
    monkeypatch.setitem(serve_web._site_state, "status", "idle")

    serve_web.post_site_generate(serve_web.SiteRequest())
    for thread in threading.enumerate():
        if thread.name == "site-generator":
            thread.join(timeout=5)

    try:
        assert serve_web._site_state["status"] == "error"
        assert "gsk_abc123" not in serve_web._site_state["error"]
        assert "Users" not in serve_web._site_state["error"]
    finally:
        serve_web._site_state.update(status="idle", error=None)
