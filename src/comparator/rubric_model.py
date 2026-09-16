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

# Judged from the page's own words, which is all the model is given.
TEXT_SCORABLE = (
    "formality_score", "clarity_score", "rate_prominence", "value_prop_clarity",
    "aida_attention", "aida_interest", "aida_desire", "aida_action",
    "persuasion_levers",
)

# Needs the rendered page. deepseek-chat has no vision; these stay human.
VISION_ONLY = (
    "accent_locations", "text_image_layout", "layout_archetype",
    "mobile_first_design_signal",
)


class ModelRubricScores(BaseModel):
    formality_score: int = Field(ge=1, le=5)
    clarity_score: int = Field(ge=1, le=5)
    value_prop_clarity: int = Field(ge=1, le=5)
    rate_prominence: str
    aida_attention: bool
    aida_interest: bool
    aida_desire: bool
    aida_action: bool
    persuasion_levers: list[str] = Field(default_factory=list)


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
    lines += [
        "",
        'For "persuasion_levers", return an array containing only the Cialdini principles the '
        'page actually uses, from: "reciprocity", "commitment", "social_proof", "authority", '
        '"liking", "scarcity". Return an empty array if none are present - do not pad it.',
    ]
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
            **result.model_dump(exclude={"persuasion_levers"}),
            "persuasion_levers": format_list(result.persuasion_levers),
        }
        # The vision-only features stay blank, in the sheet, so their absence is visible.
        for name in VISION_ONLY:
            entry[name] = pd.NA
        scored.append(entry)

    return pd.DataFrame(scored)
