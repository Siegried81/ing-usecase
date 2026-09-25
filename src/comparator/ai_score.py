"""AI Score - a transparent, rule-based composite index per bank.

Six axes (Digital, Trust, Bundled offer, Personalisation,
Innovation, Simplicity), each 0-10, computed for the radar chart in the web UI.

WHY DETERMINISTIC, NOT A MODEL CALL: every other "proprietary index" idea in the
original brief (Innovation/Trust/Digital/... scored by an LLM) would ask a model
to judge a whole bank from a handful of pages with no rubric a human could check -
exactly the kind of ungrounded number `recommendations.py` refuses to produce.
Instead, every axis here is a documented mean of features ALREADY in the
dictionary and ALREADY measured for every bank. No new LLM call, no new API key,
nothing this module could hallucinate.

Formulas (all means are of already-collected page-level features for one bank):
  * digital         - primary_cta_type == self_service_online, fast_digital_onboarding_claim,
                       mobile_first_design_signal
  * trust           - institutional_trust_signal_present, regulatory_disclosure_prominence
                       == prominent (pages where it is "not_applicable" are left out, not
                       counted as a no), branch_network_cited_as_benefit
  * cross_sell      - is_bundled_offer. Labelled "Bundled offer" on screen: it is a
                       yes/no, and reusing the word "cross-sell" put it next to
                       cross_sell.py's breadth ratio under one name.
  * personalisation - how many of the 8 target_personas values this bank's pages use at all,
                       out of the taxonomy size
  * innovation      - NOT MEASURABLE, returns None. Both inputs failed: has_animation
                       was withdrawn (analysis.CAPTURE_INVALID_FEATURES - the rule reports
                       "this stylesheet declares an animation", not "this page moves"), and
                       dominant_image_type == render_3d occurs on 1 page out of 51, so an
                       axis built on it alone would read 0 for thirteen banks of fourteen.
  * simplicity      - readability_band mapped to a 0-10 scale (very_easy=10 ... very_hard=0)

None (not 0) is returned whenever a bank has no data at all for an axis - a
missing measurement is not the same as the worst possible score, same rule
`profiles.py`'s `mean()` already follows.

What this cannot tell you: these are six independent means, not a validated
psychometric scale - a bank can score high on "trust" by citing its branch
network alone, which says nothing about whether customers actually trust it.
Read the axes as "how often this bank's pages carry each kind of signal", not
as a verdict.
"""

from __future__ import annotations

import pandas as pd

AXES = ("digital", "trust", "cross_sell", "personalisation", "innovation", "simplicity")

PERSONA_TAXONOMY_SIZE = 8  # Len(target_personas.values) in the dictionary

# Categorical values that mean "this condition does not apply to this page",
# so the page is left out of the axis rather than counted as a "no".
# regulatory_disclosure_prominence is "not_applicable" on 17 of the
# 18 current-account pages (no credit component, so no TAEG is expected), and
# counting those as "not prominent" charged the banks for a property of the
# product family. Masking them moves one bank (Revolut, 3.3 to 5.0); the other
# thirteen stay at 0.0 because their two remaining inputs really are false -
# no page here cites a branch network as a benefit.
_NOT_APPLICABLE: dict[str, set[str]] = {
    "regulatory_disclosure_prominence": {"not_applicable"},
}

_READABILITY_TO_SIMPLICITY = {
    "very_easy": 10.0, "easy": 7.5, "medium": 5.0, "hard": 2.5, "very_hard": 0.0,
}


def _mean_of_bools(rows: pd.DataFrame, specs: list[tuple[str, object]]) -> float | None:
    """Row-wise mean across one or more boolean/categorical-equality conditions, x10.

    Each spec is (column, expected_value); expected_value=True/False reads the
    column as-is (already boolean), any other value is an equality check
    (e.g. ("primary_cta_type", "self_service_online")). A condition whose column
    is missing from the frame is skipped entirely; if every condition ends up
    skipped or entirely null, the result is None, never a fabricated 0.
    """
    columns = []
    for col, expected in specs:
        if col not in rows.columns:
            continue
        if isinstance(expected, bool):
            columns.append(rows[col].astype("boolean"))
        else:
            # NaN == expected is False in pandas, not NaN - without
            # masking, a page where this categorical was never extracted would
            # silently count as "condition false" instead of being excluded.
            eq = (rows[col] == expected).mask(rows[col].isna())
            # Same idea for an explicit "does not apply": excluded, not false.
            eq = eq.mask(rows[col].isin(_NOT_APPLICABLE.get(col, set())))
            columns.append(eq.astype("boolean"))
    if not columns:
        return None
    stacked = pd.concat(columns, axis=1)
    # Mean over both axes (rows and conditions) so one page with two
    # matching conditions doesn't count twice as much as a page with one.
    values = stacked.to_numpy(dtype="float64", na_value=float("nan"))
    flat = values[~pd.isna(values)]
    if flat.size == 0:
        return None
    return round(float(flat.mean()) * 10, 1)


def score_digital(rows: pd.DataFrame) -> float | None:
    return _mean_of_bools(rows, [
        ("primary_cta_type", "self_service_online"),
        ("fast_digital_onboarding_claim", True),
        ("mobile_first_design_signal", True),
    ])


def score_trust(rows: pd.DataFrame) -> float | None:
    return _mean_of_bools(rows, [
        ("institutional_trust_signal_present", True),
        ("regulatory_disclosure_prominence", "prominent"),
        ("branch_network_cited_as_benefit", True),
    ])


def score_cross_sell(rows: pd.DataFrame) -> float | None:
    return _mean_of_bools(rows, [("is_bundled_offer", True)])


def score_personalisation(rows: pd.DataFrame, taxonomy_size: int = PERSONA_TAXONOMY_SIZE) -> float | None:
    """Breadth of distinct personas this bank's pages address, out of the taxonomy."""
    if "target_personas" not in rows.columns:
        return None
    from comparator.schema import parse_list  # Local import, avoids a module-load cycle

    distinct: set[str] = set()
    for cell in rows["target_personas"].dropna():
        distinct.update(parse_list(cell))
    if not distinct:
        return None
    return round(len(distinct) / taxonomy_size * 10, 1)


def score_innovation(rows: pd.DataFrame) -> float | None:
    """Withdrawn: neither input survives scrutiny, so no number is returned.

    Kept as an axis rather than deleted so the radar shows the gap instead of
    quietly dropping to five axes - an absent measurement is a finding, and the
    module already returns None rather than a fabricated 0 elsewhere.
    """
    return None


def score_simplicity(rows: pd.DataFrame) -> float | None:
    if "readability_band" not in rows.columns:
        return None
    non_null = rows["readability_band"].dropna()
    if non_null.empty:
        return None
    mode = non_null.mode().iat[0]
    return _READABILITY_TO_SIMPLICITY.get(str(mode))


_SCORERS = {
    "digital": score_digital,
    "trust": score_trust,
    "cross_sell": score_cross_sell,
    "personalisation": score_personalisation,
    "innovation": score_innovation,
    "simplicity": score_simplicity,
}


def score_bank(df: pd.DataFrame, bank: str) -> dict[str, float | None]:
    """All six axes for one bank."""
    rows = df[df["bank"] == bank]
    return {axis: _SCORERS[axis](rows) for axis in AXES}


def score_all(df: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    return {bank: score_bank(df, bank) for bank in sorted(df["bank"].unique())}
