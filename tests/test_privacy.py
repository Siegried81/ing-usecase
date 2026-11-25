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


def test_both_uis_link_the_privacy_notice():
    """GDPR Art. 12(1): the notice one click away from every page. The
    Streamlit sidebar and the React footer are on every page, and they must
    point at the same file.
    """
    import re

    streamlit_src = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    url = re.search(r'^PRIVACY_URL = "([^"]+)"', streamlit_src, re.M).group(1)
    assert url.endswith("/PRIVACY.md")
    assert "st.sidebar.markdown(f\"[Privacy notice]({PRIVACY_URL})\")" in streamlit_src
    assert f'href="{url}"' in (ROOT / "web" / "src" / "App.tsx").read_text(encoding="utf-8")


def test_the_notice_covers_what_art_13_asks_for():
    notice = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
    for heading in ("## Who is responsible", "## Why, and on what basis", "## Your rights"):
        assert heading in notice
    assert "Art. 6(1)(f)" in notice
    assert "Data Protection Authority" in notice
