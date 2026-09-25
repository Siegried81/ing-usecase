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
