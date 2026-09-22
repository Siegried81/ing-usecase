"""Colour extraction from a page's hero image - the automatic part of
colours_design that IS reachable without a headless browser.

New module. background_luminance here is the hero image's own
luminance as a stand-in for the page background - a real page-background
reading needs a rendered viewport, same limitation as noted in
collection/scraper.py. Documented in the returned dict, not hidden.

Audit finding - this module fetched the hero image with plain
requests.get(), never running assert_can_fetch() first like scraper.py's
_fetch_html() does. robots.txt can allow a page but disallow its /images/ or
/assets/ path, so this was a real bypass of the CLAUDE.md compliance gate.
Fixed by checking the image URL too, inside the existing try/except so a
disallowed image still degrades to "no colours" (ScrapingNotAllowed is an
Exception, caught below) instead of turning a best-effort feature into a hard
crash for the whole row.
"""
from __future__ import annotations

import io

import requests
from PIL import Image

from comparator.collection.compliance import USER_AGENT, assert_can_fetch

REQUEST_TIMEOUT_S = 15

# Must match fixtures.py's ARCHETYPES "brand" hex per bank -
# duplicated rather than imported because fixtures.py mixes in a lot of
# synthetic-only fields this module has no business depending on.
BRAND_COLOURS: dict[str, str] = {
    "ing": "#ff6200", "kbc": "#00aeef", "bnp_paribas_fortis": "#00915a",
    # Was #e94e1b (pre-rebrand red-orange), which made
    # brand_colour_share ~0 for every Argenta row. Sampled off the live
    # capture's own chrome - logo, nav CTAs, checkmarks, form submit.
    "argenta": "#00814d", "crelan": "#009640", "belfius": "#c8102e",
    "revolut": "#0666eb", "n26": "#36a18b", "bunq": "#3394ff",
    # Sourced from each site rather than guessed. vdk from its own
    # logo.svg fills (#E30613 primary), beobank from its declared theme-color
    # (#5F3A99), hellobank from the dominant cyan on its rendered page, which
    # matches the #11BAD5/#4EC1D3 in its CSS.
    "vdk": "#e30613", "hellobank": "#00b4c8", "beobank": "#5f3a99",
    # Sourced from each site. CBC from its own logos-cbc.svg fills
    # (#0097db accent next to a #0d2a50 navy), keytrade from its declared
    # theme-color (#03B3D9), both confirmed against the rendered page.
    "cbc": "#0097db", "keytrade": "#03b3d9",
}
# Euclidean RGB distance below which a pixel counts as "brand colour" - not a
# perceptual colour-distance metric (that would need Lab space), good enough
# to separate "clearly the brand colour" from "clearly something else".
_BRAND_COLOUR_TOLERANCE = 60


def _relative_luminance(r: int, g: int, b: int) -> float:
    # standard sRGB relative luminance, matches the dictionary's
    # background_luminance definition (0 = black, 1 = white).
    def lin(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def extract_colours_from_image(image: "Image.Image", *, bank: str | None = None, n_colours: int = 5) -> dict:
    """Same measurement, on an already-decoded image.

    Split out so the full-page SCREENSHOT can be measured instead of
    the hero image. The dictionary defines these features on `source: screenshot`,
    and measuring the hero photo was giving brand_colour_share = 0.0 for KBC and
    Revolut and null for Belfius - a bank's brand colour lives in its buttons,
    headers and rules, not necessarily in the lifestyle photo at the top. That
    was a measurement artefact reported as a property of those banks, and it is
    the same class of mistake as the shadow-DOM one: we were looking at the
    wrong part of the page.

    Reachable only with a rendered page, which is why it could not be done when
    this module was written.
    """
    return _measure(image, bank=bank, n_colours=n_colours)


def extract_colours(image_url: str | None, *, bank: str | None = None, n_colours: int = 5) -> dict:
    """Dominant palette + derived brand/luminance fields from one image.
    Returns nulls (never raises) if the image can't be fetched or decoded -
    one bad image must not crash the whole page's row.

    `bank` is now required to get a real brand_colour_share. FIXED
    a bug where this returned the share of whatever colour happened to be most
    frequent, mislabelled as "brand" - verified a solid BLUE test image scored
    brand_colour_share=1.0 for ING (orange). Without a known bank, the honest
    answer is None, not a number that means something else.
    """
    empty = {
        "dominant_colour_hex": None, "palette_hex": [], "brand_colour_share": None,
        "background_luminance": None, "accent_colour_count": None,
    }
    if not image_url:
        return empty
    try:
        assert_can_fetch(image_url)  # Compliance gate, must run before every fetch
        response = requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_S)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception:  # noqa: BLE001 - best-effort feature, never fatal (incl. robots disallow)
        return empty

    return _measure(img, bank=bank, n_colours=n_colours)


def _measure(img: "Image.Image", *, bank: str | None, n_colours: int) -> dict:
    """The measurement itself, on a decoded RGB image."""
    empty = {
        "dominant_colour_hex": None, "palette_hex": [], "brand_colour_share": None,
        "background_luminance": None, "accent_colour_count": None,
    }
    try:
        img = img.convert("RGB")
    except Exception:  # noqa: BLE001
        return empty

    img = img.resize((150, 150))
    quantized = img.quantize(colors=n_colours, method=Image.MEDIANCUT)
    palette = quantized.getpalette()[: n_colours * 3]
    by_count = sorted(quantized.getcolors(), reverse=True)

    hex_colours, rgb_colours = [], []
    for count, idx in by_count[:n_colours]:
        r, g, b = palette[idx * 3: idx * 3 + 3]
        hex_colours.append(f"#{r:02x}{g:02x}{b:02x}")
        rgb_colours.append((count, r, g, b))

    total_pixels = sum(c for c, *_ in rgb_colours) or 1
    mean_luminance = sum(_relative_luminance(r, g, b) * c for c, r, g, b in rgb_colours) / total_pixels

    brand_hex = BRAND_COLOURS.get(bank) if bank else None
    brand_share = None
    if brand_hex:
        br, bg, bb = (int(brand_hex[i: i + 2], 16) for i in (1, 3, 5))
        # Count EVERY pixel, not just the quantised top-n palette.
        # On a hero crop the brand colour is often one of the five dominant
        # colours, so the palette shortcut worked. On a full-page screenshot it
        # never is - a brand accent is a few percent of a mostly-white page - and
        # every bank scored exactly 0.000, which is a property of the method, not
        # of the banks. Scanning all pixels is the measurement the dictionary
        # describes ("share of coloured pixels within tolerance of the brand
        # colour") and it is cheap on a 150x150 thumbnail.
        tolerance_sq = _BRAND_COLOUR_TOLERANCE ** 2
        pixels = list(img.getdata())
        matching = sum(
            1 for r, g, b in pixels
            if (r - br) ** 2 + (g - bg) ** 2 + (b - bb) ** 2 <= tolerance_sq
        )
        brand_share = round(matching / max(len(pixels), 1), 3)

    return {
        "dominant_colour_hex": hex_colours[0] if hex_colours else None,
        "palette_hex": hex_colours,
        "brand_colour_share": brand_share,
        "background_luminance": round(mean_luminance, 3),
        "accent_colour_count": max(0, len(hex_colours) - 1),
    }
