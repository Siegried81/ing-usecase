#!/usr/bin/env python3
"""Step 5 - generate two campaign variants and score them (stretch goal).

    python3 scripts/run_generation.py --dataset data/fixtures/synthetic_sample.csv

steph 15/09. Plan section 4.5 / Appendix B, owner: me. Gated behind the Day 6
freeze in the plan - this is the machinery, run early so it is not improvised
under deadline pressure, NOT a claim that the gate has passed.

Needs DEEPSEEK_API_KEY in the environment (see .env.example). Without it the
script explains what is missing and exits rather than half-running.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd

from comparator import load_dictionary
from comparator.generation import (
    build_brief,
    build_targets,
    evaluate,
    generate,
    guardrails,
    hit_rate,
    pinned_model,
    score,
    to_html,
)
from comparator.schema import read_dataset, write_dataset

DEFAULT_DATASET = Path("data/fixtures/synthetic_sample.csv")
DEFAULT_OUTDIR = Path("outputs/generated")

BANNER = (
    "=" * 78 + "\n"
    "  SYNTHETIC CAMPAIGN - written by a language model, never published.\n"
    "  Hitting the target means the generator followed instructions. It says\n"
    "  NOTHING about whether the campaign would perform better: we have no\n"
    "  performance data at all (PRD 5.2, plan risk P-08).\n"
    + "=" * 78
)


def _header(text: str) -> None:
    print(f"\n{text}\n{'-' * len(text)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--focus", default="ing")
    parser.add_argument("--product", default="term account")
    parser.add_argument("--language", default="en", choices=["en", "nl", "fr"])
    parser.add_argument("--dry-run", action="store_true",
                        help="build and print the briefs without calling the model")
    args = parser.parse_args()

    if not args.dry_run and not os.getenv("DEEPSEEK_API_KEY"):
        print("DEEPSEEK_API_KEY is not set. Copy .env.example to .env and fill it in,\n"
              "or re-run with --dry-run to inspect the briefs without calling a model.")
        return 2

    fd = load_dictionary()
    args.outdir.mkdir(parents=True, exist_ok=True)

    # sieg 15/09: fixed - strict=True made read_dataset() raise BEFORE this
    # function got (df, report) back, so the print(report.render()) below was
    # dead code on any validation failure - the user got a raw traceback
    # instead, the exact thing run_collection.py already avoids on purpose.
    # Not hypothetical: Dan's real captures are still missing the
    # headless-render-only fields, so this WILL fail once someone points
    # --dataset at them instead of the fixture.
    df, report = read_dataset(args.dataset, fd, tier="core", strict=False)
    print(report.render())
    if not report.ok:
        print("\ndataset failed core validation - fix it before generating targets from it.")
        return 1
    if "data_source" in df and (df["data_source"] == "synthetic_fixture").any():
        print("\nNOTE: targets are derived from FIXTURE data, so they are shaped like\n"
              "real targets but are not real ones.")

    _header("Targets, derived from the dataset")
    targets = build_targets(df, fd, focus=args.focus)
    for variant, target in targets.items():
        print(f"\n{variant} - {target.description}")
        for line in target.brief_lines():
            print(f"  {line}")

    generated_rows: list[dict] = []
    for variant, target in targets.items():
        brief = build_brief(df, target, fd, focus=args.focus,
                            product=args.product, language=args.language)

        if args.dry_run:
            _header(f"Brief - {variant} (dry run, no model called)")
            print(brief.to_prompt())
            continue

        _header(f"Generating - {variant}  (model: {pinned_model()})")
        campaign, model_id = generate(brief)
        print(f"  answered by: {model_id}")
        print(f"  headline   : {campaign.headline}")
        print(f"  cta        : {campaign.cta_label}")

        row = score(campaign, variant=variant, bank=args.focus,
                    language=args.language, model_id=model_id,
                    captured_at=pd.Timestamp.now(tz="UTC").isoformat())

        check = guardrails(row)
        print(f"  guardrails : {'PASS' if check.ok else 'FAIL'}")
        for violation in check.violations:
            print(f"    VIOLATION {violation}")

        scorecard = evaluate(row, target)
        print(f"\n  scorecard (hit rate on measured criteria: {hit_rate(scorecard):.0%})")
        print(scorecard.to_string(index=False, columns=["feature", "target", "actual", "result"]))

        (args.outdir / f"{variant}.json").write_text(
            json.dumps(campaign.model_dump(), indent=2), encoding="utf-8")
        (args.outdir / f"{variant}.html").write_text(to_html(campaign), encoding="utf-8")
        scorecard.to_csv(args.outdir / f"{variant}_scorecard.csv", index=False)
        generated_rows.append(row)

    if generated_rows:
        combined = pd.concat([df, pd.DataFrame(generated_rows)], ignore_index=True)
        write_dataset(combined, args.outdir / "dataset_with_generated.csv", fd)
        _header("Done")
        print(f"  {len(generated_rows)} generated variant(s) written to {args.outdir}")
        print(f"\n{BANNER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
