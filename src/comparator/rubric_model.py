"""Score the text-inferable rubric features with the pinned model.

steph 16/09, new module. 13 rubric features are human-scored, and every run so
far reported all 13 as unscored - which means every judgement-based dimension
(tone, AIDA coverage, persuasion levers, value proposition) is missing from the
comparison and one deck claim is untestable.

THE MODEL IS A THIRD RATER, NOT A PRE-FILL. Its scores go into their own sheet,
`data/rubric/model_scores.csv`, and never into the human sheets. That matters:

  * A pre-filled human sheet gets rubber-stamped. Two people agreeing with a
    suggestion is not two independent judgements, and NFR-05's agreement number
    would become meaningless - it would measure how persuasive the model's
    guess was.
  * As a separate rater, model-vs-human agreement is measurable with the same
    machinery, which is what FR-18 asks for ("validated against human labels on
    a sample, agreement reported").
  * Until Friday's session, the model sheet gives the analysis coverage it
    otherwise has none of - explicitly marked as model-scored, never as consensus.

FOUR FEATURES ARE DELIBERATELY NOT SCORED HERE. accent_locations,
text_image_layout, layout_archetype and mobile_first_design_signal are judged
from the rendered page, and the pinned model (deepseek-chat) has no vision. The
extractor only ever sends text, so scoring them would be guessing from the wrong
evidence. They stay blank and stay human.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from comparator.collection.llm_extractor import LLMExtractionError, _call_llm
from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.rubric import RATER_COLUMN, rubric_features
from comparator.schema import format_list

# steph 18/09, FIXED - and the inter-rater data is what caught it.
#
# This list used to be hand-written, and it was wrong: 8 of the 9 features I let
# the model score from text are declared in the dictionary as `source: screenshot`.
# The module's own docstring claims it refuses to score from the wrong evidence,
# and then it did exactly that for everything except formality_score.
#
# Siegried's scoring makes the damage measurable. Against her 11 pages:
#   formality_score     source html_text   kappa  0.42   (the one scored correctly)
#   aida_attention      source screenshot  kappa  0.81   (survived - visually obvious)
#   aida_desire         source screenshot  kappa  0.15
#   clarity_score       source screenshot  kappa  0.06
#   aida_interest       source screenshot  kappa  0.00
#   aida_action         source screenshot  kappa  0.00
#   persuasion_levers   source screenshot  kappa -0.03
#   rate_prominence     source screenshot  kappa -0.10
#   value_prop_clarity  source screenshot  kappa -0.12, Spearman -0.77
#
# value_prop_clarity is the clearest: the model ranked the pages almost exactly
# OPPOSITE to a human. That is what scoring from the wrong evidence looks like -
# not noise, but a confident answer to a question the text cannot settle. And
# rate_prominence is literally about where a number sits on the page.
#
# So the split is now DERIVED from the dictionary instead of asserted here.
# A feature the dictionary says is judged from the screenshot cannot be judged
# from text, and no future edit to this file can quietly re-add one.
TEXT_SOURCE = "html_text"


def _split(fd: FeatureDictionary) -> tuple[tuple[str, ...], tuple[str, ...]]:
    text, vision = [], []
    for feature in rubric_features(fd):
        (text if feature.source == TEXT_SOURCE else vision).append(feature.name)
    return tuple(text), tuple(vision)


TEXT_SCORABLE, VISION_ONLY = _split(load_dictionary())


class ModelRubricScores(BaseModel):
    """Only the text-sourced features. Built to accept exactly what the prompt
    asks for, so a model that volunteers a screenshot-sourced field is ignored
    rather than quietly believed."""

    model_config = {"extra": "ignore"}

    formality_score: int | None = Field(default=None, ge=1, le=5)


def build_prompt(fd: FeatureDictionary) -> str:
    """Build the scoring prompt FROM the dictionary, so the rubric the model is
    given and the rubric a human reads are the same rubric."""
    lines = [
        "You are scoring a bank campaign page against a fixed rubric, for a comparison "
        "across several banks. Apply the SAME standard to every bank - consistency matters "
        "more than being generous to any one of them.",
        "",
        "You are given the page's TEXT ONLY. Judge only what the words support. Where the "
        "text does not settle a question, choose the middle or most conservative option "
        "rather than inventing detail.",
        "",
        "Return ONLY a JSON object with exactly these keys:",
    ]
    for feature in rubric_features(fd):
        if feature.name not in TEXT_SCORABLE:
            continue
        definition = " ".join(feature.definition.split())
        if feature.values:
            allowed = " | ".join(f'"{v}"' for v in feature.values)
            lines.append(f'- "{feature.name}": one of {allowed} - {definition}')
        elif feature.range:
            lines.append(f'- "{feature.name}": integer {feature.min}-{feature.max} - {definition}')
        else:
            lines.append(f'- "{feature.name}": {definition}')
        if feature.rubric:
            for level, text in sorted(feature.rubric.items()):
                lines.append(f"    {level} = {' '.join(str(text).split())}")
    return "\n".join(lines)


def score_page(page_text: str, fd: FeatureDictionary | None = None, *, retries: int = 1) -> tuple[ModelRubricScores, str]:
    """Score one page. Returns (scores, "provider/model")."""
    fd = fd or load_dictionary()
    prompt = f"Page text (truncated):\n{page_text[:6000]}"
    last: Exception | None = None
    for _ in range(retries + 1):
        raw, model_id = _call_llm(prompt, system_prompt=build_prompt(fd))
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return ModelRubricScores.model_validate(json.loads(cleaned)), model_id
        except (json.JSONDecodeError, ValidationError) as exc:
            last = exc
    raise LLMExtractionError(f"model rubric scoring failed after {retries + 1} attempt(s): {last}")


def _page_text(row: pd.Series) -> str:
    """Read the stored snapshot - the same HTML the features were extracted from."""
    from bs4 import BeautifulSoup

    path = row.get("snapshot_html_path")
    if not path or not Path(path).is_file():
        return ""
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def score_dataset(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    skip_unusable: bool = True,
) -> pd.DataFrame:
    """Produce a rubric sheet scored by the model, in the same shape as a human one."""
    fd = fd or load_dictionary()
    rows = df
    if skip_unusable and "capture_quality" in rows.columns:
        rows = rows[rows["capture_quality"] != "unusable"]

    scored = []
    for _, row in rows.iterrows():
        text = _page_text(row)
        if not text:
            continue
        try:
            result, model_id = score_page(text, fd)
        except LLMExtractionError:
            continue
        entry = {
            RATER_COLUMN: f"model/{model_id.split('/')[-1]}",
            "page_id": row["page_id"], "bank": row.get("bank"),
            "bank_category": row.get("bank_category"),
            "product_family": row.get("product_family"), "language": row.get("language"),
            "url": row.get("url"), "screenshot_path": row.get("screenshot_path"),
            "capture_quality": row.get("capture_quality"),
            **{k: v for k, v in result.model_dump().items() if v is not None},
        }
        # The vision-only features stay blank, in the sheet, so their absence is visible.
        for name in VISION_ONLY:
            entry[name] = pd.NA
        scored.append(entry)

    return pd.DataFrame(scored)
