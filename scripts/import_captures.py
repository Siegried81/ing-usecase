#!/usr/bin/env python3
"""Import manually saved page captures into the dataset.

    python3 scripts/import_captures.py --dir <folder> --merge-with data/processed/campaigns.csv

Three banks (BNP, Revolut, ING x3) fail live fetch even from a residential
machine, so the pages were saved from a normal browser instead.
run_collection.py only has a live path; this is the other one.

WHY THIS IS COMPLIANT, written down rather than assumed. A person opened a
public page in an ordinary browser and saved it. That is normal use of a public
website, not automation getting past a control: the pages are exactly what any
visitor is served. It matters most for BNP, whose edge declines our automated
traffic - we are not defeating that, we are using a copy a human was lawfully
shown.

It still does NOT take robots.txt on trust. The five paths were checked by
hand, and this script re-checks each recovered URL anyway, because "we checked
earlier" is the kind of assumption that rots. A disallowed path is skipped with
a message, same as the live path (LC-01).

Layout expected:

    <dir>/<bank>/<product_family>_<language>_<nn>.html
    <dir>/<bank>/<product_family>_<language>_<nn>.png      (optional screenshot)

The source URL is recovered from the browser's own "saved from url" comment, or
the page's canonical link - no hand-written manifest to drift out of date.
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import warnings
from datetime import UTC, datetime
from pathlib import Path

import _bootstrap  # noqa: F401
import pandas as pd

from comparator import load_dictionary
from comparator.banks import category_for
from comparator.collection.compliance import ScrapingNotAllowed, assert_can_fetch
from comparator.collection.llm_extractor import (
    LLMExtractionError,
    extract_model_assisted_with_provenance,
)
from comparator.collection.quality import assess_capture
from comparator.collection.render import VIEWPORT_HEIGHT
from comparator.collection.scraper import extract, flatten_declarative_shadow_roots
from comparator.collection.visual_features import extract_colours_from_image
from comparator.derive import recompute_derived
from comparator.schema import validate, write_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# <product_family>_<language>_<nn>
NAME_RE = re.compile(r"^(?P<family>[a-z_]+)_(?P<language>nl|fr|en)_(?P<index>\d+)$")
MOTW_RE = re.compile(r"saved from url=\(\d+\)(\S+)")


def recover_url(html: str) -> str | None:
    """The browser records where a saved page came from; so does the page itself."""
    motw = MOTW_RE.search(html[:2000])
    if motw:
        return motw.group(1).strip()
    canonical = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html, re.I)
    return canonical.group(1).strip() if canonical else None


def import_one(path: Path, bank: str, *, raw_dir: Path) -> dict | None:
    match = NAME_RE.match(path.stem)
    if not match:
        logger.warning("skipping %s: filename is not <product_family>_<language>_<nn>", path.name)
        return None
    family, language, index = match["family"], match["language"], int(match["index"])
    page_id = f"{bank}_{family}_{language}_{index:02d}"

    html = path.read_text(encoding="utf-8", errors="ignore")
    url = recover_url(html)
    if not url:
        logger.warning("skipping %s: no source URL in the saved file", page_id)
        return None

    # Re-check, do not assume. LC-01.
    try:
        assert_can_fetch(url)
    except ScrapingNotAllowed as exc:
        logger.warning("skipping %s: %s", page_id, exc)
        return None
    except Exception as exc:  # noqa: BLE001 - robots unreadable -> fail closed
        logger.warning("skipping %s: could not verify robots.txt (%s)", page_id, exc)
        return None

    # Only the count is needed here: extract() flattens the HTML itself.
    _, shadow_hosts = flatten_declarative_shadow_roots(html)
    features = extract(html, language=language, page_url=url)

    # Store the capture alongside the live ones so re-extraction needs no re-fetch.
    bank_dir = raw_dir / bank
    bank_dir.mkdir(parents=True, exist_ok=True)
    html_path = bank_dir / f"{family}_{language}_{index:02d}.html"
    html_path.write_text(html, encoding="utf-8")

    shot_path = path.with_suffix(".png")
    stored_shot = None
    colours: dict = {}
    if shot_path.is_file():
        stored_shot = bank_dir / f"{family}_{language}_{index:02d}.png"
        shutil.copyfile(shot_path, stored_shot)
        try:
            from PIL import Image

            # Same first-screen basis as the live path, or background_luminance
            # would measure the white body copy of a long page.
            colours = extract_colours_from_image(
                Image.open(stored_shot), bank=bank, first_screen_px=VIEWPORT_HEIGHT
            )
        except Exception as exc:  # noqa: BLE001 - best effort
            logger.warning("colour extraction failed for %s: %s", page_id, exc)

    try:
        model_fields, extraction_model = extract_model_assisted_with_provenance(
            features.get("_page_text", ""),
            image_count=features["image_count"],
            has_animation=features["has_animation"],
            product_family=family,
        )
    except LLMExtractionError as exc:
        logger.error("model-assisted extraction failed for %s: %s", page_id, exc)
        model_fields, extraction_model = None, None

    row = {
        "page_id": page_id, "bank": bank, "bank_category": category_for(bank),
        "product_family": family, "language": language,
        "page_role": "campaign_landing", "url": url,
        "collection_method": "manual_capture",
        # No fetch of our own, so no status of our own. Blank is the honest value:
        # writing 200 would claim a successful request nobody made.
        "http_status": None,
        "robots_allowed": True,
        # Microsecond precision, matching the live path - two formats in one
        # column is what broke captured_at parsing in the first place.
        "captured_at": datetime.fromtimestamp(
            path.stat().st_mtime, tz=UTC
        ).isoformat(timespec="microseconds"),
        "snapshot_html_path": str(html_path),
        "screenshot_path": str(stored_shot) if stored_shot else None,
        "data_source": "real",
        "extraction_model": extraction_model,
        "shadow_hosts_flattened": shadow_hosts,
        **{k: v for k, v in features.items() if not k.startswith("_")},
        **colours,
    }
    if model_fields:
        row.update(model_fields.model_dump())

    quality = assess_capture(row, features.get("_page_text", ""))
    row["capture_quality"] = quality.verdict
    row["capture_quality_note"] = quality.note()
    if quality.verdict != "ok":
        logger.warning("%s capture is %s: %s", page_id, quality.verdict, quality.note())
    else:
        logger.info("imported %s (%s words, %s shadow roots flattened)",
                    page_id, row["word_count"], shadow_hosts)
    return row


def merge_with_existing(imported: pd.DataFrame, existing: pd.DataFrame) -> pd.DataFrame:
    """Fold manual captures into an existing dataset.

    A live capture that worked is kept: it has an HTTP status, a pipeline
    timestamp, and nobody's browser session in it. A manual capture replaces
    a same-page row only when the live one is not "ok". A dataset with no
    capture_quality column predates the quality check, so every row counts as ok.
    """
    if "capture_quality" in existing.columns:
        usable_live = existing.loc[existing["capture_quality"] == "ok", "page_id"].tolist()
    else:
        usable_live = existing["page_id"].tolist()
    replaced = imported[imported["page_id"].isin(existing["page_id"])]["page_id"].tolist()
    keep = imported[~imported["page_id"].isin(usable_live)]
    dropped = sorted(set(imported["page_id"]) - set(keep["page_id"]))
    if dropped:
        logger.info("keeping the live capture for %s (it worked)", ", ".join(dropped))
    surviving = existing[~existing["page_id"].isin(keep["page_id"])]
    # The two frames legitimately differ (a manual capture has no http_status, a
    # live one has no importer fields), so one side contributes all-NA columns
    # and pandas warns it will infer their dtype differently in a future release.
    # Casting those columns to object makes the result explicit, and the column
    # is filled from the other frame anyway.
    columns = list(dict.fromkeys([*surviving.columns, *keep.columns]))
    aligned = []
    for frame in (f for f in (surviving, keep) if not f.empty):
        frame = frame.reindex(columns=columns)
        for column in columns:
            if frame[column].isna().all():
                frame[column] = frame[column].astype("object")
        aligned.append(frame)
    # Scoped narrowly so a real dtype problem elsewhere still surfaces.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=FutureWarning,
            message=".*empty or all-NA entries is deprecated.*",
        )
        combined = (pd.concat(aligned, ignore_index=True) if aligned
                    else surviving.reindex(columns=columns))
    logger.info("merged: %d existing + %d imported -> %d row(s); %d replaced",
                len(existing), len(keep), len(combined),
                len([p for p in replaced if p in set(keep["page_id"])]))
    return combined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, required=True, help="folder of <bank>/<page>.html captures")
    parser.add_argument("--out", type=Path, default=Path("data/processed/campaigns.csv"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--merge-with", type=Path, default=None,
                        help="existing dataset; a manual capture replaces a same-page live row "
                             "only when the live one is unusable")
    args = parser.parse_args()

    fd = load_dictionary()
    rows = []
    for bank_dir in sorted(p for p in args.dir.iterdir() if p.is_dir()):
        for html_path in sorted(bank_dir.glob("*.html")):
            row = import_one(html_path, bank_dir.name, raw_dir=args.raw_dir)
            if row:
                rows.append(row)

    if not rows:
        logger.error("nothing imported")
        return 1
    imported = pd.DataFrame(rows)

    if args.merge_with and args.merge_with.is_file():
        combined = merge_with_existing(imported, pd.read_csv(args.merge_with))
    else:
        combined = imported

    combined = recompute_derived(combined, fd)
    write_dataset(combined, args.out, fd)
    print()
    print(validate(combined, fd, tier="core").render())
    print(f"\nwrote {len(combined)} row(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
