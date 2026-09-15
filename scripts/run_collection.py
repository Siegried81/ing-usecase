#!/usr/bin/env python3
"""Collect real campaign pages into a dataset row per the feature dictionary.

sieg 14/09, new script. Fixed sequential chain per page - compliance check ->
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

from comparator.collection.compliance import ScrapingNotAllowed
from comparator.collection.llm_extractor import LLMExtractionError, extract_model_assisted_with_provenance
from comparator.collection.scraper import scrape
from comparator.collection.visual_features import extract_colours
from comparator.dictionary import load_dictionary
from comparator.schema import validate, write_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def collect_one(target: dict, page_index: int) -> dict | None:
    bank, product_family, language = target["bank"], target["product_family"], target["language"]
    page_id = f"{bank}_{product_family}_{language}_{page_index:02d}"

    try:
        scraped = scrape(target["url"], language=language)
    except ScrapingNotAllowed as exc:
        logger.warning("skipping %s: %s", page_id, exc)
        return None
    except Exception as exc:  # noqa: BLE001 - network/parsing failures shouldn't kill the run
        logger.error("scrape failed for %s: %s", page_id, exc)
        return None

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
        "snapshot_html_path": "",  # sieg 14/09: TODO - Dan, write scraped["_html"] to data/raw/ and set this
        "screenshot_path": "",     # TODO - only fillable once headless_render exists
        "data_source": "real",
        "extraction_model": extraction_model,
        **{k: v for k, v in scraped.items() if not k.startswith("_")},
        **colours,
    }
    if model_fields:
        row.update(model_fields.model_dump())
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="YAML file listing pages to collect")
    parser.add_argument("--out", default="data/processed/real_captures.csv")
    args = parser.parse_args()

    targets = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))["pages"]
    fd = load_dictionary()

    rows = []
    counters: dict[str, int] = {}
    for target in targets:
        counters[target["bank"]] = counters.get(target["bank"], 0) + 1
        row = collect_one(target, counters[target["bank"]])
        if row:
            rows.append(row)

    if not rows:
        logger.error("nothing collected - nothing written")
        sys.exit(1)

    import pandas as pd

    df = pd.DataFrame(rows)
    # sieg 14/09: validate WITHOUT raising here - a static_fetch run is
    # expected to be missing the headless-render-only fields (page_height_px,
    # total_image_area_ratio, ...), so a strict core-tier validation WILL
    # fail today. Report it plainly instead of crashing, so Dan can see
    # exactly what's still missing rather than getting a stack trace.
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
