"""Tests for the headless render path (steph 15/09).

No test here launches a browser - the pure functions carry the logic worth
testing, and the browser-dependent parts are exercised through mocks so the
suite still runs on a machine with no chromium installed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.collection.compliance import ScrapingNotAllowed  # noqa: E402
from comparator.collection.render import (  # noqa: E402
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
    RenderUnavailable,
    _features_from_measurement,
    _parse_css_colour,
    contrast_ratio,
    render,
)
from comparator.collection.scraper import scrape  # noqa: E402


# --- WCAG contrast -----------------------------------------------------------
@pytest.mark.parametrize(
    "fg,bg,expected",
    [
        ("rgb(255,255,255)", "rgb(0,0,0)", 21.0),   # maximum possible
        ("rgb(0,0,0)", "rgb(255,255,255)", 21.0),   # symmetric
        ("rgb(120,120,120)", "rgb(120,120,120)", 1.0),  # minimum possible
    ],
)
def test_contrast_ratio_against_known_values(fg, bg, expected):
    assert contrast_ratio(fg, bg) == expected


def test_contrast_ratio_is_none_when_a_colour_cannot_be_read():
    assert contrast_ratio("linear-gradient(red, blue)", "rgb(0,0,0)") is None
    assert contrast_ratio(None, "rgb(0,0,0)") is None


def test_parse_css_colour_handles_the_forms_browsers_return():
    assert _parse_css_colour("rgb(255, 98, 0)") == (255.0, 98.0, 0.0)
    assert _parse_css_colour("rgba(255, 98, 0, 0.5)") == (255.0, 98.0, 0.0)
    assert _parse_css_colour("transparent") is None


# --- geometry -> features ----------------------------------------------------
def _measurement(**overrides) -> dict:
    base = dict(
        page_height_px=4000, viewport=[VIEWPORT_WIDTH, VIEWPORT_HEIGHT],
        page_area=VIEWPORT_WIDTH * 4000, total_image_area=1_000_000,
        hero_image_area=500_000, above_fold_element_count=7,
        cta_colours={"fg": "rgb(255,255,255)", "bg": "rgb(255,98,0)"},
    )
    base.update(overrides)
    return base


def test_all_five_missing_features_get_a_value():
    features = _features_from_measurement(_measurement())
    for name in ("page_height_px", "total_image_area_ratio", "hero_image_area_ratio",
                 "above_fold_element_count", "cta_contrast_ratio"):
        assert features[name] is not None, f"{name} is what this module exists to fill"


def test_overlapping_images_cannot_push_a_ratio_above_one():
    """Image boxes are summed, so overlap double-counts. A ratio > 1 is nonsense."""
    features = _features_from_measurement(_measurement(total_image_area=99_000_000))
    assert features["total_image_area_ratio"] == 1.0


def test_a_page_with_no_images_scores_zero_not_none():
    features = _features_from_measurement(_measurement(total_image_area=0, hero_image_area=0))
    assert features["total_image_area_ratio"] == 0.0
    assert features["hero_image_area_ratio"] == 0.0


def test_zero_page_area_does_not_divide_by_zero():
    features = _features_from_measurement(_measurement(page_area=0))
    assert features["total_image_area_ratio"] is None


def test_missing_cta_leaves_contrast_empty_rather_than_guessing():
    features = _features_from_measurement(_measurement(cta_colours=None))
    assert features["cta_contrast_ratio"] is None


# --- compliance --------------------------------------------------------------
def test_robots_gate_runs_before_the_browser_launches():
    """A headless fetch is still a fetch (LC-01, LC-04)."""
    with patch("comparator.collection.render.assert_can_fetch",
               side_effect=ScrapingNotAllowed("disallowed")) as gate:
        with patch("playwright.sync_api.sync_playwright") as browser:
            with pytest.raises(ScrapingNotAllowed):
                render("https://example.invalid/page")
    gate.assert_called_once()
    browser.assert_not_called(), "the browser must never start for a disallowed URL"


# --- method selection --------------------------------------------------------
def test_static_method_never_launches_a_browser():
    with patch("comparator.collection.scraper.render") as renderer:
        with patch("comparator.collection.scraper._fetch_html", return_value="<html><p>x</p></html>"):
            row = scrape("https://example.invalid/p", language="en", method="static")
    renderer.assert_not_called()
    assert row["collection_method"] == "static_fetch"


def test_auto_falls_back_to_static_when_no_browser_is_available():
    with patch("comparator.collection.scraper.render", side_effect=RenderUnavailable("no chromium")):
        with patch("comparator.collection.scraper._fetch_html", return_value="<html><p>x</p></html>"):
            row = scrape("https://example.invalid/p", language="en", method="auto")
    assert row["collection_method"] == "static_fetch"


def test_headless_method_refuses_to_fall_back_silently():
    """If the operator asked for a browser, a quiet downgrade would poison the dataset."""
    with patch("comparator.collection.scraper.render", side_effect=RenderUnavailable("no chromium")):
        with pytest.raises(RenderUnavailable):
            scrape("https://example.invalid/p", language="en", method="headless")


def test_rendered_geometry_overrides_the_static_placeholders():
    from comparator.collection.render import RenderResult

    fake = RenderResult(
        html="<html><body><p>hello world</p><img src='a.png' alt='a'></body></html>",
        screenshot=b"",
        features={"page_height_px": 3210, "total_image_area_ratio": 0.42,
                  "hero_image_area_ratio": 0.31, "above_fold_element_count": 9,
                  "cta_contrast_ratio": 4.7},
    )
    with patch("comparator.collection.scraper.render", return_value=fake):
        row = scrape("https://example.invalid/p", language="en", method="headless")

    assert row["collection_method"] == "headless_render"
    assert row["page_height_px"] == 3210, "the static path hardcodes None here"
    assert row["total_image_area_ratio"] == 0.42
    assert row["word_count"] > 0, "text features still come from the rendered DOM"


def test_unknown_method_is_rejected():
    with pytest.raises(ValueError, match="unknown method"):
        scrape("https://example.invalid/p", language="en", method="turbo")
