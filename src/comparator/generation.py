"""Step 5 - LLM campaign generation and its evaluation (stretch goal).

steph 15/09, new module. Project Plan section 4.5 and Appendix B; owner: me.

THE POINT IS NOT THE COPY. It is to show the feature framework is specific
enough to (a) drive a generation and (b) measure whether the generation landed
where it was asked to. So the loop closes on itself:

    profile cards + category comparison  ->  a numeric TARGET in our own features
    target                               ->  a brief the model is given
    generated campaign                   ->  rendered to HTML
    that HTML                            ->  collection.scraper.extract(), THE SAME
                                             function that reads real bank pages
    resulting row                        ->  scored against the target, and
                                             plotted alongside the real banks

Scoring the output with a second, friendlier measuring stick would make the
evaluation meaningless, so there is deliberately only one extractor in this
repo and this module imports it rather than reimplementing anything.

HONEST LIMITS, to repeat wherever this is shown (plan risk P-08, mine):
  * A generated page is text and specs, not a real rendered page. Features that
    need a browser or real assets - actual colours, image area, page height -
    are declared by the brief, not measured. Only the text-derived and
    DOM-derived features are genuinely measured. `MEASURED_FEATURES` below is
    the explicit list, and evaluation covers nothing else.
  * Hitting the target says the generator followed instructions. It says
    NOTHING about whether the campaign would perform better - we have no
    performance data at all (PRD 5.2).
"""

from __future__ import annotations

import html as html_lib
import os
from dataclasses import dataclass, field
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from comparator.analysis import bank_vectors, category_comparison
from comparator.collection.llm_extractor import LLMExtractionError, _call_llm
from comparator.collection.scraper import extract
from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.generation_guardrails import GuardrailReport, check_generated_campaign
from comparator.profiles import build_profile
from comparator.schema import format_list

Variant = Literal["on_brand", "challenger_style"]

# Features the rendered HTML genuinely exercises, so evaluation can claim to
# have MEASURED them. Anything outside this list is a declared intention, not a
# measurement, and is excluded from the scorecard on purpose.
MEASURED_FEATURES = (
    "word_count", "word_count_band", "sentence_count", "avg_sentence_length",
    "second_person_ratio", "second_person_ratio_band", "first_person_plural_count",
    "question_count", "urgency_marker_count", "numeric_claim_count",
    "readability_band", "image_count", "hero_image_present", "cta_count",
    "cta_above_fold", "text_to_image_ratio", "text_to_image_ratio_band",
    "disclaimer_present", "disclaimer_word_share", "rate_shown",
)

# How close a numeric value has to be to count as "hit".
NUMERIC_TOLERANCE = 0.30

# steph 15/09: features our OWN guardrails make unreachable, so asking for them
# would guarantee a misleading "miss". The generator is forbidden to invent a
# rate or an amount (it writes [RATE] / [AMOUNT] placeholders), and the
# extractor counts a numeric claim by looking for digits - so a compliant
# generation scores zero here by construction.
#
# This is worth saying out loud rather than quietly dropping: you cannot ask a
# generator to match a bank's density of figures while forbidding it to invent
# figures. On a real run those numbers come from the product team, not the
# model. Listed here so the exclusion is visible in the scorecard output.
GUARDRAIL_BLOCKED_FEATURES = {
    "numeric_claim_count": "generator may not invent figures - writes [RATE]/[AMOUNT] placeholders",
    "rate_value_pct": "same - no invented rates",
    "rate_shown": "same - no invented rates",
}


# =============================================================================
# The target - expressed in our own features, derived from the data
# =============================================================================
@dataclass(frozen=True)
class TargetSpec:
    """One criterion the generation is asked to hit."""

    feature: str
    kind: Literal["exact", "range"]
    value: object = None
    low: float | None = None
    high: float | None = None
    rationale: str = ""

    @staticmethod
    def _num(value: float) -> str:
        """Ratios live below 1, counts in the hundreds - one format can't serve both."""
        return f"{value:,.2f}" if abs(value) < 10 else f"{value:,.0f}"

    def describe(self) -> str:
        if self.kind == "exact":
            return f"{self.feature} = {self.value}"
        return f"{self.feature} between {self._num(self.low)} and {self._num(self.high)}"

    def hit(self, actual: object) -> bool | None:
        """None means 'could not be measured', which is not the same as a miss."""
        if actual is None or (isinstance(actual, float) and pd.isna(actual)):
            return None
        if self.kind == "exact":
            return str(actual).lower() == str(self.value).lower()
        try:
            return self.low <= float(actual) <= self.high
        except (TypeError, ValueError):
            return None


@dataclass
class TargetProfile:
    """The full set of criteria for one variant (Plan Appendix B.1)."""

    variant: Variant
    description: str
    specs: list[TargetSpec] = field(default_factory=list)

    def brief_lines(self) -> list[str]:
        return [f"- {s.describe()}  ({s.rationale})" for s in self.specs]


def _range_around(centre: float, tolerance: float = NUMERIC_TOLERANCE) -> tuple[float, float]:
    span = abs(centre) * tolerance
    return max(0.0, centre - span), centre + span


def build_targets(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    focus: str = "ing",
    top_n: int = 6,
) -> dict[Variant, TargetProfile]:
    """Derive both variants' criteria FROM THE DATA, not from taste.

    on_brand        - keep the focus bank where it already is, but fix the
                      things the rubric says are weak (a CTA above the fold,
                      a disclaimer present).
    challenger_style- move the separating features to the challenger group's
                      own central values, so the contrast is the one the
                      comparison actually found rather than one we imagined.
    """
    fd = fd or load_dictionary()
    banks = df[df.get("data_source", "real") != "llm_generated"] if "data_source" in df else df
    vectors = bank_vectors(banks, fd)
    separation = category_comparison(banks, fd)

    focus_row = vectors.loc[focus] if focus in vectors.index else None
    challengers = banks[banks["bank_category"] == "challenger"]

    # The features that actually separate the two groups, restricted to the ones
    # a text-and-DOM generation can genuinely move.
    movable = [
        f for f in separation["feature"]
        if f in MEASURED_FEATURES and f in vectors.columns
        and f not in GUARDRAIL_BLOCKED_FEATURES
    ][:top_n]

    on_brand_specs: list[TargetSpec] = []
    challenger_specs: list[TargetSpec] = []

    for feature in movable:
        challenger_centre = pd.to_numeric(
            challengers[feature].astype("float64"), errors="coerce"
        ).dropna().median()
        if pd.isna(challenger_centre):
            continue

        is_bool = fd[feature].is_boolean if feature in fd else False
        if is_bool:
            challenger_specs.append(TargetSpec(
                feature=feature, kind="exact", value=bool(round(float(challenger_centre))),
                rationale="the challenger group's majority value",
            ))
        else:
            lo, hi = _range_around(float(challenger_centre))
            challenger_specs.append(TargetSpec(
                feature=feature, kind="range", low=lo, high=hi,
                rationale=f"challenger median {challenger_centre:,.2f}",
            ))

        if focus_row is not None and not pd.isna(focus_row.get(feature)):
            centre = float(focus_row[feature])
            if is_bool:
                on_brand_specs.append(TargetSpec(
                    feature=feature, kind="exact", value=bool(round(centre)),
                    rationale=f"{focus}'s own current value - stay on brand",
                ))
            else:
                lo, hi = _range_around(centre)
                on_brand_specs.append(TargetSpec(
                    feature=feature, kind="range", low=lo, high=hi,
                    rationale=f"{focus}'s own current level ({centre:,.2f})",
                ))

    # Rubric-driven fixes applied to BOTH variants - these are the things the
    # marketing frameworks say a campaign page should do regardless of style.
    for spec in (
        TargetSpec("cta_above_fold", "exact", True, rationale="AIDA 'action' - the next step must be visible without scrolling"),
        TargetSpec("disclaimer_present", "exact", True, rationale="guardrail - a disclaimer placeholder is never omitted"),
    ):
        on_brand_specs.append(spec)
        challenger_specs.append(spec)

    return {
        "on_brand": TargetProfile(
            variant="on_brand",
            description=f"{focus.upper()} tone of voice, optimised against the rubric but staying on brand.",
            specs=on_brand_specs,
        ),
        "challenger_style": TargetProfile(
            variant="challenger_style",
            description="The same offer, rebuilt with the patterns the analysis found at the challenger banks.",
            specs=challenger_specs,
        ),
    }


# =============================================================================
# What comes back from the model
# =============================================================================
class GeneratedCampaign(BaseModel):
    """Structured campaign copy and specs - never a finished creative."""

    headline: str
    subheading: str
    body_paragraphs: list[str] = Field(min_length=1)
    cta_label: str
    additional_cta_labels: list[str] = Field(default_factory=list)
    layout_archetype: Literal["hero_stacked", "split_columns", "card_grid", "long_form"]
    background_style: Literal["light", "dark"]
    accent_colour_hex: str
    image_briefs: list[str] = Field(min_length=1)
    disclaimer_placeholder: str
    persuasion_levers_used: list[str] = Field(default_factory=list)


SYSTEM_PROMPT = """You write structured marketing campaign specifications for a bank, for a
research comparison. You are NOT writing a finished advert.

Hard rules, no exceptions:
- Never invent a rate, price, fee, or product term. Where a figure belongs, write the
  placeholder [RATE] or [AMOUNT] exactly.
- Never reuse a named competitor's slogan, branding, or assets. Patterns only.
- Always fill disclaimer_placeholder with a short placeholder for the legal/risk text a
  compliance team would write. Never leave it empty.
- Image briefs are DESCRIPTIONS of an image to commission, never a URL or an asset.

Return ONLY a JSON object with exactly these keys:
"headline" (string), "subheading" (string), "body_paragraphs" (array of strings),
"cta_label" (string), "additional_cta_labels" (array of strings, may be empty),
"layout_archetype" (one of "hero_stacked","split_columns","card_grid","long_form"),
"background_style" (one of "light","dark"), "accent_colour_hex" (string like "#ff6200"),
"image_briefs" (array of strings), "disclaimer_placeholder" (string),
"persuasion_levers_used" (array, any of "reciprocity","commitment","social_proof",
"authority","liking","scarcity").

EVERY call-to-action label - the main one and each additional one - MUST contain one of
these words so it is machine-detectable:
discover, open, apply, get started, sign up, learn more.

Produce EXACTLY the number of image briefs and call-to-action labels the targets ask for.
Those counts are measured from what you return, so returning a different number is a miss."""


@dataclass
class GenerationBrief:
    """Everything the model is told (Plan Appendix B.1)."""

    product: str
    language: str
    target: TargetProfile
    focus_profile: dict
    competitor_patterns: list[str]

    def _structural_instructions(self) -> list[str]:
        """steph 15/09: image_count and cta_count are measured from what the model
        returns, but nothing told it how many to produce - so both variants missed
        them on the first live run for no reason other than an unstated brief.
        Counts the model can actually control are now stated as counts."""
        lines: list[str] = []
        for spec in self.target.specs:
            if spec.feature == "image_count":
                target = spec.value if spec.kind == "exact" else round((spec.low + spec.high) / 2)
                lines.append(f"Return EXACTLY {int(target)} entries in image_briefs.")
            if spec.feature == "cta_count":
                target = spec.value if spec.kind == "exact" else round((spec.low + spec.high) / 2)
                extra = max(0, int(target) - 1)
                lines.append(
                    f"Return EXACTLY {extra} entries in additional_cta_labels "
                    f"(cta_label plus those = {int(target)} calls to action in total)."
                )
        return lines

    def to_prompt(self) -> str:
        lines = [
            f"Product: {self.product}",
            f"Language of the copy: {self.language}",
            f"Variant: {self.target.variant} - {self.target.description}",
            "",
            "Hit these measurable targets (they are checked automatically afterwards):",
            *self.target.brief_lines(),
            "",
            *self._structural_instructions(),
            "",
            "The bank's current profile, for reference:",
            *[f"- {k}: {v}" for k, v in self.focus_profile.items()],
        ]
        if self.competitor_patterns:
            lines += ["", "Patterns observed at the challenger banks (patterns only, never their words):",
                      *[f"- {p}" for p in self.competitor_patterns]]
        return "\n".join(lines)


def _focus_summary(df: pd.DataFrame, fd: FeatureDictionary, focus: str) -> dict:
    profile = build_profile(df, focus, fd)
    return {
        "tone": profile["tone"],
        "value_proposition": profile["value_proposition"],
        "layout_archetype": profile["layout"]["archetype"],
        "dominant_colour": profile["palette"]["dominant_colour"],
    }


def _challenger_patterns(df: pd.DataFrame, fd: FeatureDictionary, limit: int = 5) -> list[str]:
    separation = category_comparison(df, fd)
    out = []
    for row in separation.head(limit).itertuples():
        direction = "higher" if row.effect_size_d > 0 else "lower"
        out.append(
            f"{row.feature.replace('_', ' ')} is {direction} at challengers "
            f"({row.traditional_mean:,.2f} vs {row.challenger_mean:,.2f})"
        )
    return out


def build_brief(
    df: pd.DataFrame,
    target: TargetProfile,
    fd: FeatureDictionary | None = None,
    *,
    focus: str = "ing",
    product: str = "term account",
    language: str = "en",
) -> GenerationBrief:
    fd = fd or load_dictionary()
    return GenerationBrief(
        product=product,
        language=language,
        target=target,
        focus_profile=_focus_summary(df, fd, focus),
        competitor_patterns=_challenger_patterns(df, fd) if target.variant == "challenger_style" else [],
    )


def generate(brief: GenerationBrief, *, retries: int = 1) -> tuple[GeneratedCampaign, str]:
    """Call the pinned model. Returns (campaign, "provider/model")."""
    import json

    last_error: Exception | None = None
    for _ in range(retries + 1):
        raw, model_id = _call_llm(brief.to_prompt(), system_prompt=SYSTEM_PROMPT)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return GeneratedCampaign.model_validate(json.loads(cleaned)), model_id
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
    raise LLMExtractionError(f"generation did not return a valid campaign: {last_error}")


# =============================================================================
# Render -> measure with the SAME extractor
# =============================================================================
def to_html(campaign: GeneratedCampaign) -> str:
    """Render the campaign as the minimal page the extractor knows how to read.

    Deliberately plain: the extractor detects CTAs from <a>/<button> text, a
    disclaimer from a class named "disclaimer", and images from <img> tags. This
    renders exactly those so the measurement is real rather than a stub.
    """
    esc = html_lib.escape
    images = "\n".join(
        f'<img src="brief-{i + 1}.png" alt="{esc(b)}">' for i, b in enumerate(campaign.image_briefs)
    )
    body = "\n".join(f"<p>{esc(p)}</p>" for p in campaign.body_paragraphs)
    secondary = "\n".join(
        f'<a href="#cta-{i + 2}">{esc(label)}</a>'
        for i, label in enumerate(campaign.additional_cta_labels)
    )
    return f"""<!doctype html>
<html><head><title>{esc(campaign.headline)}</title></head>
<body data-layout="{campaign.layout_archetype}" data-background="{campaign.background_style}">
<section class="hero">
{images}
<h1>{esc(campaign.headline)}</h1>
<h2>{esc(campaign.subheading)}</h2>
<a class="cta" href="#apply">{esc(campaign.cta_label)}</a>
</section>
<section class="body">
{body}
{secondary}
</section>
<footer class="disclaimer">{esc(campaign.disclaimer_placeholder)}</footer>
</body></html>"""


def score(
    campaign: GeneratedCampaign,
    *,
    variant: Variant,
    bank: str = "ing",
    bank_category: str = "traditional",
    product_family: str = "term_account",
    language: str = "en",
    model_id: str = "",
    captured_at: str = "",
) -> dict:
    """Run the generated campaign through the real extractor and build a row."""
    features = extract(to_html(campaign), language=language)
    features = {k: v for k, v in features.items() if not k.startswith("_")}

    row = {
        "page_id": f"generated_{variant}_{product_family}_{language}",
        "bank": bank,
        "bank_category": bank_category,
        "product_family": product_family,
        "page_role": "campaign_landing",
        "url": f"generated://{variant}",
        "language": language,
        "captured_at": captured_at,
        "collection_method": "static_fetch",
        "robots_allowed": True,
        "snapshot_html_path": "",
        "screenshot_path": "",
        "data_source": "llm_generated",
        "extraction_model": model_id,
        # declared by the brief, not measured - see module docstring
        "layout_archetype": campaign.layout_archetype,
        "dominant_colour_hex": campaign.accent_colour_hex,
        "persuasion_levers": format_list(campaign.persuasion_levers_used),
        "persuasion_lever_count": len(set(campaign.persuasion_levers_used)),
        **features,
    }
    return row


def evaluate(row: dict, target: TargetProfile) -> pd.DataFrame:
    """Did the generation land where it was asked to? (Plan Appendix B.2)"""
    rows = []
    for spec in target.specs:
        actual = row.get(spec.feature)
        hit = spec.hit(actual)
        rows.append({
            "feature": spec.feature,
            "target": spec.describe(),
            "actual": actual,
            "measured": spec.feature in MEASURED_FEATURES,
            "result": {True: "hit", False: "miss", None: "not measured"}[hit],
            "rationale": spec.rationale,
        })
    return pd.DataFrame(rows)


def hit_rate(scorecard: pd.DataFrame) -> float:
    """Share of MEASURED criteria that were hit. Unmeasured ones are excluded."""
    measured = scorecard[scorecard["result"].isin(["hit", "miss"])]
    return 0.0 if measured.empty else float((measured["result"] == "hit").mean())


def guardrails(row: dict) -> GuardrailReport:
    """Reuse Siegried's checklist rather than writing a second one."""
    return check_generated_campaign(row)


def pinned_model() -> str:
    """The model Decision 6 pins this project to, for the record."""
    return f"deepseek/{os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')}"
