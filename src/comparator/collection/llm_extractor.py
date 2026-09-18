"""Fills the model_assisted fields with ONE structured call per page.

sieg 14/09, new module - answers "will you use my .env.example?": yes, same
env-var names, because it's already a working pattern and there's no reason to
invent a second one for this project. Only the LLM section of your
.env.example is relevant here - the market-data/news/academic keys belong to
portfolio_forecasting, not this repo.

sieg 15/09: provider ORDER is now DEEPSEEK_API_KEY -> GROQ_API_KEY[_2/_3] ->
OPENROUTER_API_KEY -> CEREBRAS_API_KEY -> SAMBANOVA_API_KEY -> OLLAMA_HOST,
not the Groq-first order this paragraph used to describe - DeepSeek is now
first per steph's Decision 6 below (pinned labelling model, docs/decisions.md).
Updated here so the docstring doesn't silently disagree with _PROVIDERS.

WHY ONE CALL, NOT AN AGENT: same reasoning as the rest of this project (see
README "why a chain, not an agent"). Every page gets the same fixed prompt and
schema, applied identically - consistency across banks is the point, not
autonomous tool use. This is a feature-extraction call, nothing decides
anything here.

Providers are called via their OpenAI-compatible chat-completions endpoint
directly (requests), so this needs no per-provider SDK.

sieg 15/09: the default model names for OpenRouter/Cerebras/SambaNova were
originally guessed and flagged as unverified - replaced with the values from
Sieg's own portfolio_forecasting .env.example (qwen/qwen3-4b:free / gpt-oss-120b
/ gpt-oss-120b), which are known to work. Base URLs are still worth a quick
check against each provider's current docs if a call starts failing.
"""
from __future__ import annotations

import json
import os

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

# sieg 16/09: load environment variables via python-dotenv.
load_dotenv()

MODEL_FIELDS = (
    "primary_product", "dominant_image_type", "people_present", "imagery_register",
    "institutional_trust_signal_present", "youth_student_targeting",
    "secondary_bank_positioning", "expat_cross_border_targeting",
    "branch_network_cited_as_benefit", "first_time_investor_targeting",
    "senior_preretirement_targeting",
    # sieg 15/09: moved from rubric to model_assisted - these 12 are all
    # judged from page TEXT (source: html_text in the dictionary), same
    # reasoning as the fields above, not from the screenshot. persuasion_levers
    # and the 4 AIDA fields are deliberately NOT here - their dictionary
    # source is "screenshot" (layout/visual prominence matters for them) and
    # this extractor only ever sends text, never the image, to the LLM.
    "benefit_framing", "fab_level", "audience_segment", "is_bundled_offer",
    "cross_sell_delivery_model", "rate_framing", "primary_cta_type",
    "switching_framing", "regulatory_disclosure_prominence",
    "hidden_conditions_behind_free_claim", "esg_claim_specificity",
    "green_product_specific_benefit", "fast_digital_onboarding_claim",
)

SYSTEM_PROMPT = """You are extracting structured features from a bank campaign page for a
comparison across several banks. Apply the SAME criteria to every bank - consistency across
banks matters more than being generous to any single one.

Return ONLY a JSON object with exactly these keys:
- "primary_product": string, the specific product named on the page, in the page's own words
- "dominant_image_type": one of "photo", "illustration", "render_3d", "icon_only", "none"
- "people_present": boolean, whether any image on the page shows people
- "imagery_register": one of "lifestyle", "product", "abstract", "mixed", "none"
- "institutional_trust_signal_present": boolean, does the page invoke tenure, customer count,
  or ownership backing (e.g. state ownership) as a trust/safety argument
- "youth_student_targeting": boolean, is a junior/student account or youth-oriented offer promoted
- "secondary_bank_positioning": boolean, does the bank frame itself as an ADDITION to an existing
  bank ("keep your bank, add us") rather than a full replacement
- "expat_cross_border_targeting": boolean, does the page target expats/international clients
- "branch_network_cited_as_benefit": boolean, does the page explicitly cite branch/ATM network
  size as an advantage
- "first_time_investor_targeting": boolean, does the page frame investing as a first step for a
  novice (beginner glossary, low/no minimum amount) rather than assuming existing experience
- "senior_preretirement_targeting": boolean, does the page target a pre-retirement/senior life
  stage (pension planning, wealth transfer or succession, end-of-career estate management)
- "benefit_framing": one of "rational", "emotional", "mixed" - is the offer argued with figures,
  with feelings, or both
- "fab_level": one of "feature", "advantage", "benefit" - dominant level of the
  feature-advantage-benefit ladder ("3.2% gross annual" is a feature; "your money works while
  you sleep" is a benefit)
- "audience_segment": one of "retail", "professional", "mixed" - does the page address an
  individual, a professional/self-employed activity, or both
- "is_bundled_offer": boolean, does the page push a bundle (account + card + insurance +
  investment) in the same funnel, rather than one isolated product
- "cross_sell_delivery_model": one of "internal_advisor_led", "partner_addon_digital",
  "not_applicable" - when something is cross-sold, is it an in-house product with a dedicated
  advisor, a digital add-on distributed through a third-party partner with no advisor, or is
  nothing cross-sold on this page
- "rate_framing": one of "base_rate", "promo_bonus", "capped_tiered", "not_shown" - is the
  headline rate the regulated base rate, a promotional bonus, a capped/tiered rate presented as
  the full rate, or is no rate shown
- "primary_cta_type": one of "self_service_online", "book_advisor_or_branch", "other" - is the
  primary call to action self-service online, booking an advisor/branch visit, or something else
- "switching_framing": one of "retention_reassurance", "acquisition_encouragement",
  "not_applicable" - does the message reassure against switching away, actively encourage
  switching in, or is this not applicable
- "regulatory_disclosure_prominence": one of "prominent", "present_not_prominent", "absent",
  "not_applicable" - how visible is the disclosure that actually applies to THIS PAGE'S product
  family (given below): APR/TAEG for a mortgage, the deposit guarantee scheme for a
  term_account/savings_account, a capital-at-risk warning for an investment product. Use
  "not_applicable" when no such disclosure is expected for this product (e.g. a plain current
  account pack with no credit component) - do NOT score "absent" in that case, and do NOT expect
  a TAEG on a savings/term account (TAEG is a credit-only disclosure, savings accounts don't have
  one)
- "hidden_conditions_behind_free_claim": boolean, is "free" the headline claim while conditions
  (minimum balance, usage requirement) sit in small print
- "esg_claim_specificity": one of "no_claim", "vague_adjective_only",
  "backed_by_reference_or_figure" - does a sustainability claim carry a verifiable reference or
  figure, is it an adjective only, or is it absent
- "green_product_specific_benefit": boolean, is a concrete financial benefit (e.g. a rate
  discount) explicitly tied to a green/energy-performance criterion, vs a generic sustainability
  claim
- "fast_digital_onboarding_claim": boolean, does the page claim a fast, frictionless digital
  account-opening process (e.g. "open an account in 5 minutes", no branch visit needed, instant
  approval)

No preamble, no markdown fences, JSON only."""


class ModelAssistedFields(BaseModel):
    primary_product: str
    dominant_image_type: str
    people_present: bool
    imagery_register: str
    institutional_trust_signal_present: bool
    youth_student_targeting: bool
    secondary_bank_positioning: bool
    expat_cross_border_targeting: bool
    branch_network_cited_as_benefit: bool
    first_time_investor_targeting: bool
    senior_preretirement_targeting: bool
    benefit_framing: str
    fab_level: str
    audience_segment: str
    is_bundled_offer: bool
    cross_sell_delivery_model: str
    rate_framing: str
    primary_cta_type: str
    switching_framing: str
    regulatory_disclosure_prominence: str
    hidden_conditions_behind_free_claim: bool
    esg_claim_specificity: str
    green_product_specific_benefit: bool
    fast_digital_onboarding_claim: bool


class LLMExtractionError(Exception):
    """Raised when every provider fails or the response can't be validated."""


# (provider name, env var prefix, chat-completions URL, model env var, default model)
# sieg 14/09: same order as .env.example - Groq first (with key rotation),
# then hosted fallbacks, then local Ollama for dev.
#
# steph 15/09, Decision 6 (mine, due Day 2): DEEPSEEK IS THE PINNED MODEL for
# this project - one model, named, so every bank is labelled by the same judge.
# Stephane has the key, so it is the one we can actually run today. Sieg's chain
# stays underneath as a fallback for when DeepSeek is down, because losing a
# night of collection to one provider outage is worse than a mixed dataset - but
# a fallback is now RECORDED in extraction_model rather than silent, and
# schema.validate() warns when a dataset mixes models. See docs/decisions.md.
_PROVIDERS = [
    ("deepseek", "DEEPSEEK_API_KEY", None, "DEEPSEEK_MODEL", "deepseek-chat"),
    ("groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "GROQ_MODEL", "openai/gpt-oss-120b"),
    # sieg 15/09: kept steph's provider-tuple structure (name + deepseek pin,
    # decision 6) but fixed the default model ids for these three fallbacks -
    # they were unverified guesses (old docstring: "VERIFY... Cerebras/
    # SambaNova less so"). now verified against each provider's live model
    # listing: openrouter serves qwen/qwen3-4b:free, cerebras and sambanova
    # both serve gpt-oss-120b - matches Sieg's own portfolio_forecasting
    # .env.example, which is known to work.
    ("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_MODEL", "qwen/qwen3-4b:free"),
    ("cerebras", "CEREBRAS_API_KEY", "https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_MODEL", "gpt-oss-120b"),
    ("sambanova", "SAMBANOVA_API_KEY", "https://api.sambanova.ai/v1/chat/completions", "SAMBANOVA_MODEL", "gpt-oss-120b"),
]

DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"


def _provider_url(name: str, url: str | None) -> str:
    """DeepSeek's base URL is configurable, so it is resolved at call time."""
    if name == "deepseek":
        base = os.getenv("DEEPSEEK_BASE_URL", DEEPSEEK_DEFAULT_BASE_URL).rstrip("/")
        return f"{base}/chat/completions"
    return url


def _groq_keys() -> list[str]:
    keys = [os.getenv("GROQ_API_KEY"), os.getenv("GROQ_API_KEY_2"), os.getenv("GROQ_API_KEY_3")]
    return [k for k in keys if k]


def _call_openai_compatible(url: str, api_key: str, model: str, user_prompt: str, *, system_prompt: str = SYSTEM_PROMPT, timeout: int = 30) -> str:
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _call_ollama(user_prompt: str, *, system_prompt: str = SYSTEM_PROMPT, timeout: int = 60) -> str:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    response = requests.post(
        f"{host}/v1/chat/completions",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _call_llm(user_prompt: str, *, system_prompt: str = SYSTEM_PROMPT, timeout: int = 30) -> tuple[str, str]:
    """Try each provider in order; return (response_text, "provider/model").

    steph 15/09: now returns WHICH model answered, so the caller can record it
    (Decision 6). Previously the fallback was invisible - a run that started on
    one provider and finished on another produced a dataset that looked
    uniformly labelled but was not.
    """
    errors: list[str] = []

    for name, env_key, url, model_env, default_model in _PROVIDERS:
        keys = _groq_keys() if name == "groq" else [os.getenv(env_key)]
        keys = [k for k in keys if k]
        if not keys:
            continue
        model = os.getenv(model_env, default_model)
        resolved_url = _provider_url(name, url)
        for key in keys:
            try:
                text = _call_openai_compatible(resolved_url, key, model, user_prompt, system_prompt=system_prompt, timeout=timeout)
                return text, f"{name}/{model}"
            except requests.RequestException as exc:  # noqa: PERF203 - key rotation needs the loop
                errors.append(f"{name}: {exc}")

    try:
        return _call_ollama(user_prompt, system_prompt=system_prompt, timeout=timeout), f"ollama/{os.getenv('OLLAMA_MODEL', 'llama3.1')}"
    except requests.RequestException as exc:
        errors.append(f"ollama: {exc}")

    raise LLMExtractionError(f"every provider failed: {'; '.join(errors)}")


def extract_model_assisted(
    page_text: str, *, image_count: int, has_animation: bool, product_family: str, retries: int = 1
) -> ModelAssistedFields:
    """Run the extraction with validation + one retry on a bad response.

    sieg 15/09: product_family is now required - regulatory_disclosure_prominence
    cannot be judged without knowing which disclosure is even expected (TAEG only
    applies to a mortgage, not a savings account); see its dictionary entry.
    """
    user_prompt = (
        f"Page text (truncated): {page_text[:3000]}\n\n"
        f"Image count on page: {image_count}\n"
        f"Contains animation/video: {has_animation}\n"
        f"Product family: {product_family}"
    )
    fields, _model = extract_model_assisted_with_provenance(
        page_text, image_count=image_count, has_animation=has_animation,
        product_family=product_family, retries=retries,
    )
    return fields


def extract_model_assisted_with_provenance(
    page_text: str, *, image_count: int, has_animation: bool, product_family: str, retries: int = 1
) -> tuple[ModelAssistedFields, str]:
    """Same as extract_model_assisted, but also returns "provider/model".

    steph 15/09: added so run_collection.py can write extraction_model into the
    row. extract_model_assisted() is kept as a thin wrapper so existing callers
    and tests are unaffected.
    """
    user_prompt = (
        f"Page text (truncated): {page_text[:3000]}\n\n"
        f"Image count on page: {image_count}\n"
        f"Contains animation/video: {has_animation}\n"
        f"Product family: {product_family}"
    )
    last_error: Exception | None = None
    for _ in range(retries + 1):
        raw, model_id = _call_llm(user_prompt)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            data = json.loads(cleaned)
            return ModelAssistedFields.model_validate(data), model_id
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            continue
    raise LLMExtractionError(f"could not get a valid structured response after {retries + 1} attempt(s): {last_error}")
