"""Tests for the web backend's own logic (scripts/serve_web.py).

The endpoint functions are called directly rather than through an HTTP client,
so no extra test dependency is needed and no model is ever called.
"""
from __future__ import annotations

import sys
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
