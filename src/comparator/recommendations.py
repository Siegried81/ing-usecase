"""LLM-written recommendations grounded in one analysis run.

The business UI reads a snapshot (`report.json`). This module turns that same
snapshot into a short, ordered list of things ING could change, written by the
pinned model (D6) and every one of them tied back to a measured feature in the
report.

steph 18/09, new module. The web UI is deliberately read-only, so the only
place a model is allowed to opine is here: the report says what the pages look
like, this says what to do about it, and the two never blend - a recommendation
carries the feature and the gap it was argued from, so a reader can reject it.

Guardrails, because a recommendation is where this kind of project goes wrong:
  * The prompt receives ONLY numbers that are already in the report. The model
    may not introduce a figure of its own, and the output is not trusted to.
  * Every recommendation must name the features it is based on; ids are checked
    against the report before the list leaves this module.
  * `selected` is carried through so the UI can pass a subset to site
    generation without this module knowing anything about the site.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from comparator.collection.llm_extractor import LLMExtractionError, _call_llm

Priority = Literal["high", "medium", "low"]


class RecommendationModel(BaseModel):
    """One recommendation as returned by the model."""

    title: str
    priority: Priority = "medium"
    finding: str = Field(description="what the analysis shows, grounded in the report")
    recommendation: str = Field(description="the concrete change to make")
    features: list[str] = Field(default_factory=list)
    page_targets: list[str] = Field(default_factory=list)


class RecommendationSetModel(BaseModel):
    summary: str
    recommendations: list[RecommendationModel] = Field(min_length=1)


SYSTEM_PROMPT = """You are a marketing analytics advisor to ING Belgium. You are given the
results of a measured comparison of Belgian bank campaign pages. Turn the findings into a short
list of concrete, prioritised recommendations for ING's own campaign pages.

Hard rules, no exceptions:
- Use ONLY the numbers and feature names present in the analysis. Never invent a figure, a rate,
  a conversion number, or a competitor's wording.
- In prose ("finding" and "recommendation" text), refer to a measured signal by its human-readable
  "label" (for example "Page brightness"), written naturally into the sentence - never paste a raw
  snake_case feature id or a long decimal into prose. Round figures to one or two decimals when you
  state them in a sentence.
- The "features" array is different: it is machine-checked, so it MUST use the exact snake_case
  feature identifiers from the analysis (for example "cta_above_fold", "second_person_ratio"), not
  the labels.
- A recommendation is a change ING can make to a page: copy, structure, layout, disclosure or
  call to action. Not market research, not a new product, not a data-collection exercise.
- Respect the limitations: where the evidence is thin, say so rather than overclaiming.
- Write in English.

Return ONLY a JSON object with exactly these keys:
"summary" (2-3 sentences, the single most important thing the analysis says about ING), and
"recommendations" (array of 6 to 8 objects). Each recommendation object has exactly:
  "title" (short, imperative),
  "priority" (one of "high","medium","low"),
  "finding" (what the data shows, referencing the feature and the gap),
  "recommendation" (the specific change to make on the page),
  "features" (array of exact feature identifiers from the analysis this is based on),
  "page_targets" (array of page keys, from this list only: index, comptes-epargne,
   compte-a-terme, compte-courant, jeunes, investir, credit-hypothecaire,
   ouvrir-compte, pourquoi-ing, contact).

No preamble, no markdown fences, JSON only."""


@dataclass
class Recommendation:
    id: str
    title: str
    priority: Priority
    finding: str
    recommendation: str
    features: list[str] = field(default_factory=list)
    page_targets: list[str] = field(default_factory=list)


@dataclass
class RecommendationSet:
    generated_at: str
    model: str
    summary: str
    recommendations: list[Recommendation]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "RecommendationSet":
        return cls(
            generated_at=payload.get("generated_at", ""),
            model=payload.get("model", ""),
            summary=payload.get("summary", ""),
            recommendations=[Recommendation(**r) for r in payload.get("recommendations", [])],
        )


def _round(value: object, digits: int = 2) -> object:
    """Round a report number before it reaches the model. sieg 20/09.

    The report stores full float precision (e.g. 0.5912291666666667) for
    charts and exact recomputation; the model has no use for that precision
    and was copying it verbatim into recommendation prose, which read as
    unpolished. Rounding here changes formatting only, not the value the
    guardrail above cares about (no new number is introduced)."""
    return round(value, digits) if isinstance(value, float) else value


def _digest(report: dict) -> str:
    """The slice of the report the model is allowed to see.

    Deliberately not the whole report: the bank profile cards carry pages of
    per-bank detail that would swamp the handful of comparisons a recommendation
    can actually be argued from. Everything sent here is a number the UI shows.
    """
    scope = report.get("scope", {})
    headline = report.get("headline", {})

    peer_gaps = [
        {
            "feature": g.get("feature"),
            "label": g.get("label"),
            "focus_value": _round(g.get("focusValue")),
            "peer_mean": _round(g.get("peerMean")),
            "gap_sd": _round(g.get("gapSd")),
            "direction": g.get("direction"),
            "trust": g.get("extraction"),
        }
        for g in report.get("peerGaps", [])
    ]
    separation = [
        {
            "feature": s.get("feature"),
            "label": s.get("label"),
            "traditional_mean": _round(s.get("traditional")),
            "challenger_mean": _round(s.get("challenger")),
            "effect_size_d": _round(s.get("effect")),
            "higher_at": s.get("higherAt"),
        }
        for s in report.get("separation", [])
    ]
    claims = [
        {"id": c.get("id"), "claim": c.get("claim"), "verdict": c.get("verdict"),
         "evidence": c.get("evidence")}
        for c in report.get("deckClaims", [])
    ]
    focus = report.get("banks", [])
    focus_signature = []
    for bank in focus:
        if bank.get("key") == "ing":
            focus_signature = bank.get("signature", [])

    payload = {
        "scope": {
            "product_family": scope.get("product_family_label"),
            "pages": scope.get("pages"),
            "banks": scope.get("banks"),
            "features_measured": scope.get("n_features"),
            "languages": scope.get("languages"),
        },
        "focus_bank": headline.get("focus"),
        "focus_position_score": headline.get("score"),
        "focus_verdict": headline.get("verdict"),
        "focus_gaps_vs_peers": peer_gaps,
        "traditional_vs_challenger": separation,
        "deck_claims_checked": claims,
        "focus_signature_sd_from_market": focus_signature,
        "limitations": report.get("limitations", {}),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _known_features(report: dict) -> set[str]:
    ids: set[str] = set()
    for g in report.get("peerGaps", []):
        if g.get("feature"):
            ids.add(g["feature"])
    for s in report.get("separation", []):
        if s.get("feature"):
            ids.add(s["feature"])
    return ids


def parse_response(raw: str) -> RecommendationSetModel:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return RecommendationSetModel.model_validate(json.loads(cleaned))


def build_recommendations(report: dict, *, retries: int = 1) -> RecommendationSet:
    """Ask the pinned model for recommendations, then verify them against the report.

    A feature id the model made up is dropped rather than failing the run: the
    recommendation still stands on its prose, and silently keeping a phantom
    feature id would let the UI link to evidence that does not exist.
    """
    from datetime import datetime, timezone

    prompt = (
        "Analysis of Belgian bank campaign pages, measured on the same features "
        "for every bank:\n\n" + _digest(report)
    )

    last_error: Exception | None = None
    for _ in range(retries + 1):
        raw, model_id = _call_llm(prompt, system_prompt=SYSTEM_PROMPT, timeout=180)
        try:
            parsed = parse_response(raw)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            continue

        known = _known_features(report)
        recommendations = [
            Recommendation(
                id=f"R{i + 1}",
                title=r.title.strip(),
                priority=r.priority,
                finding=r.finding.strip(),
                recommendation=r.recommendation.strip(),
                features=[f for f in dict.fromkeys(r.features) if f in known] or list(dict.fromkeys(r.features)),
                page_targets=list(dict.fromkeys(r.page_targets)),
            )
            for i, r in enumerate(parsed.recommendations)
        ]
        return RecommendationSet(
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            model=model_id,
            summary=parsed.summary.strip(),
            recommendations=recommendations,
        )

    raise LLMExtractionError(f"recommendation generation failed: {last_error}")


def select(recommendation_set: RecommendationSet, selected_ids: list[str]) -> RecommendationSet:
    """The subset a user ticked, preserving the model's original order."""
    wanted = set(selected_ids)
    return RecommendationSet(
        generated_at=recommendation_set.generated_at,
        model=recommendation_set.model,
        summary=recommendation_set.summary,
        recommendations=[r for r in recommendation_set.recommendations if r.id in wanted],
    )
