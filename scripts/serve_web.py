#!/usr/bin/env python3
"""Backend for the business web UI.

    python3 scripts/serve_web.py            # http://localhost:8000

The UI itself stays a static snapshot of the analysis. This server adds exactly
two things a snapshot cannot hold: the model calls that write recommendations,
and the model calls that turn a chosen subset of those recommendations into a
ten-page ING-styled website. It serves the generated site at /site/.

Design notes, because a demo server that lies is worse than no server:
  * Recommendations and the site are different jobs: recommendations are a
    single ~30s call, the site is ten parallel calls. The site runs in a
    background thread and the UI polls /api/site/status, so a browser refresh
    halfway through does not throw the work away.
  * Both artefacts are written to outputs/ as they complete, and reloaded at
    start-up, so restarting this process does not lose a generated site.
  * Nothing here re-derives a number. Recommendations read report.json; the
    site reads the recommendations. One direction only.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap  # noqa: F401

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from comparator.collection.llm_extractor import LLMExtractionError
from comparator.recommendations import RecommendationSet, build_recommendations, select
from comparator.site_generator import PAGES, generate_site

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "web" / "public" / "report.json"
TRENDS_PATH = REPO_ROOT / "web" / "public" / "trends.json"
SITE_DIR = REPO_ROOT / "outputs" / "generated_site"
RECS_PATH = REPO_ROOT / "outputs" / "web_recommendations.json"

app = FastAPI(title="ING campaign comparator — recommendations and site generation")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_state_lock = threading.Lock()
_site_state: dict = {"status": "idle", "progress": 0, "total": len(PAGES), "page": None,
                     "error": None, "manifest": None}


def _read_report() -> dict:
    if not REPORT_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="No report.json yet. Run: python3 scripts/export_web_report.py",
        )
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def _load_recommendations() -> dict | None:
    if RECS_PATH.is_file():
        return json.loads(RECS_PATH.read_text(encoding="utf-8"))
    return None


def _load_trends() -> dict | None:
    if TRENDS_PATH.is_file():
        return json.loads(TRENDS_PATH.read_text(encoding="utf-8"))
    return None


def _save_recommendations(payload: dict) -> None:
    RECS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_site_manifest() -> dict | None:
    manifest = SITE_DIR / "manifest.json"
    if manifest.is_file():
        return json.loads(manifest.read_text(encoding="utf-8"))
    return None


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "report": REPORT_PATH.is_file(), "site": (SITE_DIR / "index.html").is_file()}


@app.get("/api/recommendations")
def get_recommendations() -> dict:
    saved = _load_recommendations()
    if saved is None:
        return {"available": False, "recommendations": [], "summary": None}
    return {"available": True, **saved}


class RecommendationRequest(BaseModel):
    include_trends: bool = False
    include_reputation: bool = False  # sieg 21/09


@app.post("/api/recommendations/generate")
def post_recommendations(request: RecommendationRequest | None = None) -> dict:
    """One model call over the analysis snapshot. Synchronous; the UI shows a wait state.

    With `include_trends`, the Trends tab snapshot (`web/public/trends.json`) is
    added to the prompt as context. Search interest never becomes evidence of
    performance; the additional recommendations are labelled by `basis`.

    sieg 21/09: `include_reputation` does the same for news headline themes.
    No separate file to load - report.json already carries the reputation
    dashboard - so a missing signal surfaces as the same LLMExtractionError ->
    502 path build_recommendations already uses for trends, rather than a
    second pre-flight 409 check.
    """
    include_trends = bool(request and request.include_trends)
    trends = _load_trends() if include_trends else None
    if include_trends and trends is None:
        raise HTTPException(
            status_code=409,
            detail="No trends data available. Run: python3 scripts/export_web_report.py",
        )
    include_reputation = bool(request and request.include_reputation)
    try:
        result = build_recommendations(
            _read_report(), include_trends=include_trends, trends=trends,
            include_reputation=include_reputation,
        )
    except LLMExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    payload = result.to_dict()
    _save_recommendations(payload)
    return {"available": True, **payload}


class SiteRequest(BaseModel):
    recommendation_ids: list[str] = Field(default_factory=list)
    language: str = "fr"
    # Explained mode: each section that implements a recommendation is rendered
    # with a glowing box and a note saying which one and why.
    explain: bool = False


@app.post("/api/site/generate")
def post_site_generate(request: SiteRequest) -> dict:
    saved = _load_recommendations()
    if saved is None:
        raise HTTPException(status_code=409, detail="Generate recommendations first.")

    full = RecommendationSet.from_dict(saved)
    if request.recommendation_ids:
        chosen = select(full, request.recommendation_ids)
        if not chosen.recommendations:
            raise HTTPException(status_code=400, detail="None of the selected ids exist.")
    else:
        chosen = full

    with _state_lock:
        if _site_state["status"] == "generating":
            raise HTTPException(status_code=409, detail="A site is already being generated.")
        _site_state.update(status="generating", progress=0, total=len(PAGES), page=None,
                           error=None, manifest=None)

    report = _read_report()

    def on_progress(done: int, total: int, slug: str) -> None:
        with _state_lock:
            _site_state.update(progress=done, total=total, page=slug)

    def run() -> None:
        try:
            manifest = generate_site(
                report, chosen, language=request.language, explain=request.explain,
                out_dir=SITE_DIR, on_progress=on_progress,
            )
            with _state_lock:
                _site_state.update(status="ready", manifest=manifest, page=None)
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI verbatim
            with _state_lock:
                _site_state.update(status="error", error=f"{type(exc).__name__}: {exc}")

    threading.Thread(target=run, name="site-generator", daemon=True).start()
    return {"status": "generating", "total": len(PAGES),
            "recommendations": [r.id for r in chosen.recommendations]}


@app.get("/api/site/status")
def get_site_status() -> dict:
    with _state_lock:
        state = dict(_site_state)
    manifest = state.get("manifest") or _load_site_manifest()
    ready = (SITE_DIR / "index.html").is_file()
    status = state["status"]
    if status in ("idle",) and manifest and ready:
        status = "ready"
    return {
        "status": status,
        "progress": state.get("progress", 0),
        "total": state.get("total", 0),
        "page": state.get("page"),
        "error": state.get("error"),
        "ready": ready,
        "manifest": manifest,
        "site_url": "site/index.html" if ready else None,
    }


SITE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/site", StaticFiles(directory=str(SITE_DIR), html=True), name="site")


def main() -> int:
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    print(f"recommendations + site backend on http://{args.host}:{args.port}")
    print(f"  report : {REPORT_PATH}")
    print(f"  site   : {SITE_DIR}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
