"""Privacy settings and the privacy notice, pinned to the code they describe.

PRIVACY.md lists every outside service that receives data. A provider added to
the code without a line in the notice would make the notice wrong without
anyone noticing, so the LLM provider list is checked against it here.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

from comparator.collection import llm_extractor

ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_does_not_send_visitor_usage_stats():
    """Streamlit defaults to sending usage statistics from each visitor's
    browser. The dashboard is public on Render, so it is switched off in the
    project config, which the Docker image copies with the rest of the repo.
    """
    config = ROOT / ".streamlit" / "config.toml"
    settings = tomllib.loads(config.read_text(encoding="utf-8"))
    assert settings["browser"]["gatherUsageStats"] is False


def test_the_privacy_notice_names_every_llm_provider():
    notice = (ROOT / "PRIVACY.md").read_text(encoding="utf-8").lower()
    providers = [name for name, *_ in llm_extractor._PROVIDERS] + ["ollama"]
    missing = [name for name in providers if name not in notice]
    assert not missing, f"PRIVACY.md does not mention: {missing}"


def test_the_readme_links_the_privacy_notice():
    assert "(PRIVACY.md)" in (ROOT / "README.md").read_text(encoding="utf-8")
