#!/usr/bin/env python3
"""Collect real campaign pages into a dataset row per the feature dictionary.

New script. Fixed sequential chain per page - compliance check ->
scrape -> visual features -> LLM-assisted features -> assemble -> validate ->
append. One bank failing (blocked by robots.txt, network error, bad LLM
response) is logged and skipped, never stops the rest of the run - same
reasoning as the plan's "chain, not agent" section: predictable steps,
partial failure shouldn't cost the whole batch the night before a deadline.

Usage:
    python3 scripts/run_collection.py --config scripts/collection_targets.yaml

The targets file lists (bank, bank_category, product_family, page_role, url,
language) rows - see the example created alongside this script. This script
does NOT decide which banks/pages to collect; that list is a team decision
(PRD FR-01, "justify your scope"), not something to hardcode here.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
import yaml
from dotenv import load_dotenv

# Load environment variables via python-dotenv.
load_dotenv()

from comparator.collection.compliance import ScrapingNotAllowed
from comparator.collection.quality import assess_capture

# BNP Paribas Fortis - diagnosed, not worked around.
#   robots.txt           200, and no Disallow covers the target path
#   robots.txt itself    200 (static file, different edge config)
#   every other path     503 from server: AkamaiNetStorage, including / and
#                        /sitemap.xml - so the sitemap route (LC-02) is shut too
#   our honest UA        503
#   a browser UA         503, byte-identical (9875 bytes)
#
# Not user-agent-based bot detection: swapping to a browser UA changes nothing.
# Whatever the edge is refusing, it is not the string we send. That leaves
# rotating IPs or residential proxies as the only things that might work, and
# those are exactly what LC-04 forbids ("no bot-detection evasion"). We hold a
# robots.txt allow for this path; we do not hold permission to get past an edge
# that is declining us.
#
# So: no workaround. Retry-with-backoff (collection/render.py) recovers a
# genuinely transient 503 on any site, and BNP re-attempts on every run. If it
# stays down, the honest deliverable is a named gap in D-09, not a bank
# characterised from a maintenance page.
from comparator.collection.llm_extractor import LLMExtractionError, extract_model_assisted_with_provenance
from comparator.collection.scraper import scrape
from comparator.collection.visual_features import extract_colours, extract_colours_from_image
from comparator.dictionary import load_dictionary
from comparator.schema import validate, write_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def collect_one(
    target: dict, page_index: int, *, method: str = "auto", raw_dir: Path = Path("data/raw")
) -> dict | None:
    bank, product_family, language = target["bank"], target["product_family"], target["language"]
    page_id = f"{bank}_{product_family}_{language}_{page_index:02d}"

    # The snapshot IS the reproducibility guarantee (DR-03, DR-06) -
    # feature extraction has to be re-runnable without re-fetching anyone's site.
    # snapshot_html_path is core, required and not nullable, so a row without it
    # fails validation anyway.
    bank_dir = raw_dir / bank
    html_path = bank_dir / f"{product_family}_{language}_{page_index:02d}.html"
    shot_path = bank_dir / f"{product_family}_{language}_{page_index:02d}.png"

    try:
        scraped = scrape(target["url"], language=language, method=method,
                         wait_until=target.get("wait_until", "networkidle"),
                         timeout_ms=target.get("timeout_ms"),
                         screenshot_path=shot_path)
    except ScrapingNotAllowed as exc:
        logger.warning("skipping %s: %s", page_id, exc)
        return None
    except Exception as exc:  # noqa: BLE001 - network/parsing failures shouldn't kill the run
        logger.error("scrape failed for %s: %s", page_id, exc)
        return None

    bank_dir.mkdir(parents=True, exist_ok=True)
    html_path.write_text(scraped["_html"], encoding="utf-8")

    # Measure colour on the RENDERED PAGE when we have one. The
    # dictionary defines these features on source: screenshot, and measuring the
    # hero photo instead gave brand_colour_share = 0.0 for KBC and Revolut and
    # null for Belfius - their brand colour is in buttons and headers, not in the
    # lifestyle photo. The hero image stays the fallback for a static fetch.
    colours = None
    shot = scraped.get("_screenshot")
    if shot:
        try:
            from io import BytesIO

            from PIL import Image

            # Measure background_luminance on the first screen (the capture
            # viewport), not the whole page strip - see
            # visual_features.extract_colours_from_image().
            from comparator.collection.render import VIEWPORT_HEIGHT

            colours = extract_colours_from_image(
                Image.open(BytesIO(shot)), bank=bank, first_screen_px=VIEWPORT_HEIGHT
            )
        except Exception as exc:  # noqa: BLE001 - best-effort, never fatal
            logger.warning("screenshot colour extraction failed for %s: %s", page_id, exc)
    if not colours or colours.get("brand_colour_share") is None:
        colours = extract_colours(scraped.get("_hero_image_url"), bank=bank)

    try:
        model_fields, extraction_model = extract_model_assisted_with_provenance(
            scraped["_page_text"],
            image_count=scraped["image_count"],
            has_animation=scraped["has_animation"],
            product_family=product_family,
        )
    except LLMExtractionError as exc:
        logger.error("model-assisted extraction failed for %s: %s (row kept, those fields null)", page_id, exc)
        model_fields, extraction_model = None, None

    row = {
        "page_id": page_id,
        "bank": bank,
        "bank_category": target["bank_category"],
        "product_family": product_family,
        "page_role": target.get("page_role", "campaign_landing"),
        "url": target["url"],
        "language": language,
        "collection_method": scraped["collection_method"],
        "robots_allowed": scraped["robots_allowed"],
        "captured_at": scraped["captured_at"],
        "snapshot_html_path": str(html_path),
        "screenshot_path": str(shot_path) if shot_path.exists() else None,
        "data_source": "real",
        "extraction_model": extraction_model,
        **{k: v for k, v in scraped.items() if not k.startswith("_")},
        **colours,
    }
    if model_fields:
        row.update(model_fields.model_dump())

    # Judge the capture before it becomes a row. Two of the first
    # six real pages were an empty shell and a maintenance notice; both passed
    # every other check because their numbers were in range.
    quality = assess_capture(row, scraped.get("_page_text", ""))
    row["capture_quality"] = quality.verdict
    row["capture_quality_note"] = quality.note()
    if quality.verdict != "ok":
        logger.warning("%s capture is %s: %s", page_id, quality.verdict, quality.note())
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--method", default="auto", choices=["auto", "headless", "headful", "static"],
        help="auto: render if possible, else static (and say so). headless: require a "
             "browser. static: never launch one - leaves the five geometry features "
             "empty, which fails strict validation.",
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--config", required=True, help="YAML file listing pages to collect")
    parser.add_argument("--out", default="data/processed/real_captures.csv")
    args = parser.parse_args()

    targets = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))["pages"]
    fd = load_dictionary()

    rows = []
    counters: dict[str, int] = {}
    for target in targets:
        counters[target["bank"]] = counters.get(target["bank"], 0) + 1
        # a target may override the run-wide method: some hosts refuse headless
        # clients but serve a real browser (see the headful comment in scraper.py)
        row = collect_one(target, counters[target["bank"]],
                          method=target.get("method", args.method), raw_dir=args.raw_dir)
        if row:
            rows.append(row)

    if not rows:
        logger.error("nothing collected - nothing written")
        sys.exit(1)

    import pandas as pd

    df = pd.DataFrame(rows)
    # Validate WITHOUT raising here - a static_fetch run is expected to be
    # missing the headless-render-only fields (page_height_px,
    # total_image_area_ratio, ...), so a strict core-tier validation fails by
    # design. Report it plainly instead of crashing, so the run shows exactly
    # what is still missing rather than a stack trace.
    report = validate(df, fd, tier="core")
    print(report.render())
    path = write_dataset(df, args.out, fd)
    logger.info("wrote %d row(s) -> %s", len(df), path)
    if not report.ok:
        logger.warning(
            "dataset does NOT pass strict core validation yet - expected until headless "
            "rendering fills page_height_px/total_image_area_ratio/cta_contrast_ratio/"
            "above_fold_element_count (see collection/scraper.py docstring)."
        )


if __name__ == "__main__":
    main()
