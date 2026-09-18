"""Headless render path - the five features a static fetch can never produce.

steph 15/09, new module. Siegried's call, and he is right that it is the last
real gap in collection. Confirmed before building it: `page_height_px` is core,
required AND not nullable, so `run_collection.py` does not merely degrade on
real rows today - strict validation FAILS and the run aborts.

The quieter problem is `total_image_area_ratio`. It is nullable, so it passes
validation as a blank and says nothing - but it is currently the STRONGEST
separator between traditional banks and challengers in the analysis. Collecting
real pages without it would silently remove the best evidence the comparison
has, and nobody would see an error.

WHAT IS MEASURED HERE, and how honestly:

  page_height_px            full scroll height at a FIXED viewport. Exact.
  hero_image_area_ratio     largest image intersecting the first viewport,
                            as a share of the viewport. Exact geometry.
  total_image_area_ratio    summed image boxes over the full page area.
                            Overlapping images are counted twice - capped at 1.0.
  above_fold_element_count  interactive/content elements intersecting the
                            first viewport. Heuristic in what counts as an
                            "element", exact in what counts as visible.
  cta_contrast_ratio        WCAG 2.x contrast between the primary CTA's text
                            and its own background colour. Exact formula, but
                            a CTA sitting on an image gets its declared
                            background, which may not be what a reader sees.

THE VIEWPORT IS PART OF THE MEASUREMENT. Every capture must use the same one or
page_height_px and both area ratios are not comparable across banks - the
feature dictionary says so in page_height_px's own notes. It is a module
constant, not an argument, so it cannot drift per call site.

SHADOW DOM. steph 16/09: ING's site is built from web components, and its page
content lives inside shadow roots. `page.content()` serialises the LIGHT DOM
only, so the first real collection saw 16 words (the <title>, twice) on a page
that actually carries 1,745 words and 51 images. It looked like a failed render;
it was a blind extractor. After measuring and screenshotting, this module
flattens every shadow root into the light DOM so the existing BeautifulSoup
extraction sees the whole page. Nothing else downstream had to change.

HTTP STATUS. A 503 still renders a page - BNP's whole site was serving a
maintenance notice with status 503 and we recorded it as a normal capture. The
status is now returned and carried on the row.

Compliance: the robots.txt gate runs BEFORE navigation, exactly as in the static
path. A headless browser is still a fetch (LC-01, LC-04). sieg 17/09: also
gates every SAME-ORIGIN sub-resource the page then loads (see
_blocks_same_origin_asset) - third-party assets are left alone on purpose,
see that function's docstring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from comparator.collection.compliance import USER_AGENT, assert_can_fetch, check_robots

logger = logging.getLogger(__name__)

# Fixed for every capture - see module docstring.
VIEWPORT_WIDTH = 1440
VIEWPORT_HEIGHT = 900
NAV_TIMEOUT_MS = 30_000
# Let lazy-loaded imagery and web fonts settle before measuring.
SETTLE_MS = 1_500
# Ignore tracking pixels and icon sprites when measuring imagery.
MIN_IMAGE_EDGE_PX = 32


# steph 16/09: a 503 is sometimes genuinely transient. Retrying costs one extra
# request and recovers a real outage without anyone re-running the pipeline by
# hand. It does NOT get past BNP - see the note in run_collection.py - but it is
# the right behaviour regardless of who is down.
RETRY_STATUSES = (429, 500, 502, 503, 504)
RETRY_BACKOFF_S = (2, 8)


class RenderUnavailable(RuntimeError):
    """Playwright or its browser binary is not installed.

    Deliberately distinct from a page error: 'this machine cannot render' is a
    setup problem for the operator, not a property of the page being collected.
    """


@dataclass
class RenderResult:
    html: str
    screenshot: bytes
    features: dict
    http_status: int | None = None
    shadow_hosts: int = 0


# Inline every shadow root into its host, so the serialised HTML contains the
# content a reader actually sees. Runs AFTER the screenshot and the geometry
# measurement, because it rewrites the DOM.
_FLATTEN_JS = """
() => {
  let hosts = 0;
  const flatten = (root) => {
    // Deepest first, so a nested host is already flattened when its parent is read.
    for (const el of [...root.querySelectorAll('*')]) {
      if (el.shadowRoot) {
        flatten(el.shadowRoot);
        const html = el.shadowRoot.innerHTML;
        if (html && html.trim()) {
          const holder = document.createElement('div');
          holder.setAttribute('data-shadow-host', el.tagName.toLowerCase());
          holder.innerHTML = html;
          el.appendChild(holder);
          hosts++;
        }
      }
    }
  };
  flatten(document);
  return hosts;
}
"""

# JavaScript runs in the page: geometry has to be read where the layout lives.
_MEASURE_JS = """
(minEdge) => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const pageH = Math.max(
    document.body ? document.body.scrollHeight : 0,
    document.documentElement.scrollHeight
  );
  const pageArea = vw * pageH;

  const visible = (el) => {
    const s = getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity || '1') > 0.01;
  };

  // steph 16/09: walk shadow roots too - on a web-component site every image
  // lives inside one, and querySelectorAll on the document finds none of them.
  const deep = (selector) => {
    const found = [];
    const walk = (root) => {
      for (const el of root.querySelectorAll(selector)) found.push(el);
      for (const el of root.querySelectorAll('*')) if (el.shadowRoot) walk(el.shadowRoot);
    };
    walk(document);
    return found;
  };

  let totalImageArea = 0, heroArea = 0;
  for (const img of deep('img, picture, video')) {
    if (!visible(img)) continue;
    const r = img.getBoundingClientRect();
    if (r.width < minEdge || r.height < minEdge) continue;
    totalImageArea += r.width * r.height;
    const topOffset = r.top + window.scrollY;
    if (topOffset < vh) heroArea = Math.max(heroArea, r.width * r.height);
  }

  let aboveFold = 0;
  for (const el of deep('a, button, input, select, h1, h2, h3, p, img, video, form')) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.bottom > 0 && r.top < vh && r.width > 0 && r.height > 0) aboveFold++;
  }

  // Primary CTA: first link/button whose label reads like a call to action.
  const CTA = ['discover','open','apply','get started','sign up','learn more',
               'decouvrir','découvrir','ouvrir','demander','en savoir plus',
               'ontdek','openen','aanvragen','meer weten'];
  let ctaColours = null;
  for (const el of deep('a, button')) {
    if (!visible(el)) continue;
    const label = (el.textContent || '').trim().toLowerCase();
    if (!label || !CTA.some(k => label.includes(k))) continue;
    const s = getComputedStyle(el);
    let bg = s.backgroundColor, node = el;
    // Walk up while the background is transparent - that is what a reader sees.
    while (node && (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent')) {
      node = node.parentElement;
      if (!node) break;
      bg = getComputedStyle(node).backgroundColor;
    }
    ctaColours = { fg: s.color, bg: bg || 'rgb(255, 255, 255)' };
    break;
  }

  return {
    page_height_px: Math.round(pageH),
    viewport: [vw, vh],
    page_area: pageArea,
    total_image_area: totalImageArea,
    hero_image_area: heroArea,
    above_fold_element_count: aboveFold,
    cta_colours: ctaColours,
  };
}
"""


def _parse_css_colour(value: str | None) -> tuple[float, float, float] | None:
    """Accept the rgb()/rgba() forms getComputedStyle actually returns."""
    if not value:
        return None
    text = value.strip().lower()
    if not text.startswith("rgb"):
        return None
    inner = text[text.find("(") + 1: text.find(")")]
    parts = [p.strip() for p in inner.replace("/", ",").split(",") if p.strip()]
    if len(parts) < 3:
        return None
    try:
        return tuple(float(p) for p in parts[:3])  # type: ignore[return-value]
    except ValueError:
        return None


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG 2.x relative luminance."""
    channels = []
    for raw in rgb:
        c = raw / 255.0
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(foreground: str | None, background: str | None) -> float | None:
    """WCAG contrast ratio between two CSS colours, 1.0 to 21.0."""
    fg, bg = _parse_css_colour(foreground), _parse_css_colour(background)
    if fg is None or bg is None:
        return None
    l1, l2 = sorted((_relative_luminance(fg), _relative_luminance(bg)), reverse=True)
    return round((l1 + 0.05) / (l2 + 0.05), 2)


def _features_from_measurement(raw: dict) -> dict:
    page_area = raw.get("page_area") or 0
    vw, vh = raw.get("viewport", [VIEWPORT_WIDTH, VIEWPORT_HEIGHT])
    viewport_area = (vw or VIEWPORT_WIDTH) * (vh or VIEWPORT_HEIGHT)
    cta = raw.get("cta_colours") or {}

    def ratio(numerator: float, denominator: float) -> float | None:
        if not denominator:
            return None
        # Overlapping boxes are double-counted; a ratio above 1 is meaningless.
        return round(min(1.0, numerator / denominator), 3)

    return {
        "page_height_px": raw.get("page_height_px"),
        "total_image_area_ratio": ratio(raw.get("total_image_area", 0), page_area),
        "hero_image_area_ratio": ratio(raw.get("hero_image_area", 0), viewport_area),
        "above_fold_element_count": raw.get("above_fold_element_count"),
        "cta_contrast_ratio": contrast_ratio(cta.get("fg"), cta.get("bg")),
    }


# sieg 17/09, audit finding (MEDIUM). assert_can_fetch(url) only gated the top-
# level navigation - every sub-resource page.goto() pulls in (images, scripts,
# fonts, XHR) loaded with no per-URL robots check at all, even though
# visual_features.py was patched (15/09) to add exactly this check for a
# single image fetch. A site whose robots.txt allows the page path but
# disallows e.g. /api/ would still have it fetched during render.
#
# Scoped to SAME-ORIGIN requests only, deliberately: third-party CDN/font/
# analytics domains are not what LC-01/LC-04 is about (their robots.txt says
# nothing about us, and most sites don't expect a browser to consult it per
# asset), and blocking them would corrupt the very geometry this module
# measures (page_height_px, image ratios) rather than enforce compliance.
# check_robots() is cache-per-domain (compliance.py), so after the initial
# assert_can_fetch(url) call this adds no extra network round-trip for the
# page's own domain.
def _blocks_same_origin_asset(request_url: str, page_origin: str) -> bool:
    if urlparse(request_url).netloc != page_origin:
        return False
    return not check_robots(request_url).allowed


def render(url: str, *, screenshot_path: str | Path | None = None) -> RenderResult:
    """Render one page in a fixed viewport and measure what needs a browser.

    Raises ScrapingNotAllowed if robots.txt disallows it - the gate runs before
    navigation, not after.
    """
    assert_can_fetch(url)
    # sieg 17/09, audit finding (HIGH). This used to be a fixed value computed
    # once from the pre-navigation URL, which made _blocks_same_origin_asset a
    # silent no-op across any redirect that changes host - e.g. n26.com (a
    # real target in collection_targets.yaml) redirecting to www.n26.com would
    # make every one of the ACTUAL page's sub-resources compare as
    # "cross-origin" and skip the robots check entirely, reverting to the
    # pre-fix behaviour. Tracked dynamically below instead, via
    # page.on("framenavigated"), which fires once the main frame's URL is
    # actually committed - i.e. after redirects resolve and before the
    # resulting document's own sub-resources start loading.
    page_origin = urlparse(url).netloc

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - environment, not logic
        raise RenderUnavailable(
            "playwright is not installed. `pip install playwright` then "
            "`python3 -m playwright install chromium`."
        ) from exc

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(
                    viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
                    user_agent=USER_AGENT,
                )
                # sieg 17/09: gate same-origin sub-resources too - see
                # _blocks_same_origin_asset() above. Registered once; it stays
                # in effect across the retry re-navigation below.
                def _track_origin(frame) -> None:
                    # sieg 17/09, audit finding (HIGH): keep page_origin in
                    # sync with whatever host the browser actually committed
                    # to, so a host-changing redirect doesn't blind the gate.
                    nonlocal page_origin
                    if frame == page.main_frame:
                        page_origin = urlparse(frame.url).netloc

                page.on("framenavigated", _track_origin)
                page.route(
                    "**/*",
                    lambda route: route.abort()
                    if _blocks_same_origin_asset(route.request.url, page_origin)
                    else route.continue_(),
                )
                response = page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="networkidle")
                status = response.status if response else None

                # Polite retry on a server-side status, backing off between tries.
                for delay in RETRY_BACKOFF_S:
                    if status not in RETRY_STATUSES:
                        break
                    logger.info("HTTP %s from %s - retrying in %ss", status, url, delay)
                    page.wait_for_timeout(delay * 1000)
                    response = page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="networkidle")
                    status = response.status if response else None

                page.wait_for_timeout(SETTLE_MS)

                # Order matters: measure and screenshot the page as rendered,
                # THEN rewrite the DOM to expose shadow content for extraction.
                measurement = page.evaluate(_MEASURE_JS, MIN_IMAGE_EDGE_PX)
                shot = page.screenshot(full_page=True)
                hosts = page.evaluate(_FLATTEN_JS)
                html = page.content()
            finally:
                browser.close()
    except Exception as exc:
        message = str(exc)
        if "Executable doesn't exist" in message or "playwright install" in message:
            raise RenderUnavailable(
                "playwright is installed but its browser is not. Run "
                "`python3 -m playwright install chromium`."
            ) from exc
        raise

    if screenshot_path:
        path = Path(screenshot_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(shot)

    if hosts:
        logger.info("flattened %d shadow host(s) into the HTML for %s", hosts, url)

    return RenderResult(
        html=html,
        screenshot=shot,
        features=_features_from_measurement(measurement),
        http_status=status,
        shadow_hosts=hosts,
    )


def is_available() -> bool:
    """Whether this machine can render, without raising. For a preflight check."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False
