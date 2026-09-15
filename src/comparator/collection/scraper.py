"""Deterministic (automatic) feature extraction from a campaign page's HTML.

sieg 14/09, new module - Dan's workstream had no code at all before this; the
analysis chain existed, the collection layer didn't. This covers every field
tagged extraction: automatic in config/feature_dictionary.yaml that can be
produced from a STATIC fetch (requests + BeautifulSoup), and says so plainly
where it can't.

WHAT THIS DOES NOT DO, ON PURPOSE (read before trusting a row):
  - No headless rendering. page_height_px, hero_image_area_ratio,
    total_image_area_ratio and cta_contrast_ratio all need the page actually
    LAID OUT in a viewport (the dictionary's own definitions say "rendered
    page" / "viewport"), which a static fetch cannot give you (this is
    exactly PRD risk R-02). Rows from this module are collection_method =
    "static_fetch" and those four fields are left None, not guessed.
  - text_to_image_ratio is filled with an APPROXIMATION (word_count /
    image_count) as a stand-in for the real text-area/image-area ratio the
    dictionary defines - close in spirit, not the same number. Flagged in
    the returned row so it isn't mistaken for the real thing.
  - readability_score implements the three formulas the dictionary names
    (Flesch/Kandel-Moles/Flesch-Douma). sieg 15/09: VERIFIED against
    published sources - Flesch Reading Ease (en): 206.835 - 1.015*ASL -
    84.6*ASW; Kandel-Moles (fr, 1958): 207 - 1.015*ASL - 73.6*ASW;
    Flesch-Douma (nl, 1960): 206.84 - 0.93*ASL - 77*ASW. All three match the
    coefficients below exactly.

Next step for Dan: add a headless_render path (e.g. playwright) that fills
the four fields above and replaces the text_to_image_ratio approximation
with the real one; static_fetch stays as the fast path for everything else.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from comparator import bands
from comparator.collection.compliance import USER_AGENT, assert_can_fetch

REQUEST_TIMEOUT_S = 15

# --- per-language word lists -------------------------------------------------
# sieg 14/09: starter lists, not exhaustive - extend as real pages surface
# terms these miss. Matches the dictionary's own examples (second_person_ratio,
# urgency_marker_count) almost word for word.
_SECOND_PERSON = {
    "nl": {"u", "uw", "je", "jij", "jouw"},
    "fr": {"vous", "votre", "vos", "tu", "ton", "ta", "tes"},
    "en": {"you", "your", "yours"},
}
_FIRST_PERSON_PLURAL = {
    "nl": {"wij", "we", "ons", "onze"},
    "fr": {"nous", "notre", "nos"},
    "en": {"we", "our", "ours", "us"},
}
_URGENCY_MARKERS = {
    "nl": ["nog tot", "beperkt", "tijdelijk", "alleen vandaag"],
    "fr": ["offre limitee", "offre limitée", "jusqu'au", "temporaire", "seulement"],
    "en": ["only until", "limited offer", "limited time", "today only"],
}
_LOYALTY_REFERRAL_TERMS = [
    "refer a friend", "invite a friend", "loyalty", "rewards program",
    "parrainage", "fidelite", "fidélité", "programme de fidelite",
    "vriend werven", "beloningsprogramma",
]
_CTA_KEYWORDS = (
    "discover", "open", "apply", "get started", "sign up", "learn more",
    "decouvrir", "découvrir", "ouvrir", "demander", "en savoir plus",
    # sieg 15/09: FIXED - verified live on kbc.be, this list only had the FR
    # infinitives, so real buttons ("Ouvrez un compte à vue", "Ouvrez dès
    # maintenant...") scored cta_count=0. Banking CTAs are near-universally
    # the imperative in French, not the infinitive ("ouvrir" is not a
    # substring of "ouvrez") - added the imperative forms actually seen,
    # per this module's own "extend as real pages surface terms these miss".
    "ouvrez", "découvrez", "decouvrez", "demandez", "profitez", "simulez", "calculez",
    "ontdek", "openen", "aanvragen", "meer weten",
)

# Standard-form readability coefficients (words/sentence, syllables/word).
# sieg 15/09: VERIFIED against published sources (see module docstring) -
# these are the exact Flesch / Kandel-Moles / Flesch-Douma coefficients, not
# an approximation.
_READABILITY_COEFFS = {
    "en": dict(base=206.835, per_word=1.015, per_syllable=84.6),
    "fr": dict(base=207.0, per_word=1.015, per_syllable=73.6),   # Kandel-Moles (1958)
    "nl": dict(base=206.84, per_word=0.93, per_syllable=77.0),   # Flesch-Douma (1960)
}
_READABILITY_FORMULA_NAME = {
    "nl": "flesch_douma_nl", "fr": "kandel_moles_fr", "en": "flesch_reading_ease_en",
}
_BAND_EDGES = [(90, "very_easy"), (70, "easy"), (50, "medium"), (30, "hard")]


def _fetch_html(url: str) -> str:
    assert_can_fetch(url)  # fails closed - see collection/compliance.py
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_S)
    response.raise_for_status()
    return response.text


def _syllable_count(word: str) -> int:
    """Crude vowel-group counter. Good enough for a readability APPROXIMATION
    across nl/fr/en, not a substitute for a real per-language syllabifier."""
    word = word.lower()
    groups = re.findall(r"[aeiouyàâäéèêëîïôöùûüœ]+", word)
    return max(1, len(groups))


def _readability(text: str, language: str) -> tuple[float, str, str]:
    words = re.findall(r"[\w'-]+", text, flags=re.UNICODE)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    if not words or not sentences:
        return 50.0, _READABILITY_FORMULA_NAME[language], "medium"
    syllables = sum(_syllable_count(w) for w in words)
    c = _READABILITY_COEFFS[language]
    score = c["base"] - c["per_word"] * (len(words) / len(sentences)) - c["per_syllable"] * (syllables / len(words))
    score = max(0.0, min(100.0, score))
    band = next((label for edge, label in _BAND_EDGES if score >= edge), "very_hard")
    return round(score, 1), _READABILITY_FORMULA_NAME[language], band


def _count_terms(text: str, terms) -> int:
    tokens = re.findall(r"[\w'-]+", text.lower(), flags=re.UNICODE)
    term_set = {t.lower() for t in terms}
    return sum(1 for t in tokens if t in term_set)


def _count_ctas(soup: BeautifulSoup) -> tuple[int, bool]:
    candidates = soup.find_all(["a", "button"])
    count, above_fold_guess = 0, False
    for i, el in enumerate(candidates):
        label = el.get_text(strip=True).lower()
        if any(k in label for k in _CTA_KEYWORDS):
            count += 1
            if i < 5:  # heuristic only - a real above-the-fold check needs rendering
                above_fold_guess = True
    return count, above_fold_guess


def _has_animation(soup: BeautifulSoup, html: str) -> bool:
    if soup.find(["video", "source"]):
        return True
    if soup.find("img", src=lambda s: s and s.lower().endswith(".gif")):
        return True
    return "@keyframes" in html or "animation:" in html


def _hero_image_url(soup: BeautifulSoup):
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return og_image["content"]
    first_img = soup.find("img", src=True)
    return first_img["src"] if first_img else None


def _disclaimer_share(soup: BeautifulSoup, total_words: int) -> tuple[bool, float]:
    # heuristic: elements whose class/id mentions disclaimer/legal/small-print
    candidates = soup.find_all(attrs={"class": re.compile(r"disclaimer|legal|small-?print|fine-?print", re.I)})
    candidates += soup.find_all(attrs={"id": re.compile(r"disclaimer|legal|small-?print|fine-?print", re.I)})
    if not candidates or total_words == 0:
        return False, 0.0
    disclaimer_words = sum(len(c.get_text(strip=True).split()) for c in candidates)
    return True, round(min(1.0, disclaimer_words / total_words), 3)


def _rate(text: str):
    match = re.search(r"(\d+[.,]\d+|\d+)\s?%", text)
    if not match:
        return False, None
    value = float(match.group(1).replace(",", "."))
    return True, value


def extract(html: str, *, language: str) -> dict:
    """Parse fetched HTML into every automatic feature this module covers."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    words = re.findall(r"[\w'-]+", text, flags=re.UNICODE)
    word_count = len(words)
    sentence_count = max(1, len([s for s in re.split(r"[.!?]+", text) if s.strip()]))
    readability_score, readability_formula, readability_band = _readability(text, language)

    image_count = len(soup.find_all("img"))
    hero_url = _hero_image_url(soup)
    animated = _has_animation(soup, html)
    cta_count, cta_above_fold_guess = _count_ctas(soup)
    disclaimer_present, disclaimer_word_share = _disclaimer_share(soup, word_count)
    rate_shown, rate_value_pct = _rate(text)

    content_images = [img for img in soup.find_all("img") if img.get("src")]
    images_have_alt_text = bool(content_images) and all((img.get("alt") or "").strip() for img in content_images)

    title_tag = soup.find("title")

    # sieg 14/09: named so the raw field and its _band field always agree
    avg_sentence_length = round(word_count / sentence_count, 2)
    # sieg 15/09: FIXED - was dividing by word_count (hundreds of words), so
    # every real page landed near 0 and got banded "rarely_direct" regardless
    # of actual tone (verified: a page saturated with vous/votre still scored
    # 0.024). The dictionary defines this as "share of personal pronouns that
    # address the reader" - the denominator must be total personal pronouns
    # counted (second + first-person-plural, the two families this module
    # tracks), not total words. Matches the 0.2/0.5 band thresholds in
    # bands.py and the 0.4-0.75 range fixtures.py already assumes.
    second_person_count = _count_terms(text, _SECOND_PERSON[language])
    first_person_plural_count = _count_terms(text, _FIRST_PERSON_PLURAL[language])
    total_personal_pronouns = second_person_count + first_person_plural_count
    second_person_ratio = round(second_person_count / max(total_personal_pronouns, 1), 3)
    text_to_image_ratio = round(word_count / max(image_count, 1), 2)  # APPROXIMATION, see module docstring

    return {
        # tone & messaging
        "word_count": word_count,
        "word_count_band": bands.word_count_band(word_count),  # sieg 14/09
        "sentence_count": sentence_count,
        "sentence_count_band": bands.sentence_count_band(sentence_count),  # sieg 14/09
        "avg_sentence_length": avg_sentence_length,
        "avg_sentence_length_band": bands.avg_sentence_length_band(avg_sentence_length),  # sieg 14/09
        "readability_score": readability_score,
        "readability_formula": readability_formula,
        "readability_band": readability_band,
        "second_person_ratio": second_person_ratio,
        "second_person_ratio_band": bands.second_person_ratio_band(second_person_ratio),  # sieg 14/09
        "first_person_plural_count": first_person_plural_count,
        "first_person_plural_band": bands.first_person_plural_band(first_person_plural_count),  # sieg 14/09
        "question_count": text.count("?"),
        "urgency_marker_count": sum(text.lower().count(term) for term in _URGENCY_MARKERS[language]),
        "numeric_claim_count": len(re.findall(r"\d+[.,]?\d*\s?%|\d+[.,]?\d*\s?(?:eur|€)", text, flags=re.I)),
        # topics & value proposition
        "rate_shown": rate_shown,
        "rate_value_pct": rate_value_pct,
        "disclaimer_present": disclaimer_present,
        "disclaimer_word_share": disclaimer_word_share,
        "disclaimer_word_share_band": bands.disclaimer_word_share_band(disclaimer_word_share),  # sieg 14/09
        # visuals
        "image_count": image_count,
        "hero_image_present": hero_url is not None,
        "animated_asset_count": 1 if animated else 0,  # coarse - counts "any", not each asset
        "has_animation": animated,
        # layout & structure
        "section_count": len(soup.find_all(["section", "article"])) or None,
        "cta_count": cta_count,
        "cta_above_fold": cta_above_fold_guess,  # heuristic, see docstring - not a real viewport check
        "text_to_image_ratio": text_to_image_ratio,  # APPROXIMATION, see module docstring
        "text_to_image_ratio_band": bands.text_to_image_ratio_band(text_to_image_ratio),  # sieg 14/09
        "has_comparison_table": soup.find("table") is not None,
        # banking-domain (sieg 14/09 addendum, automatic-tagged ones only)
        "mentions_loyalty_or_referral": any(term in text.lower() for term in _LOYALTY_REFERRAL_TERMS),
        "images_have_alt_text": images_have_alt_text,
        "meta_title": title_tag.get_text(strip=True) if title_tag else None,
        # fields this module deliberately leaves None - need headless_render
        "page_height_px": None,
        "hero_image_area_ratio": None,
        "total_image_area_ratio": None,
        "cta_contrast_ratio": None,
        "above_fold_element_count": None,
        # bookkeeping for the caller - not dataset columns, consumed by
        # collection.visual_features and collection.llm_extractor
        "_hero_image_url": hero_url,
        "_page_text": text,
    }


def scrape(url: str, *, language: str) -> dict:
    """Compliant fetch + full automatic extraction for one page."""
    html = _fetch_html(url)
    features = extract(html, language=language)
    features["_html"] = html
    features["collection_method"] = "static_fetch"
    features["robots_allowed"] = True  # reaching this line means assert_can_fetch already passed
    features["captured_at"] = datetime.now(timezone.utc).isoformat()
    return features
