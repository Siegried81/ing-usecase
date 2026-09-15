"""Enforce the schema freeze rule semantically.

steph 15/09, new module. Risk P-04 in the project plan is mine, and its stated
mitigation is the actual rule:

    "Schema frozen Day 2; additions allowed, renames and removals only by
     unanimous agreement."                       - Project Plan, section 3.2

`tests/test_schema.py::test_dictionary_matches_frozen_snapshot` (sieg 15/09)
compares the two YAML files byte for byte. That is a useful DRIFT DETECTOR - it
stops an accidental edit landing unnoticed - and it stays. But it is not the
rule: it fails on an addition, which the rule explicitly permits, and it passes
on a rename, because updating both files makes the bytes match again. A rename
is the change that actually breaks analysis code, so it is the one worth
catching.

This module checks the rule itself. Additions pass. Anything that can break code
already written against the frozen schema fails, and says which feature and why.

    python3 scripts/check_schema_freeze.py

Both checks together: byte equality says "you changed it on purpose", this says
"what you changed is allowed".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from comparator.dictionary import DEFAULT_DICTIONARY, Feature, FeatureDictionary, load_dictionary

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FROZEN = REPO_ROOT / "config" / "feature_dictionary.frozen.yaml"

# Widening a tier is fine (extended -> core makes more data required of the
# collectors, never less of the consumers). Demoting core -> extended is a
# breaking change: analysis code may already require the column.
_TIER_RANK = {"extended": 0, "core": 1}


@dataclass
class FreezeReport:
    """What changed between the frozen schema and the working one."""

    breaking: list[str] = field(default_factory=list)
    additions: list[str] = field(default_factory=list)
    benign: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.breaking

    def raise_if_failed(self) -> None:
        if not self.ok:
            joined = "\n  - ".join(self.breaking)
            raise ValueError(
                "schema freeze violated - these changes need all three of us to agree "
                f"(Project Plan 3.2):\n  - {joined}"
            )

    def render(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        lines = [f"Schema freeze check: {status}"]
        for item in self.breaking:
            lines.append(f"  BREAKING  {item}")
        for item in self.additions:
            lines.append(f"  added     {item}")
        for item in self.benign:
            lines.append(f"  ok        {item}")
        if not (self.breaking or self.additions or self.benign):
            lines.append("  no change since the freeze")
        return "\n".join(lines)


def _compare_feature(frozen: Feature, current: Feature, report: FreezeReport) -> None:
    """Compare one feature that exists in both schemas."""
    name = frozen.name

    if frozen.type != current.type:
        report.breaking.append(
            f"{name}: type changed {frozen.type!r} -> {current.type!r}; "
            "code that reads this column expects the frozen type"
        )

    if frozen.primary_key != current.primary_key:
        report.breaking.append(f"{name}: primary-key flag changed")

    # Removing an allowed value invalidates rows already collected with it.
    if frozen.values and current.values is not None:
        dropped = [v for v in frozen.values if v not in current.values]
        if dropped:
            report.breaking.append(
                f"{name}: allowed value(s) removed: {dropped}; rows already scored with them become invalid"
            )
        gained = [v for v in (current.values or []) if v not in frozen.values]
        if gained:
            report.benign.append(f"{name}: allowed value(s) added: {gained}")

    # Narrowing a range invalidates values already recorded outside the new one.
    # sieg 15/09: fixed - the "frozen.range and current.range" guard skipped a
    # newly added range entirely, so a field with NO range before could gain
    # one with no check at all, even though that is itself a narrowing (any
    # value already recorded outside the new range becomes invalid). checked
    # as its own case instead of folding it into the two checks below, since
    # frozen.min/frozen.max don't exist to compare against.
    if not frozen.range and current.range:
        report.breaking.append(
            f"{name}: range added {current.range!r} where none existed; "
            "rows already recorded outside it become invalid"
        )
    elif frozen.range and current.range:
        f_lo, f_hi = frozen.min, frozen.max
        c_lo, c_hi = current.min, current.max
        if f_lo is not None and c_lo is not None and c_lo > f_lo:
            report.breaking.append(f"{name}: minimum raised {f_lo} -> {c_lo}, narrowing the accepted range")
        if f_hi is not None and c_hi is not None and c_hi < f_hi:
            report.breaking.append(f"{name}: maximum lowered {f_hi} -> {c_hi}, narrowing the accepted range")

    if _TIER_RANK.get(current.tier, 0) < _TIER_RANK.get(frozen.tier, 0):
        report.breaking.append(
            f"{name}: tier demoted {frozen.tier!r} -> {current.tier!r}; "
            "analysis may already require this column"
        )

    if frozen.nullable and not current.nullable:
        report.breaking.append(
            f"{name}: nullable -> not nullable; rows already collected with a blank here stop validating"
        )

    # Everything below is a change worth seeing but cannot break a consumer.
    if frozen.extraction != current.extraction:
        report.benign.append(f"{name}: extraction {frozen.extraction} -> {current.extraction}")
    if frozen.comparability != current.comparability:
        report.benign.append(f"{name}: comparability {frozen.comparability} -> {current.comparability}")
    if frozen.dimension != current.dimension:
        report.benign.append(f"{name}: dimension {frozen.dimension} -> {current.dimension}")


def compare(frozen: FeatureDictionary, current: FeatureDictionary) -> FreezeReport:
    """Apply the freeze rule: additions allowed, renames and removals are not."""
    report = FreezeReport()

    frozen_names = set(frozen.names)
    current_names = set(current.names)

    for name in sorted(frozen_names - current_names):
        report.breaking.append(
            f"{name}: removed or renamed; every consumer of this column breaks silently"
        )

    for name in sorted(current_names - frozen_names):
        report.additions.append(f"{name} ({current[name].dimension}, {current[name].tier})")

    for name in sorted(frozen_names & current_names):
        _compare_feature(frozen[name], current[name], report)

    return report


def check(
    current_path: str | Path = DEFAULT_DICTIONARY,
    frozen_path: str | Path = DEFAULT_FROZEN,
) -> FreezeReport:
    """Load both schemas and compare them."""
    return compare(load_dictionary(frozen_path), load_dictionary(current_path))
