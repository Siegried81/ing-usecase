"""Safety guardrails for an LLM-generated campaign row.

sieg 15/09, new module. Project Plan Appendix B.2 ("Is it safe?") already commits
the team to a checklist before any generated campaign is shown: no invented
rates/prices, no borrowed competitor assets, disclaimers never omitted, always
labelled synthetic. Step 5 (the generator itself) is a stretch goal gated behind
the Day 6 freeze and is NOT built here - this module only encodes the checklist
now, tested, so it is not improvised under deadline pressure once Step 5 starts.

Only what is mechanically checkable FROM THE ROW is checked here. "No invented
rates/prices" and "no borrowed competitor assets" need a human/prompt-level
comparison against the brief given to the generator - that cannot be derived
from the row alone, so those two are deliberately NOT checked here rather than
faked with a false sense of coverage.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GuardrailReport:
    ok: bool
    violations: list[str] = field(default_factory=list)


def check_generated_campaign(row: dict) -> GuardrailReport:
    """Check one generated campaign row against the plan's safety checklist."""
    violations: list[str] = []

    if row.get("data_source") != "llm_generated":
        violations.append(
            "data_source must be 'llm_generated' - a generated row must always be "
            "labelled, never passed off as a real capture (Appendix B.2, 'Is it safe?')"
        )

    if row.get("disclaimer_present") is not True:
        violations.append(
            "disclaimer_present must be true - the generation brief requires a "
            "disclaimer placeholder, never omitted (Appendix B.1, 'what it must not do')"
        )

    if row.get("regulatory_disclosure_prominence") == "absent":
        violations.append(
            "regulatory_disclosure_prominence must not be 'absent' on a generated row"
        )

    return GuardrailReport(ok=not violations, violations=violations)
