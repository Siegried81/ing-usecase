#!/usr/bin/env python3
"""Generate docs/feature_dictionary.md from the YAML, so the two cannot drift.

    python3 scripts/build_feature_docs.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from comparator.dictionary import load_dictionary

DEFAULT_OUT = Path("docs/feature_dictionary.md")


def render(fd) -> str:
    meta = fd.meta
    lines = [
        f"# {meta['name']}",
        "",
        "> Generated from `config/feature_dictionary.yaml` by `scripts/build_feature_docs.py`.",
        "> Edit the YAML, never this file.",
        "",
        f"**Version** {meta['version']} · **Status** {meta['status']} · **Date** {meta['date']}  ",
        f"**Owner** {meta['owner']}  ",
        f"**Grain** {meta['grain']}  ",
        f"**Freeze target** {meta['freeze_target']}",
        "",
        f"{len(fd)} features — {len(fd.columns('core'))} core, "
        f"{len(fd) - len(fd.columns('core'))} extended.",
        "",
        "## How to read the tables",
        "",
        "| Column | Meaning |",
        "| --- | --- |",
        "| **Extraction** | How the value is produced, and therefore how much it can be trusted. |",
        "| **Comparability** | How far the value travels. `within_language` values cannot cross NL/FR/EN. |",
        "| **Tier** | `core` is the Day 6 MVP minimum; `extended` is added only after the gate passes. |",
        "",
    ]

    for method, spec in fd.extraction_methods.items():
        lines.append(f"- **{method}** (trust: {spec['trust']}, owner: {spec['owner']}) — {spec['description'].strip()}")
    lines.append("")

    for dim_key, dim in fd.dimensions.items():
        features = fd.select(dimension=dim_key)
        lines += [
            f"## {dim['label']}",
            "",
            f"*{dim['prd_ref']}* — {len(features)} features",
            "",
            "| Feature | Type | Extraction | Comparability | Tier | Definition |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for f in features:
            type_text = f.type
            if f.values:
                type_text += "<br>" + " · ".join(f"`{v}`" for v in f.values)
            elif f.range:
                lo = "−∞" if f.min is None else f.min
                hi = "∞" if f.max is None else f.max
                type_text += f"<br>[{lo}, {hi}]"
            definition = " ".join(f.definition.split())
            if f.notes:
                definition += f"<br>*{' '.join(f.notes.split())}*"
            lines.append(
                f"| `{f.name}` | {type_text} | {f.extraction} | {f.comparability} | {f.tier} | {definition} |"
            )
        lines.append("")

        rubrics = [f for f in features if f.rubric]
        for f in rubrics:
            lines += [f"### Rubric — `{f.name}`", ""]
            for level, text in sorted(f.rubric.items()):
                lines.append(f"- **{level}** — {text}")
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    fd = load_dictionary()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(fd), encoding="utf-8")
    print(f"wrote {args.out} ({len(fd)} features)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
