"""What the search-interest benchmarks actually do on their pages.

The Trends tab picks three brands worth studying -
the traditional bank with the largest share of brand search, the one whose
share rose fastest, and the measurable challenger. It picks them on attention
alone and says so: Google Trends knows who was looked up, never why.

This module answers the next question, and only that one: what do those three
pages measurably DO that ING's do not. The selection comes from search
interest; every fact below comes from the measured feature set, on the same
z-scores the profile cards use.

THE LINE THIS MODULE DOES NOT CROSS. It never claims a page feature explains
a share of search. The two halves are deliberately computed from different
sources and joined only by the bank name: search interest selects WHO to look
at, the dataset says WHAT they do. Anything more would be the causal claim the
whole project refuses (PRD 5.2, plan risk P-08) - a 2026 page cannot explain a
2023 movement, and nothing here regresses one onto the other.

Small samples, stated plainly: a bank with one captured page has a z-score
built on one page. The threshold constants below are presentation conventions,
not significance tests.
"""

from __future__ import annotations

import pandas as pd

from comparator.analysis import bank_vectors, standardise
from comparator.dictionary import FeatureDictionary

# A benchmark's feature is worth reporting when it sits this far from the
# focus bank on the standardised scale. Below it the two are doing the same
# thing and there is nothing to take.
LESSON_MIN_GAP_SD = 1.0

# For a feature to count as shared ground, all three must lean the same way by
# at least this much, and the focus bank must lean the other way.
COMMON_MIN_SD = 0.3

# For a feature to count as a disagreement, the three must straddle the mean
# by at least this much on both sides.
DIVERGENCE_MIN_SD = 0.5

MAX_LESSONS_PER_BANK = 4
MAX_COMMON = 4
MAX_DIVERGENT = 5

ROLE_LABELS = {
    "attention": "largest share of brand search among traditional banks",
    "momentum": "fastest-rising share of brand search among traditional banks",
    "challenger": "the challenger with enough search volume to measure",
}

def _caveat(count: int) -> str:
    """Counted, not written: the selection is valid from two brands up."""
    return (
        f"These {count} brands were selected on search attention alone. What follows is "
        "what their pages measurably do differently - not a demonstration that those "
        "choices are why they are searched for. This data cannot show that."
    )


def _direction(value: float) -> str:
    return "above" if value > 0 else "below"


def _pick_by_dimension(
    candidates: list[dict], fd: FeatureDictionary, limit: int
) -> list[dict]:
    """Strongest feature per dimension, so twin features do not say it twice.

    `has_animation` and `animated_asset_count` are two columns describing one
    choice; listing both reads as two findings when there is one.
    """
    best: dict[str, dict] = {}
    for item in candidates:
        name = item["feature"]
        dimension = fd[name].dimension if name in fd else name
        current = best.get(dimension)
        if current is None or abs(item["strength"]) > abs(current["strength"]):
            best[dimension] = item
    ordered = sorted(best.values(), key=lambda i: -abs(i["strength"]))
    return ordered[:limit]


def _benchmark_keys(
    trajectory: dict, bank_keys: set[str], focus: str
) -> list[tuple[str, str, dict]]:
    """(bank_key, role, entry) for every benchmark the Trends tab selected.

    The focus bank is dropped here as well as upstream: this module is handed a
    trajectory it does not build, and a bank cannot be its own benchmark.
    """
    scope = (trajectory or {}).get("benchmark") or {}
    entries = list(scope.get("benchmarks") or [])
    if scope.get("challenger"):
        entries.append(scope["challenger"])

    picked: list[tuple[str, str, dict]] = []
    for entry in entries:
        key = entry.get("key")
        if key not in bank_keys or key == focus:
            continue
        for role in entry.get("roles", []):
            picked.append((key, role, entry))
            break
    return picked


def build_benchmark_lessons(
    df: pd.DataFrame,
    fd: FeatureDictionary,
    trajectory: dict | None,
    *,
    focus: str = "ing",
) -> dict | None:
    """Per-benchmark, shared and divergent page choices. None when unavailable."""
    if not trajectory:
        return None

    vectors = bank_vectors(df, fd, tier=None).dropna(axis=1, how="any")
    if vectors.empty or focus not in vectors.index:
        return None
    z = standardise(vectors)

    selected = _benchmark_keys(trajectory, set(z.index), focus)
    if len(selected) < 2:
        return None

    keys = [key for key, _, _ in selected]
    focus_row = z.loc[focus]

    # Shared ground first, so a fact claimed by all three is not repeated as
    # one bank's own lesson further down.
    common_candidates = []
    for feature in z.columns:
        values = [float(z.loc[key, feature]) for key in keys]
        focus_value = float(focus_row[feature])
        if min(abs(v) for v in values) < COMMON_MIN_SD:
            continue
        if not (all(v > 0 for v in values) or all(v < 0 for v in values)):
            continue
        if (focus_value > 0) == (values[0] > 0):
            continue
        mean = sum(values) / len(values)
        common_candidates.append({
            "feature": feature,
            "strength": mean,
            "meanZ": round(mean, 2),
            "focusZ": round(focus_value, 2),
            "direction": _direction(mean),
        })
    common = _pick_by_dimension(common_candidates, fd, MAX_COMMON)
    claimed = {item["feature"] for item in common}

    banks = []
    for key, role, entry in selected:
        candidates = []
        for feature in z.columns:
            if feature in claimed:
                continue
            value = float(z.loc[key, feature])
            focus_value = float(focus_row[feature])
            gap = value - focus_value
            if abs(gap) < LESSON_MIN_GAP_SD:
                continue
            candidates.append({
                "feature": feature,
                "strength": gap,
                "z": round(value, 2),
                "focusZ": round(focus_value, 2),
                "gapSd": round(gap, 2),
                "direction": _direction(gap),
            })
        banks.append({
            "bank": entry.get("bank", key),
            "key": key,
            "role": role,
            "roleLabel": ROLE_LABELS.get(role, role),
            "lastSharePct": entry.get("lastSharePct"),
            "relativeSlopePctPerYear": entry.get("relativeSlopePctPerYear"),
            "trendDirection": entry.get("direction"),
            "pages": int((df["bank"] == key).sum()),
            "lessons": _pick_by_dimension(candidates, fd, MAX_LESSONS_PER_BANK),
        })

    divergent_candidates = []
    for feature in z.columns:
        values = [(key, float(z.loc[key, feature])) for key in keys]
        highest = max(v for _, v in values)
        lowest = min(v for _, v in values)
        if highest < DIVERGENCE_MIN_SD or lowest > -DIVERGENCE_MIN_SD:
            continue
        divergent_candidates.append({
            "feature": feature,
            "strength": highest - lowest,
            "spreadSd": round(highest - lowest, 2),
            "values": [
                {"bank": entry.get("bank", key), "key": key, "z": round(value, 2)}
                for (key, value), (_, _, entry) in zip(values, selected)
            ],
        })
    divergent = _pick_by_dimension(divergent_candidates, fd, MAX_DIVERGENT)

    for item in common + divergent:
        item.pop("strength", None)
    for bank in banks:
        for lesson in bank["lessons"]:
            lesson.pop("strength", None)

    return {
        "focus": focus,
        "banks": banks,
        "common": common,
        "divergent": divergent,
        "caveat": _caveat(len(banks)),
    }
