"""Generate a 10-page ING campaign website from the selected recommendations.

steph 18/09, new module, stretch on top of step 5. The campaign generator
(`generation.py`) writes one page and scores it. This writes a small site and
deliberately does NOT score it - the scorecard belongs to the single-page loop.
What this module is for is showing a recommendation turned into something a
stakeholder can click through, in ING's own house style.

Two things are kept apart on purpose:

  * The SKELETON is fixed here in code - ten page keys, a shared nav, a shared
    stylesheet. A model asked to invent a site invents a different site every
    time, and a different site cannot be compared with the last one.
  * The CONTENT is written by the pinned model (D6), one call per page, in
    French (fr-BE), from the selected recommendations only. One page failing
    does not take the other nine with it.

House style is ING's current ing.be look, reusing their own published assets:
the logo and illustration SVGs are fetched from ing.be / assets.ing.com and
served locally with the site, and the palette is the brand's own - orange
#FF6200, ING blue #000066, black and white. Nothing here redraws the logo.

No rate, fee or product term is ever invented: the copy model is told to use a
[RATE]-style placeholder where a figure belongs, exactly like `generation.py`.
"""

from __future__ import annotations

import html as html_lib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import requests
from pydantic import BaseModel, Field, ValidationError

from comparator.collection.llm_extractor import LLMExtractionError, _call_llm
from comparator.recommendations import RecommendationSet

# -----------------------------------------------------------------------------
# The fixed skeleton
# -----------------------------------------------------------------------------
ASSET_BASE = "web/public/ing-assets"


@dataclass(frozen=True)
class PageSpec:
    slug: str
    purpose: str
    image: str


# Ten pages, fixed keys. `purpose` is the model's brief and stays in English -
# it is engineering metadata, not page copy. Everything a reader sees is
# localised below, chrome included: a French body under a Dutch navigation is
# exactly the language mix this module must not produce.
PAGES: tuple[PageSpec, ...] = (
    PageSpec("index",
             "the savings home page: the promise, the product tiles and the clearest possible next step",
             "home"),
    PageSpec("comptes-epargne",
             "the flagship savings-account page: rate, benefit, how to open, reassurance",
             "savings"),
    PageSpec("compte-a-terme",
             "the term-account page: fixed term, fixed rate placeholder, comparison with a savings account",
             "term"),
    PageSpec("compte-courant",
             "the current-account pack: everyday banking, card, fees transparency, switching",
             "current"),
    PageSpec("jeunes",
             "the youth page: an account for a child or student, opened by a parent, in plain language",
             "youth"),
    PageSpec("investir",
             "the investment page: first-time-investor framing, risk warning, clear next step",
             "invest"),
    PageSpec("credit-hypothecaire",
             "the mortgage page: the offer, the legal TAEG disclosure, an appointment CTA",
             "mortgage"),
    PageSpec("ouvrir-compte",
             "the digital onboarding page: how fast it is, what is needed, start now",
             "onboarding"),
    PageSpec("pourquoi-ing",
             "the trust page: what ING stands for, digital plus human, customer protections",
             "why"),
    PageSpec("contact",
             "the contact and FAQ page: the most common questions answered, routes to a human",
             "contact"),
)

PAGE_BY_SLUG = {p.slug: p for p in PAGES}

# One label set per page, per language. The slug stays French in every case
# because it is a file name and a recommendation target, not copy.
NAV_LABELS: dict[str, dict[str, str]] = {
    "fr": {
        "index": "Accueil", "comptes-epargne": "Comptes d'épargne", "compte-a-terme": "Compte à terme",
        "compte-courant": "Compte courant", "jeunes": "Jeunes", "investir": "Investir",
        "credit-hypothecaire": "Crédit hypothécaire", "ouvrir-compte": "Ouvrir un compte",
        "pourquoi-ing": "Pourquoi ING", "contact": "Contact",
    },
    "nl": {
        "index": "Home", "comptes-epargne": "Spaarrekeningen", "compte-a-terme": "Termijnrekening",
        "compte-courant": "Zichtrekening", "jeunes": "Jongeren", "investir": "Beleggen",
        "credit-hypothecaire": "Hypothecair krediet", "ouvrir-compte": "Rekening openen",
        "pourquoi-ing": "Waarom ING", "contact": "Contact",
    },
    "en": {
        "index": "Home", "comptes-epargne": "Savings accounts", "compte-a-terme": "Term account",
        "compte-courant": "Current account", "jeunes": "Youth", "investir": "Invest",
        "credit-hypothecaire": "Mortgage", "ouvrir-compte": "Open an account",
        "pourquoi-ing": "Why ING", "contact": "Contact",
    },
}

# Fallback page titles, used only when the model did not return a page.
PAGE_TITLES: dict[str, dict[str, str]] = {
    "fr": {
        "index": "Épargner avec ING", "comptes-epargne": "Comptes d'épargne",
        "compte-a-terme": "Compte à terme", "compte-courant": "Compte courant et carte",
        "jeunes": "Comptes pour enfants et jeunes", "investir": "Investir",
        "credit-hypothecaire": "Crédit hypothécaire", "ouvrir-compte": "Ouvrir un compte en ligne",
        "pourquoi-ing": "Pourquoi ING", "contact": "Contact et questions",
    },
    "nl": {
        "index": "Sparen met ING", "comptes-epargne": "Spaarrekeningen",
        "compte-a-terme": "Termijnrekening", "compte-courant": "Zichtrekening en kaart",
        "jeunes": "Rekeningen voor kinderen en jongeren", "investir": "Beleggen",
        "credit-hypothecaire": "Hypothecair krediet", "ouvrir-compte": "Online een rekening openen",
        "pourquoi-ing": "Waarom ING", "contact": "Contact en vragen",
    },
    "en": {
        "index": "Save with ING", "comptes-epargne": "Savings accounts",
        "compte-a-terme": "Term account", "compte-courant": "Current account and card",
        "jeunes": "Accounts for children and young people", "investir": "Invest",
        "credit-hypothecaire": "Mortgage", "ouvrir-compte": "Open an account online",
        "pourquoi-ing": "Why ING", "contact": "Contact and questions",
    },
}

# Every fixed string in the shell, so the chrome follows the chosen language
# instead of silently staying French.
UI: dict[str, dict[str, str]] = {
    "fr": {
        "locale_label": "Français", "search": "Que recherchez-vous ?", "contact": "Contact",
        "services": "Services", "login": "Connexion", "open": "Ouvrir un compte",
        "faq_heading": "Questions fréquentes",
        "band_heading": "Prêt à passer à l'action ?", "band_button": "Ouvrir un compte",
        "products": "Produits", "help": "Besoin d'aide ?",
        "nav_savings": "Épargne", "nav_term": "Compte à terme", "nav_invest": "Investir",
        "nav_open": "Ouvrir un compte", "nav_contact": "Contact", "nav_why": "Pourquoi ING",
        "nav_faq": "Questions fréquentes",
        "fallback_disclaimer": "Texte légal à compléter par les équipes conformité. Taux et conditions à confirmer.",
        "fallback_heading": "À propos de cette page",
        "fallback_body": "Cette page n'a pas pu être générée à temps. Le contenu sera complété.",
        "foot_legal": ("Site de démonstration généré à partir d'une analyse comparative. Aucun taux, "
                       "montant ou condition ne doit être considéré comme une offre réelle."),
    },
    "nl": {
        "locale_label": "Nederlands", "search": "Waar zoekt u naar?", "contact": "Contact",
        "services": "Diensten", "login": "Aanmelden", "open": "Rekening openen",
        "faq_heading": "Veelgestelde vragen",
        "band_heading": "Klaar om te starten?", "band_button": "Rekening openen",
        "products": "Producten", "help": "Hulp nodig?",
        "nav_savings": "Sparen", "nav_term": "Termijnrekening", "nav_invest": "Beleggen",
        "nav_open": "Rekening openen", "nav_contact": "Contact", "nav_why": "Waarom ING",
        "nav_faq": "Veelgestelde vragen",
        "fallback_disclaimer": "Juridische tekst aan te vullen door de compliance-teams. Tarieven en voorwaarden te bevestigen.",
        "fallback_heading": "Over deze pagina",
        "fallback_body": "Deze pagina kon niet op tijd worden gegenereerd. De inhoud wordt aangevuld.",
        "foot_legal": ("Demonstratiesite gegenereerd op basis van een vergelijkende analyse. Geen enkel "
                       "tarief, bedrag of voorwaarde mag als een reëel aanbod worden beschouwd."),
    },
    "en": {
        "locale_label": "English", "search": "What are you looking for?", "contact": "Contact",
        "services": "Services", "login": "Log in", "open": "Open an account",
        "faq_heading": "Frequently asked questions",
        "band_heading": "Ready to get started?", "band_button": "Open an account",
        "products": "Products", "help": "Need help?",
        "nav_savings": "Savings", "nav_term": "Term account", "nav_invest": "Invest",
        "nav_open": "Open an account", "nav_contact": "Contact", "nav_why": "Why ING",
        "nav_faq": "Frequently asked questions",
        "fallback_disclaimer": "Legal text to be completed by the compliance teams. Rates and conditions to be confirmed.",
        "fallback_heading": "About this page",
        "fallback_body": "This page could not be generated in time. The content will be completed.",
        "foot_legal": ("Demonstration site generated from a comparative analysis. No rate, amount or "
                       "condition should be treated as a real offer."),
    },
}


def nav_label(slug: str, language: str) -> str:
    table = NAV_LABELS.get(language, NAV_LABELS["fr"])
    return table.get(slug, slug)


def ui(language: str, key: str) -> str:
    table = UI.get(language, UI["fr"])
    return table.get(key, UI["fr"].get(key, key))

# The illustrations are ING's own published SVGs. Downloaded once, then served
# with the generated site so the pages do not depend on a live third party.
#
# logo-full is ING's official two-colour logo (blue #006 wordmark, orange #f60
# lion). The white-on-dark header version is derived from it below by recoloring
# only the wordmark, because the "white" logo the CDN serves is in fact the blue
# one - which is what made "ING" almost invisible on our black masthead.
ASSETS: dict[str, str] = {
    "logo-full": "https://assets.ing.com/m/2aca6424a136d895/original/ing-logo-full.svg",
    "home": "https://assets.ing.com/m/23738d6568dacbac/original/Woman-relax-yoga-coins-scene-1.svg",
    "savings": "https://assets.ing.com/m/e6f4e29d58b8378/original/Money-calendar-coins.svg",
    "term": "https://assets.ing.com/m/564b42e7cfd964d9/original/Calculator-2-1.svg",
    "current": "https://assets.ing.com/m/7a2129767fd78dda/original/handshake.svg",
    "youth": "https://assets.ing.com/m/3acbbaeee094da51/original/House-with-green_Spot.svg",
    "invest": "https://assets.ing.com/m/23738d6568dacbac/original/Woman-relax-yoga-coins-scene-1.svg",
    "mortgage": "https://assets.ing.com/m/3acbbaeee094da51/original/House-with-green_Spot.svg",
    "onboarding": "https://assets.ing.com/m/3d2cefbba16f577b/original/Fingerprint-phone-hand-spot.svg",
    "why": "https://assets.ing.com/m/7a2129767fd78dda/original/handshake.svg",
    "contact": "https://assets.ing.com/m/3d2cefbba16f577b/original/Fingerprint-phone-hand-spot.svg",
}

LANGUAGES = {
    "fr": ("fr-BE", "Belgian French",
           "VERPLICHT/OBLIGATOIRE : tout le texte est en français de Belgique. "
           "Pas un seul mot en néerlandais, pas un seul mot en anglais."),
    "nl": ("nl-BE", "Belgian Dutch",
           "VERPLICHT: alle tekst is in het Nederlands van België. "
           "Geen enkel woord in het Frans, geen enkel woord in het Engels."),
    "en": ("en-BE", "English",
           "MANDATORY: every word of the copy is in English. "
           "Not a single word in French or Dutch."),
}


# -----------------------------------------------------------------------------
# What the model returns, per page
# -----------------------------------------------------------------------------
class Hero(BaseModel):
    eyebrow: str
    headline: str
    subheading: str
    primary_cta: str
    secondary_cta: str | None = None
    image: str = "home"


class Section(BaseModel):
    heading: str
    body: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    cta_label: str | None = None


class Faq(BaseModel):
    q: str
    a: str


class PageContent(BaseModel):
    slug: str
    page_title: str
    meta_description: str
    hero: Hero
    sections: list[Section] = Field(default_factory=list)
    faq: list[Faq] = Field(default_factory=list)
    disclaimer: str
    recommendations_implemented: list[str] = Field(default_factory=list)


PAGE_SYSTEM_PROMPT = """You write website copy for ING Belgium in its own plain, confident
tone: short sentences, direct address, no jargon, no exclamation marks, no hype. You write ONE
page of a ten-page savings website. You are given the page's purpose, the navigation, the ING
tone rules, and a set of selected recommendations the page must implement.

LANGUAGE IS MANDATORY, and it is the first thing to get right:
- Write EVERY string you return - every headline, paragraph, bullet, question, answer, call to
  action, eyebrow and disclaimer - in the ONE requested language.
- Never mix languages. Never fall back to the language of the brief, of the recommendations, of
  the slugs, or of ING's other markets.
- Page slugs like "comptes-epargne" are file names and identifiers. They are NOT a language
  instruction. The requested language is stated explicitly and overrides everything else.
- If the requested language is French, address the reader as "vous" and use "votre/vos".
  If Dutch, use "u/uw". If English, use "you/your".

Hard rules, no exceptions:
- Never invent a rate, price, fee, return or product term. Where a figure belongs, write the
  placeholder [TAUX], [MONTANT] or [DUREE] exactly.
- Never invent a legal or regulatory text. Put a short, clearly-placeholder disclaimer.
- Do not mention any competitor by name, and never reuse a competitor's wording.
- Implement the selected recommendations concretely in the copy and structure where this page is
  an appropriate place to do so; list the ids you actually implemented.
- The call to action must be an unmistakable next step, visible at the top of the page.

Return ONLY a JSON object with exactly these keys:
"slug" (the exact slug given to you),
"page_title" (for the browser tab),
"meta_description" (one sentence),
"hero" (object with: "eyebrow", "headline", "subheading", "primary_cta",
  "secondary_cta" (string or null), "image" (one of the asset keys given to you)),
"sections" (array of 3 to 5 objects, each with: "heading", "body" (array of 1-3 paragraphs),
  "bullets" (array of 0-4 short strings), "cta_label" (string or null)),
"faq" (array of 3 to 5 objects, each with "q" and "a"),
"disclaimer" (the placeholder legal line for this page),
"recommendations_implemented" (array of the recommendation ids you implemented).

No preamble, no markdown fences, JSON only."""


def _rec_brief(recs: RecommendationSet) -> str:
    lines = []
    for r in recs.recommendations:
        lines.append(
            f"- {r.id} [{r.priority}] {r.title}\n"
            f"  finding: {r.finding}\n"
            f"  action: {r.recommendation}\n"
            f"  features: {', '.join(r.features) or 'n/a'}"
        )
    return "\n".join(lines)


def _page_prompt(spec: PageSpec, recs: RecommendationSet, language: str, site_summary: str) -> str:
    locale, language_name, language_rule = LANGUAGES.get(language, LANGUAGES["fr"])
    nav = " | ".join(f"{p.slug} ({nav_label(p.slug, language)})" for p in PAGES)
    return (
        f"!!! REQUESTED LANGUAGE: {language_name} ({locale}). {language_rule}\n"
        f"Write the ENTIRE page in {language_name}. Do not mix in any other language, "
        f"not even for a product name or a single heading.\n\n"
        f"Global positioning for the site: {site_summary}\n\n"
        f"This page: slug={spec.slug}; navigation label in the requested language="
        f"\"{nav_label(spec.slug, language)}\"; purpose={spec.purpose}\n\n"
        f"The ten pages (slug and its label in the requested language): {nav}\n"
        f"Asset keys you may use for hero.image: home, savings, term, current, youth, invest, "
        f"mortgage, onboarding, why, contact. Pick the one that best fits this page; "
        f"{spec.image} is the natural default.\n\n"
        f"Selected recommendations this page should help implement (written in English - read "
        f"them, but output {language_name}):\n{_rec_brief(recs)}\n\n"
        f"Reminder: the final output must be entirely in {language_name}."
    )


# Cheap language check, not a classifier: a handful of high-frequency function
# words per language is enough to catch the failure that actually happened -
# the model writing Dutch for a Belgian bank when French was requested. It runs
# on generated content only, never on the localised chrome, which would bias it.
_LANGUAGE_MARKERS: dict[str, tuple[str, ...]] = {
    "fr": (" le ", " la ", " les ", " des ", " une ", " pour ", " vous ", " votre ", " vos ",
           " avec ", " dans ", " sur ", " est ", " sont ", " plus ", " nous ", " nos ", " et ",
           "du ", "au ", "que ", "qui "),
    "nl": (" de ", " het ", " een ", " voor ", " u ", " uw ", " met ", " in ", " op ", " van ",
           " en ", " is ", " zijn ", " meer ", " bij ", " niet ", " ook ", " dat ", " die ",
           "wij ", "onze "),
    "en": (" the ", " a ", " an ", " for ", " you ", " your ", " with ", " in ", " on ", " of ",
           " and ", " is ", " are ", " more ", " at ", " not ", " also ", " that ", " this ",
           "we ", "our "),
}


def _detected_language(text: str) -> str | None:
    lowered = f" {text.lower()} "
    scores = {lang: sum(lowered.count(m) for m in markers)
              for lang, markers in _LANGUAGE_MARKERS.items()}
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return None
    # A near-tie is not evidence either way; only report a clear winner.
    ordered = sorted(scores.values(), reverse=True)
    if len(ordered) > 1 and ordered[0] - ordered[1] < 2:
        return None
    return best


def _content_text(page: PageContent) -> str:
    parts = [page.hero.eyebrow, page.hero.headline, page.hero.subheading, page.hero.primary_cta]
    for s in page.sections:
        parts += [s.heading, *s.body, *s.bullets]
    for f in page.faq:
        parts += [f.q, f.a]
    return " ".join(p for p in parts if p)


def generate_page(spec: PageSpec, recs: RecommendationSet, language: str, site_summary: str,
                  *, retries: int = 2) -> PageContent:
    last_error: Exception | None = None
    for _ in range(retries + 1):
        raw, _model = _call_llm(
            _page_prompt(spec, recs, language, site_summary),
            system_prompt=PAGE_SYSTEM_PROMPT,
            timeout=180,
        )
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            data = json.loads(cleaned)
            data["slug"] = spec.slug
            data.setdefault("hero", {})
            if isinstance(data["hero"], dict):
                data["hero"].setdefault("image", spec.image)
            page = PageContent.model_validate(data)
        except (json.JSONDecodeError, ValidationError, KeyError, TypeError) as exc:
            last_error = exc
            continue

        detected = _detected_language(_content_text(page))
        if detected is not None and detected != language:
            # The model answered in the wrong language. That is the one error a
            # reader will notice immediately, so it is worth another call.
            last_error = LLMExtractionError(
                f"page came back in {detected} but {language} was requested"
            )
            continue
        return page

    raise LLMExtractionError(f"page {spec.slug} did not return valid content: {last_error}")


# -----------------------------------------------------------------------------
# Rendering - ING house style
# -----------------------------------------------------------------------------
def _esc(value) -> str:
    return html_lib.escape(str(value if value is not None else ""))


def _paragraphs(items: list[str]) -> str:
    return "".join(f"<p>{_esc(p)}</p>" for p in items if str(p).strip())


def _bullets(items: list[str]) -> str:
    if not items:
        return ""
    return "<ul>" + "".join(f"<li>{_esc(b)}</li>" for b in items if str(b).strip()) + "</ul>"


def _hero_image(image: str) -> str:
    name = image if image in ASSETS else "home"
    file = f"{name}.svg"
    return f'<img class="hero-illu" src="assets/{_esc(file)}" alt="">'


def _nav(current: str, language: str) -> str:
    links = []
    for p in PAGES:
        cls = ' class="active"' if p.slug == current else ""
        href = "index.html" if p.slug == "index" else f"{p.slug}.html"
        links.append(f'<a{cls} href="{href}">{_esc(nav_label(p.slug, language))}</a>')
    return "".join(links)


def _sections(sections: list[Section]) -> str:
    out = []
    for i, s in enumerate(sections):
        cta = (
            f'<a class="btn btn-primary" href="ouvrir-compte.html">{_esc(s.cta_label)}</a>'
            if s.cta_label else ""
        )
        out.append(
            f'<section class="block{" alt" if i % 2 else ""}"><div class="wrap">'
            f'<h2>{_esc(s.heading)}</h2>{_paragraphs(s.body)}{_bullets(s.bullets)}{cta}'
            f"</div></section>"
        )
    return "".join(out)


def _faq(items: list[Faq], language: str) -> str:
    if not items:
        return ""
    rows = "".join(
        f"<details><summary>{_esc(f.q)}</summary><div>{_esc(f.a)}</div></details>"
        for f in items
    )
    return (f'<section class="block"><div class="wrap"><h2>{_esc(ui(language, "faq_heading"))}</h2>'
            f"{rows}</div></section>")


def render_page(content: PageContent, language: str) -> str:
    locale, _name, _rule = LANGUAGES.get(language, LANGUAGES["fr"])
    hero = content.hero
    secondary_link = (
        f'<a class="btn btn-ghost" href="contact.html">{_esc(hero.secondary_cta)}</a>'
        if hero.secondary_cta else ""
    )
    return f"""<!doctype html>
<html lang="{_esc(locale)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(content.page_title)} · ING</title>
<meta name="description" content="{_esc(content.meta_description)}">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<div class="utility"><div class="wrap">
<span class="u-active">Particuliers</span><a href="#">Business</a><a href="#">Private Banking</a>
<span class="u-lang">{_esc(ui(language, "locale_label"))} ▾</span>
</div></div>
<header class="masthead"><div class="wrap masthead-in">
<a class="logo" href="index.html"><img src="assets/logo-white.svg" alt="ING"></a>
<div class="search"><input type="search" placeholder="{_esc(ui(language, "search"))}" aria-label="{_esc(ui(language, "search"))}"><span aria-hidden="true">⌕</span></div>
<nav class="actions">
<a href="contact.html">◎ {_esc(ui(language, "contact"))}</a><a href="index.html">▦ {_esc(ui(language, "services"))}</a>
<a class="pill-outline" href="ouvrir-compte.html">{_esc(ui(language, "login"))}</a>
<a class="pill-fill" href="ouvrir-compte.html">{_esc(ui(language, "open"))}</a>
</nav>
</div>
<nav class="mainnav" aria-label="Principal"><div class="wrap">{_nav(content.slug, language)}</div></nav>
</header>

<main id="main">
<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <div class="eyebrow">{_esc(hero.eyebrow)}</div>
      <h1>{_esc(hero.headline)}</h1>
      <p class="lede">{_esc(hero.subheading)}</p>
      <div class="hero-cta">
        <a class="btn btn-primary" href="ouvrir-compte.html">{_esc(hero.primary_cta)}</a>
        {secondary_link}
      </div>
    </div>
    <div class="hero-art">{_hero_image(hero.image)}</div>
  </div>
</section>

{_sections(content.sections)}
{_faq(content.faq, language)}
</main>

<section class="cta-band"><div class="wrap">
<h2>{_esc(ui(language, "band_heading"))}</h2>
<a class="btn btn-dark" href="ouvrir-compte.html">{_esc(ui(language, "band_button"))}</a>
</div></section>

<footer class="foot"><div class="wrap">
<img class="foot-logo" src="assets/logo-white.svg" alt="ING">
<div class="foot-cols">
<div><strong>{_esc(ui(language, "products"))}</strong><a href="comptes-epargne.html">{_esc(ui(language, "nav_savings"))}</a><a href="compte-a-terme.html">{_esc(ui(language, "nav_term"))}</a><a href="investir.html">{_esc(ui(language, "nav_invest"))}</a></div>
<div><strong>{_esc(ui(language, "services"))}</strong><a href="ouvrir-compte.html">{_esc(ui(language, "nav_open"))}</a><a href="contact.html">{_esc(ui(language, "nav_contact"))}</a><a href="pourquoi-ing.html">{_esc(ui(language, "nav_why"))}</a></div>
<div><strong>{_esc(ui(language, "help"))}</strong><a href="contact.html">{_esc(ui(language, "nav_faq"))}</a><a href="contact.html">{_esc(ui(language, "nav_contact"))}</a></div>
</div>
<p class="disclaimer">{_esc(content.disclaimer)}</p>
<p class="foot-legal">{_esc(ui(language, "foot_legal"))}</p>
</div></footer>
</body>
</html>"""


ASSETS_CSS = """/* ING house style, reusing the palette of ing.be: orange #FF6200, ING blue
   #000066, black and white. Type falls back through the ING stack to system
   sans, because the licensed ING fonts are not redistributed with a demo. */
:root{--orange:#ff6200;--blue:#000066;--ink:#08080b;--panel:#141419;--line:#3a3a44;
--muted:#c7c8cf;--radius:22px;--maxw:1180px;
--sans:"ING Me",ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:#000;color:#fff;font-family:var(--sans);font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.skip-link{position:absolute;left:-9999px;top:0;background:#fff;color:#111;padding:10px 16px;z-index:100}
.skip-link:focus{left:16px;top:12px}
:focus-visible{outline:3px solid #fff;outline-offset:2px}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}
.utility{background:#fff;color:#111;font-size:13px}
.utility .wrap{display:flex;gap:22px;align-items:center;height:44px}
.utility a{color:#45454d}
.utility .u-active{font-weight:700;color:#111}
.utility .u-lang{margin-left:auto;color:#45454d}
.masthead{background:#000;border-bottom:1px solid var(--line);padding-top:14px}
.masthead-in{display:flex;align-items:center;gap:20px;padding-bottom:12px}
.logo img{height:34px;display:block}
.search{flex:1;display:flex;align-items:center;background:#232329;border:1px solid #4a4a55;border-radius:999px;padding:8px 16px;max-width:520px}
.search input{flex:1;background:none;border:0;color:#fff;font-size:14px;outline:none}
.search input::placeholder{color:#c7c8cf}
.search span{color:var(--orange)}
.actions{display:flex;align-items:center;gap:18px;font-size:14px;white-space:nowrap}
.pill-outline{border:1.5px solid #fff;border-radius:999px;padding:8px 18px;font-weight:600}
.pill-fill{background:#7a7aec;border-radius:999px;padding:9px 20px;font-weight:700;color:#0a0a0f}
.mainnav{border-top:1px solid var(--line)}
.mainnav .wrap{display:flex;gap:26px;flex-wrap:wrap;padding:12px 24px;font-size:14.5px}
.mainnav a{color:#e2e2e8;padding:2px 0}
.mainnav a.active{color:#fff;font-weight:700;box-shadow:inset 0 -3px 0 var(--orange)}
.hero{background:radial-gradient(1200px 500px at 80% -10%,#241606 0,#000 60%);padding:56px 0 44px}
.hero-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:40px;align-items:center}
.eyebrow{color:#ff8a3d;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:12.5px}
.hero h1{font-size:clamp(34px,5vw,58px);line-height:1.05;letter-spacing:-.02em;margin:10px 0 14px}
.lede{color:var(--muted);font-size:19px;max-width:52ch;margin:0 0 24px}
.hero-cta{display:flex;gap:12px;flex-wrap:wrap}
.hero-illu{width:100%;max-height:360px;object-fit:contain;display:block}
.btn{display:inline-block;border-radius:12px;padding:14px 24px;font-weight:700;font-size:15px}
.btn-primary{background:var(--orange);color:#0a0a0f}
.btn-dark{background:#000;color:#fff;border:1.5px solid #000}
.btn-ghost{border:1.5px solid #fff;color:#fff}
.block{padding:52px 0}
.block.alt{background:var(--panel)}
.block h2{font-size:clamp(24px,3vw,34px);letter-spacing:-.015em;margin:0 0 14px}
.block p{color:var(--muted);font-size:16.5px;max-width:72ch}
.block ul{color:var(--muted);font-size:16.5px;max-width:72ch;padding-left:20px}
.block ul li{margin:6px 0}
.block .btn{margin-top:14px}
details{border-bottom:1px solid var(--line);padding:16px 0}
summary{cursor:pointer;font-weight:650;font-size:16.5px;list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"+";color:var(--orange);font-weight:700;margin-right:10px}
details[open] summary::before{content:"–"}
details div{color:var(--muted);padding:10px 0 2px 22px;max-width:78ch}
.cta-band{background:var(--orange);color:#0a0a0f;padding:44px 0}
.cta-band .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}
.cta-band h2{margin:0;font-size:clamp(22px,3vw,30px)}
.foot{background:#000;border-top:1px solid var(--line);padding:44px 0 60px}
.foot-logo{height:30px;margin-bottom:22px}
.foot-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:22px;margin-bottom:26px}
.foot-cols strong{display:block;margin-bottom:8px;color:#fff}
.foot-cols a{display:block;color:var(--muted);font-size:14px;padding:3px 0}
.disclaimer{color:var(--muted);font-size:12.5px;max-width:80ch;border-top:1px solid var(--line);padding-top:18px}
.foot-legal{color:var(--muted);font-size:12px;max-width:80ch}
@media(max-width:820px){.hero-grid{grid-template-columns:1fr}.actions{display:none}.masthead-in{gap:12px}}
"""


# -----------------------------------------------------------------------------
# Assets + orchestration
# -----------------------------------------------------------------------------
def _download_assets(dest: Path) -> list[str]:
    """Fetch ING's own logo and illustrations once, keep them with the site.

    A generated site that hot-links ing.be would break the moment they move an
    asset, and would quietly call out to a third party every time someone opens
    a demo. Copied locally instead; a failure to fetch one image is not fatal.
    """
    dest.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    for key, url in ASSETS.items():
        target = dest / f"{key}.svg"
        if target.is_file() and target.stat().st_size > 0:
            continue
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            target.write_bytes(response.content)
        except requests.RequestException as exc:
            warnings.append(f"could not fetch {key}: {exc}")

    # White-on-dark logo: ING's own logo with only the blue wordmark recolored,
    # so the orange lion and the white details stay exactly as published. Dark
    # blue #000066 on the black masthead measured ~1.3:1 contrast - unreadable.
    # Rebuilt every run rather than cached: an earlier version of this function
    # shipped the blue-on-black logo, and a stale cache would keep it forever.
    full = dest / "logo-full.svg"
    white = dest / "logo-white.svg"
    if full.is_file():
        try:
            svg = full.read_text(encoding="utf-8")
            svg = svg.replace('fill="#006"', 'fill="#ffffff"').replace('fill="#000066"', 'fill="#ffffff"')
            _safe_write(white, svg)
        except OSError as exc:
            warnings.append(f"could not build the white logo: {exc}")
    return warnings


def _safe_write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def generate_site(
    report: dict,
    recommendations: RecommendationSet,
    *,
    language: str = "fr",
    out_dir: Path,
    on_progress: Callable[[int, int, str], None] | None = None,
    max_workers: int = 3,
) -> dict:
    """Build the ten pages and return a manifest.

    One model call per page, in parallel. A page that fails after its retries is
    rendered from a deterministic fallback so the site still has all ten pages -
    the manifest records which ones those were, so a demo cannot quietly pass a
    fallback off as generated copy.
    """
    language = language if language in LANGUAGES else "fr"
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = out_dir / "assets"
    asset_warnings = _download_assets(assets_dir)
    _safe_write(assets_dir / "site.css", ASSETS_CSS)

    summary = recommendations.summary or "ING savings, made clear and easy to start."

    contents: dict[str, PageContent] = {}
    failures: list[str] = []
    done = 0

    def work(spec: PageSpec) -> tuple[str, PageContent, str | None]:
        try:
            return spec.slug, generate_page(spec, recommendations, language, summary), None
        except LLMExtractionError as exc:
            return spec.slug, _fallback_page(spec, summary, language), str(exc)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(work, spec): spec for spec in PAGES}
        for future in as_completed(futures):
            slug, content, error = future.result()
            contents[slug] = content
            if error:
                failures.append(slug)
            done += 1
            if on_progress:
                on_progress(done, len(PAGES), slug)

    for spec in PAGES:
        _safe_write(out_dir / f"{spec.slug}.html", render_page(contents[spec.slug], language))

    manifest = {
        "language": language,
        "locale": LANGUAGES[language][0],
        "generated_at": report.get("generated_at"),
        "model": recommendations.model,
        "pages": [
            {
                "slug": spec.slug,
                "nav": nav_label(spec.slug, language),
                "title": contents[spec.slug].page_title,
                "file": "index.html" if spec.slug == "index" else f"{spec.slug}.html",
                "used_fallback": spec.slug in failures,
                "recommendations_implemented": contents[spec.slug].recommendations_implemented,
            }
            for spec in PAGES
        ],
        "recommendations": [
            {"id": r.id, "title": r.title, "priority": r.priority}
            for r in recommendations.recommendations
        ],
        "asset_warnings": asset_warnings,
    }
    _safe_write(out_dir / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


def _fallback_page(spec: PageSpec, summary: str, language: str = "fr") -> PageContent:
    """A complete, honest page when the model did not deliver one.

    Not hidden: the manifest marks it. This exists so a partial model outage
    costs one page of copy rather than the whole demo. It is localised too -
    a French placeholder under Dutch chrome would be the same language mix.
    """
    return PageContent(
        slug=spec.slug,
        page_title=PAGE_TITLES.get(language, PAGE_TITLES["fr"]).get(spec.slug, spec.slug),
        meta_description=spec.purpose,
        hero=Hero(
            eyebrow=nav_label(spec.slug, language),
            headline=PAGE_TITLES.get(language, PAGE_TITLES["fr"]).get(spec.slug, spec.slug),
            subheading=summary,
            primary_cta=ui(language, "open"),
            secondary_cta=ui(language, "contact"),
            image=spec.image,
        ),
        sections=[Section(
            heading=ui(language, "fallback_heading"),
            body=[ui(language, "fallback_body")],
            bullets=[],
            cta_label=None,
        )],
        faq=[],
        disclaimer=ui(language, "fallback_disclaimer"),
        recommendations_implemented=[],
    )
