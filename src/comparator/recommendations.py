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
  * Trends (`include_trends`) are opt-in and add recommendations on top of the
    analysis ones. They are labelled `basis="trends"` and carry the search
    window they came from. They are context, never evidence - the same line
    trends.py draws - so the prompt may use them for timing and focus only, and
    a trends recommendation is never allowed to cite a page feature as proof.
  * Reputation (`include_reputation`, sieg 21/09) is the same idea for news
    headline themes: opt-in, `basis="reputation"`, context never evidence -
    the same line reputation.py draws - and never allowed to cite a page
    feature as proof either. Unlike trends it needs no separate payload: the
    dashboard already travels inside `report["reputation"]`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from comparator.collection.llm_extractor import LLMExtractionError, _call_llm
from comparator.reputation import RECENT_DAYS  # sieg 21/09
from comparator.trends import PRODUCT_MAP

Priority = Literal["high", "medium", "low"]
Basis = Literal["analysis", "trends", "reputation"]


class RecommendationModel(BaseModel):
    """One recommendation as returned by the model."""

    title: str
    priority: Priority = "medium"
    finding: str = Field(description="what the analysis shows, grounded in the report")
    recommendation: str = Field(description="the concrete change to make")
    features: list[str] = Field(default_factory=list)
    page_targets: list[str] = Field(default_factory=list)
    basis: Basis = "analysis"
    market_context: str | None = Field(default=None, description="search-interest context, trends basis only")
    # sieg 21/09: mirrors market_context for the reputation basis.
    reputation_context: str | None = Field(
        default=None, description="news-theme context, reputation basis only"
    )


class RecommendationSetModel(BaseModel):
    summary: str
    recommendations: list[RecommendationModel] = Field(min_length=1)


_BASE_RULES = """You are a marketing analytics advisor to ING Belgium. You are given the
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
- Write in English."""

_PAGE_KEYS = ("index, comptes-epargne, compte-a-terme, compte-courant, jeunes, investir, "
              "credit-hypothecaire, ouvrir-compte, pourquoi-ing, contact")

_TRENDS_ADDENDUM = """You are ALSO given Google Trends search-interest context for Belgium: weekly
search interest per bank and product, with anomalies a separate detector flagged. Use it to add
recommendations that the page measurements alone cannot support.

Trends rules, no exceptions:
- Search interest is CONTEXT, never evidence that anything worked. A spike is not proof a page, a
  campaign or a change caused anything, and it is never by itself a reason to change a feature.
- Coverage is partial: only the banks marked covered have any data. Never claim behaviour for a
  bank without trends data, and never compare a covered bank to an uncovered one.
- Use ONLY the dates, kinds and values given in the context. Never invent, average or extrapolate
  a search number.
- A trends-based recommendation is about TIMING, SEQUENCING or MARKET FOCUS: when to make a change,
  which product page to prioritise, or which period a message must be ready for. It is still an
  action on an ING page.
- Trends recommendations must NOT cite page features as evidence; leave "features" empty and put
  the reasoning in "finding". Say plainly that the link is a hypothesis to verify."""

_REPUTATION_ADDENDUM = """You are ALSO given recent news headline THEMES (never sentiment) for some
banks: counts of what real headlines about that bank were ABOUT in the last 90 days, plus up to 5
notable headlines.

Reputation rules, no exceptions:
- Theme counts are CONTEXT, never evidence that a page or campaign performed. They say what a bank
  is currently in the news ABOUT, nothing more.
- Use ONLY the theme names, counts and headlines given. Never invent a headline, a count, or an
  outlet, and never describe a theme as positive or negative - themes are topics, not sentiment.
- A reputation-based recommendation compares what ING's OWN page claims against what the press is
  actually covering right now (for example: a page claims digital leadership but the news themes
  show nothing under innovation_digital), or flags a theme ING should be careful not to amplify with
  unrelated framing on the page (for example: heavy urgency language next to a crisis_or_scandal
  theme).
- Reputation recommendations must NOT cite page features as evidence; leave "features" empty and put
  the reasoning in "finding". Say plainly that the link is a hypothesis to verify."""

def _system_prompt(*, with_trends: bool, with_reputation: bool) -> str:
    """Assemble the system prompt from whichever optional context blocks apply.

    sieg 21/09: reputation joins trends as a second, independent opt-in context.
    Built from parts rather than one hardcoded constant per combination (trends
    only / reputation only / both / neither), so a third context later is one
    more addendum, not four more near-duplicate strings.
    """
    parts = [_BASE_RULES]
    bases = ['"analysis"']
    extra_counts: list[str] = []
    if with_trends:
        parts.append(_TRENDS_ADDENDUM)
        bases.append('"trends"')
        extra_counts.append("2 to 4 more from search-interest context")
    if with_reputation:
        parts.append(_REPUTATION_ADDENDUM)
        bases.append('"reputation"')
        extra_counts.append("1 to 3 more from news-theme context")

    extra_text = f" (plus {'; '.join(extra_counts)})" if extra_counts else ""
    extra_bases = [b.strip('"') for b in bases if b != '"analysis"']
    empty_features_note = (
        f"; empty for a {' or '.join(extra_bases)} recommendation" if extra_bases else ""
    )
    output_spec = f"""Return ONLY a JSON object with exactly these keys:
"summary" (2-3 sentences, the single most important thing the analysis says about ING), and
"recommendations" (array of 6 to 8 analysis recommendations{extra_text}). Each recommendation object
has exactly:
  "title" (short, imperative),
  "priority" (one of "high","medium","low"),
  "finding" (what the data shows),
  "recommendation" (the specific change to make on the page),
  "features" (exact feature identifiers from the analysis{empty_features_note}),
  "page_targets" (array of page keys, from this list only: {_PAGE_KEYS}),
  "basis" (one of {", ".join(bases)}),
  "market_context" (null unless basis is "trends"; then one or two sentences naming the attention
   pattern and the window it comes from),
  "reputation_context" (null unless basis is "reputation"; then one or two sentences naming the
   theme(s) and headline count this recommendation is drawn from).

No preamble, no markdown fences, JSON only."""
    parts.append(output_spec)
    return "\n\n".join(parts)


@dataclass
class Recommendation:
    id: str
    title: str
    priority: Priority
    finding: str
    recommendation: str
    features: list[str] = field(default_factory=list)
    page_targets: list[str] = field(default_factory=list)
    basis: Basis = "analysis"
    market_context: str | None = None
    reputation_context: str | None = None


@dataclass
class RecommendationSet:
    generated_at: str
    model: str
    summary: str
    recommendations: list[Recommendation]
    used_trends: bool = False
    used_reputation: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "RecommendationSet":
        return cls(
            generated_at=payload.get("generated_at", ""),
            model=payload.get("model", ""),
            summary=payload.get("summary", ""),
            recommendations=[Recommendation(**r) for r in payload.get("recommendations", [])],
            used_trends=bool(payload.get("used_trends", False)),
            used_reputation=bool(payload.get("used_reputation", False)),
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


# How much of Dan's five-year series travels into the prompt. The model gets the
# anomalies a detector already flagged inside this window, never the raw weekly
# points, so it cannot read a level and turn it into a target.
TRENDS_RECENT_DAYS = 730


def _within_window(anomaly: dict, cutoff: date | None) -> bool:
    raw = anomaly.get("date")
    if not raw:
        return False
    try:
        when = date.fromisoformat(str(raw))
    except ValueError:
        return False
    return cutoff is None or when >= cutoff


def _trends_digest(trends: dict, report: dict, *, per_product: int = 6) -> str | None:
    """The slice of Dan's Trends payload the model is allowed to see.

    Context, not evidence: flagged weeks and the dates around them, never a value
    to regress a page feature onto. Only the banks this run actually captured,
    only the recent window, and the coverage gap travels with it so the model
    cannot imply a comparison the data does not support. Returns None when there
    is nothing relevant, which is also what makes the caller fall back cleanly.
    """
    # The report's scope lists banks by display name; Dan's payload keeps both a
    # key and the same display name, so match on the name the UI shows.
    captured = list(report.get("scope", {}).get("banks") or [])
    if not captured:
        return None

    by_name = {b.get("name"): b for b in trends.get("banks", [])}
    window = trends.get("window", {})

    # Keep the digest to the product family this run measured, so the model does
    # not reason about mortgage searches for a current-account comparison. If the
    # mapping finds nothing, fall back to the full set rather than returning none.
    family = report.get("scope", {}).get("product_family")
    if family and not any(
        PRODUCT_MAP.get(p.get("id")) == family
        for name in captured
        for p in (by_name.get(name) or {}).get("products", [])
    ):
        family = None
    cutoff: date | None = None
    if window.get("end"):
        try:
            cutoff = date.fromisoformat(str(window["end"])) - timedelta(days=TRENDS_RECENT_DAYS)
        except ValueError:
            cutoff = None

    banks: list[dict] = []
    covered_names: set[str] = set()
    for name in captured:
        bank = by_name.get(name)
        if bank is None:
            continue
        covered_names.add(name)
        products = []
        for product in bank.get("products", []):
            if family and PRODUCT_MAP.get(product.get("id")) != family:
                continue
            anomalies = [
                {
                    "date": a.get("date"),
                    "term": term.get("label") or term.get("term"),
                    "kind": a.get("label") or a.get("type"),
                    "value": a.get("value"),
                    "score": a.get("score"),
                }
                for term in product.get("terms", [])
                for a in term.get("anomalies", [])
                if _within_window(a, cutoff)
            ]
            if not anomalies:
                continue
            anomalies.sort(key=lambda a: a.get("date") or "", reverse=True)
            products.append({
                "product": product.get("label") or product.get("id"),
                "recent_anomalies": anomalies[:per_product],
                "recent_count": len(anomalies),
            })
        if products:
            banks.append({"bank": bank.get("name"), "products": products})

    if not banks:
        return None

    events = [
        {"date": e.get("date"), "bank": e.get("bank"), "label": e.get("label")}
        for e in trends.get("events", [])
        if e.get("bank") in covered_names
    ]
    matches = [
        {
            "bank": m.get("campaignBank"),
            "campaign": m.get("campaignName"),
            "product": m.get("productId"),
            "term": m.get("term"),
            "date": m.get("date"),
            "kind": m.get("label"),
            "delay_days": m.get("delayDays"),
            "seasonal_confound": m.get("seasonalConfound"),
        }
        for m in trends.get("campaigns", {}).get("matches", [])
        if m.get("campaignBank") in covered_names
    ][:12]

    coverage = trends.get("coverage", {})
    payload = {
        "window": window,
        "covered_banks": coverage.get("covered"),
        "uncovered_banks": coverage.get("uncovered"),
        "attention_anomalies": banks,
        "known_structural_events": events,
        "campaigns_matched_to_spikes": matches,
        "guardrail": trends.get("guardrail"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _reputation_digest(report: dict) -> str | None:
    """The slice of the reputation dashboard the model is allowed to see.

    sieg 21/09. Unlike trends, reputation needs no separate payload argument:
    `report["reputation"]` already carries `build_dashboard()`'s output (see
    export_web_report.py). Only banks this run actually compared, and only
    ones with at least one classified theme, so the model never reasons about
    a bank reputation.py could not fetch anything for. Returns None when
    reputation was never configured or nothing covers this run's banks - same
    fall-back-cleanly pattern as `_trends_digest`.
    """
    dashboard = report.get("reputation") or {}
    if not dashboard.get("available"):
        return None

    snapshots = dashboard.get("banks", {})
    banks: list[dict] = []
    for entry in report.get("banks", []):
        snapshot = snapshots.get(entry.get("key"))
        if not snapshot:
            continue
        themes = {t: c for t, c in snapshot.get("themes", {}).items() if c > 0}
        if not themes:
            continue
        banks.append({
            "bank": entry.get("name"),
            "headline_count": snapshot.get("headline_count", 0),
            "themes": themes,
            "notable_headlines": [
                h.get("title") for h in snapshot.get("notable_headlines", []) if h.get("title")
            ],
        })
    if not banks:
        return None
    return json.dumps({"window_days": RECENT_DAYS, "banks": banks}, ensure_ascii=False, indent=2)


def parse_response(raw: str) -> RecommendationSetModel:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return RecommendationSetModel.model_validate(json.loads(cleaned))


def build_recommendations(
    report: dict,
    *,
    include_trends: bool = False,
    trends: dict | None = None,
    include_reputation: bool = False,
    retries: int = 1,
) -> RecommendationSet:
    """Ask the pinned model for recommendations, then verify them against the report.

    A feature id the model made up is dropped rather than failing the run: the
    recommendation still stands on its prose, and silently keeping a phantom
    feature id would let the UI link to evidence that does not exist.

    When `include_trends` is set, `trends` (the Trends tab payload) is sliced to
    a recent, captured-banks-only digest and added to the prompt as CONTEXT. The
    model is told to add trends recommendations on top of the analysis ones; they
    come back with `basis="trends"` and cannot cite page features.

    When `include_reputation` is set (sieg 21/09), `report["reputation"]` - already
    part of the report, no separate argument needed - is sliced the same way and
    added as a second, independent CONTEXT block. Those recommendations come back
    with `basis="reputation"` and cannot cite page features either.
    """
    trends_digest = _trends_digest(trends, report) if (include_trends and trends) else None
    if include_trends and not trends_digest:
        raise LLMExtractionError(
            "trends context was requested but no trends data covers this run's banks"
        )

    reputation_digest = _reputation_digest(report) if include_reputation else None
    if include_reputation and not reputation_digest:
        raise LLMExtractionError(
            "reputation context was requested but no reputation data covers this run's banks"
        )

    prompt = (
        "Analysis of Belgian bank campaign pages, measured on the same features "
        "for every bank:\n\n" + _digest(report)
    )
    if trends_digest:
        prompt += (
            "\n\nGoogle Trends search-interest context (Belgium) - CONTEXT ONLY, "
            "not performance data:\n\n" + trends_digest
        )
    if reputation_digest:
        prompt += (
            "\n\nRecent news headline themes (Belgium) - CONTEXT ONLY, never "
            "sentiment or performance data:\n\n" + reputation_digest
        )

    system_prompt = _system_prompt(with_trends=bool(trends_digest), with_reputation=bool(reputation_digest))
    last_error: Exception | None = None
    for _ in range(retries + 1):
        raw, model_id = _call_llm(prompt, system_prompt=system_prompt, timeout=180)
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
                basis=r.basis,
                market_context=(r.market_context or "").strip() or None,
                reputation_context=(r.reputation_context or "").strip() or None,
            )
            for i, r in enumerate(parsed.recommendations)
        ]
        return RecommendationSet(
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            model=model_id,
            summary=parsed.summary.strip(),
            recommendations=recommendations,
            used_trends=bool(trends_digest),
            used_reputation=bool(reputation_digest),
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
        used_trends=recommendation_set.used_trends,
        used_reputation=recommendation_set.used_reputation,
    )
