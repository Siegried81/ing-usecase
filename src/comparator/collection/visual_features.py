"""Colour extraction from a page's hero image - the automatic part of
colours_design that IS reachable without a headless browser.

sieg 14/09, new module. background_luminance here is the hero image's own
luminance as a stand-in for the page background - a real page-background
reading needs a rendered viewport, same limitation as noted in
collection/scraper.py. Documented in the returned dict, not hidden.
"""
from __future__ import annotations

import io

import requests
from PIL import Image

from comparator.collection.compliance import USER_AGENT

REQUEST_TIMEOUT_S = 15

# sieg 15/09: must match fixtures.py's ARCHETYPES "brand" hex per bank -
# duplicated rather than imported because fixtures.py mixes in a lot of
# synthetic-only fields this module has no business depending on.
BRAND_COLOURS: dict[str, str] = {
    "ing": "#ff6200", "kbc": "#00aeef", "bnp_paribas_fortis": "#00915a",
    "argenta": "#e94e1b", "crelan": "#009640", "belfius": "#c8102e",
    "revolut": "#0666eb", "n26": "#36a18b", "bunq": "#3394ff",
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


def extract_colours(image_url: str | None, *, bank: str | None = None, n_colours: int = 5) -> dict:
    """Dominant palette + derived brand/luminance fields from one image.
    Returns nulls (never raises) if the image can't be fetched or decoded -
    one bad image must not crash the whole page's row.

    sieg 15/09: `bank` is now required to get a real brand_colour_share. FIXED
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
        response = requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_S)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception:  # noqa: BLE001 - best-effort feature, never fatal
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
        matching = sum(
            c for c, r, g, b in rgb_colours
            if ((r - br) ** 2 + (g - bg) ** 2 + (b - bb) ** 2) ** 0.5 <= _BRAND_COLOUR_TOLERANCE
        )
        brand_share = round(matching / total_pixels, 3)

    return {
        "dominant_colour_hex": hex_colours[0] if hex_colours else None,
        "palette_hex": hex_colours,
        "brand_colour_share": brand_share,
        "background_luminance": round(mean_luminance, 3),
        "accent_colour_count": max(0, len(hex_colours) - 1),
    }
