#!/usr/bin/env python3
"""Browser-driven audit of the recommendations tab and the generated website.

    python3 scripts/browser_audit.py --out outputs/browser_audit

Runs a fixed matrix of selections and languages. For each one it drives the
real UI with Playwright (tick/untick recommendations, pick a language, press
Generate), waits for the site, opens it through the actual "Browse generated
website" link, then audits all ten pages in the browser:

  * does the page express each selected recommendation, by feature?
  * does it respect usability basics (h1, above-fold CTA, nav, images, overflow)?
  * what WCAG contrast does the rendered text actually have?
  * is the copy in one language, the requested one?

Writes results.json plus a summary.md, and screenshots per iteration. Nothing
is mocked: this is the same servers a person would use.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
UI = "http://127.0.0.1:5173"
# steph 20/09, FIXED: this polled :8010, but serve_web.py defaults to :8000 and
# web/vite.config.ts proxies /api there. Against the documented dev setup the
# request never connected, so wait_ready() swallowed the connection error and
# retried until it raised a 420s TimeoutError - the audit looked like a slow
# site generation instead of a wrong port. Keep these in step with the proxy.
API = "http://127.0.0.1:8000"

# 10 iterations: a spread of counts (1-8) so "more" and "less" are both
# exercised, alternating direction, across the three languages.
MATRIX: list[dict] = [
    {"ids": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"], "lang": "fr", "direction": "down"},
    {"ids": ["R1", "R2", "R3"], "lang": "nl", "direction": "down"},
    {"ids": ["R4", "R5"], "lang": "en", "direction": "up"},
    {"ids": ["R1", "R3", "R4", "R6"], "lang": "fr", "direction": "up"},
    {"ids": ["R2", "R5", "R7", "R8"], "lang": "nl", "direction": "down"},
    {"ids": ["R1"], "lang": "en", "direction": "up"},
    {"ids": ["R1", "R2", "R3", "R4", "R5", "R6"], "lang": "fr", "direction": "down"},
    {"ids": ["R6", "R8"], "lang": "nl", "direction": "up"},
    {"ids": ["R2", "R4"], "lang": "en", "direction": "down"},
    {"ids": ["R1", "R2", "R4", "R5", "R6", "R7", "R8"], "lang": "fr", "direction": "up"},
]

# -----------------------------------------------------------------------------
# Feature -> automated expression check, multilingual
# -----------------------------------------------------------------------------
RATE_CUES = ("[taux]", "[rate]", "[rentevoet]", "taux", "rentevoet", "interest rate", "rente",
             "%")
BEGINNER_CUES = ("première fois", "premier pas", "débutant", "nouveau", "beginner",
                 "eerste keer", "eerste stap", "beginnende", "first time", "new to investing",
                 "se lancer", "commencer petit")
EXPAT_CUES = ("expat", "international", "étranger", "buitenland", "cross-border", "frontière",
              "grens", "abroad")
TRUST_CUES = ("clients", "klanten", "depuis", "sinds", "confiance", "vertrouwen", "des milliers",
              "duizenden", "millions", "miljoenen", "expert", "protégé", "beschermd", "protected")


def _feature_checks(features: list[str], pages: dict[str, dict], page_targets: list[str]) -> list[dict]:
    """One check per selected recommendation, keyed by the feature it names."""
    target_pages = {s: pages.get(s, {}) for s in page_targets} or pages
    joined = " ".join((p.get("text") or "").lower() for p in target_pages.values())
    checks: list[dict] = []

    if {"rate_shown", "rate_value_pct"} & set(features):
        checks.append({"feature": "rate_shown", "label": "a rate is visible",
                       "pass": any(c in joined for c in RATE_CUES),
                       "detail": f"rate cue found on {sum(1 for p in target_pages.values() if any(c in (p.get('text') or '').lower() for c in RATE_CUES))} page(s)"})
    if "cta_count" in features:
        counts = {s: p.get("cta_count", 0) for s, p in target_pages.items()}
        checks.append({"feature": "cta_count", "label": "multiple calls to action",
                       "pass": bool(counts) and min(counts.values()) >= 2,
                       "detail": f"CTA counts {counts}"})
    if "images_have_alt_text" in features:
        empty = sum(p.get("img_empty_alt", 0) for p in pages.values())
        total = sum(p.get("img_total", 0) for p in pages.values())
        checks.append({"feature": "images_have_alt_text", "label": "images carry alt text",
                       "pass": empty == 0, "detail": f"{total} images, {empty} with empty alt"})
    if "first_time_investor_targeting" in features:
        checks.append({"feature": "first_time_investor_targeting", "label": "first-time framing",
                       "pass": any(c in joined for c in BEGINNER_CUES),
                       "detail": f"beginner cue on target pages: {any(c in joined for c in BEGINNER_CUES)}"})
    if "expat_cross_border_targeting" in features:
        checks.append({"feature": "expat_cross_border_targeting", "label": "expat / cross-border angle",
                       "pass": any(c in joined for c in EXPAT_CUES),
                       "detail": f"expat cue on target pages: {any(c in joined for c in EXPAT_CUES)}"})
    if "value_prop_clarity" in features:
        hero_ok = all((p.get("h1_text") or "").strip() for p in target_pages.values())
        short = {s: len(p.get("h1_text") or "") for s, p in target_pages.items()}
        checks.append({"feature": "value_prop_clarity", "label": "clear hero value proposition",
                       "pass": hero_ok and max(short.values() or [0]) <= 90,
                       "detail": f"h1 lengths {short}"})
    if "persuasion_lever_count" in features:
        checks.append({"feature": "persuasion_lever_count", "label": "trust / persuasion cues",
                       "pass": any(c in joined for c in TRUST_CUES),
                       "detail": f"trust cue present: {any(c in joined for c in TRUST_CUES)}"})
    if {"aida_coverage_score", "numeric_claim_count"} & set(features):
        struct = {s: (p.get("section_count", 0), p.get("details_count", 0), p.get("cta_band", False))
                  for s, p in pages.items()}
        ok = all(sec >= 3 and det >= 3 and band for sec, det, band in struct.values())
        checks.append({"feature": "aida_coverage_score", "label": "full AIDA structure",
                       "pass": ok,
                       "detail": f"per page (sections, faq, cta-band): {struct}"})
    return checks


# -----------------------------------------------------------------------------
# In-page measurement
# -----------------------------------------------------------------------------
MEASURE_JS = r"""
() => {
  const parse = (c) => {
    const m = (c || '').match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x.trim()));
    return {r:p[0], g:p[1], b:p[2], a:p.length > 3 ? p[3] : 1};
  };
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
  const lum = (c) => 0.2126*lin(c.r) + 0.7152*lin(c.g) + 0.0722*lin(c.b);
  const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); const hi = Math.max(l1,l2), lo = Math.min(l1,l2); return (hi+0.05)/(lo+0.05); };
  const blend = (fg, bg) => ({
    r: fg.r*fg.a + bg.r*(1-fg.a), g: fg.g*fg.a + bg.g*(1-fg.a), b: fg.b*fg.a + bg.b*(1-fg.a), a: 1
  });
  const bgOf = (el) => {
    let node = el, acc = [];
    while (node) {
      const c = parse(getComputedStyle(node).backgroundColor);
      if (c && c.a > 0) { acc.push(c); if (c.a === 1) break; }
      node = node.parentElement;
    }
    let base = {r:255, g:255, b:255, a:1};
    for (let i = acc.length - 1; i >= 0; i--) base = blend(acc[i], base);
    return base;
  };
  const seen = new Set();
  const violations = [];
  const sel = 'h1,h2,h3,p,a,li,summary,strong,span,label,button,input,div';
  document.querySelectorAll(sel).forEach((el) => {
    if (el.children.length > 0 && !['A','BUTTON','SUMMARY','LABEL'].includes(el.tagName)) return;
    const text = (el.innerText || el.value || '').trim();
    if (!text || text.length < 2) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.15) return;
    const rect = el.getBoundingClientRect();
    if (rect.width < 3 || rect.height < 3) return;
    const fg = parse(cs.color);
    if (!fg) return;
    const bg = bgOf(el);
    const eff = fg.a < 1 ? blend(fg, bg) : fg;
    const size = parseFloat(cs.fontSize) || 16;
    const weight = parseInt(cs.fontWeight) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const required = large ? 3 : 4.5;
    const r = ratio(eff, bg);
    if (r < required) {
      const key = el.tagName + '|' + (el.className || '').toString().slice(0, 40) + '|' + text.slice(0, 25);
      if (!seen.has(key)) {
        seen.add(key);
        violations.push({ tag: el.tagName, cls: (el.className || '').toString().slice(0, 60),
                          text: text.slice(0, 45), ratio: Math.round(r*100)/100, required, large });
      }
    }
  });
  violations.sort((a, b) => a.ratio - b.ratio);

  const firstH1 = document.querySelector('h1');
  const cta = document.querySelector('.hero-cta .btn-primary');
  const imgs = [...document.images];
  const imgsSized = imgs.filter(i => i.getBoundingClientRect().width > 0);
  const nav = [...document.querySelectorAll('.mainnav a')];
  const links = [...document.querySelectorAll('a')];
  const inputs = [...document.querySelectorAll('input')];
  return {
    title: document.title,
    lang: document.documentElement.lang,
    h1_count: document.querySelectorAll('h1').length,
    h1_text: firstH1 ? firstH1.innerText.trim() : null,
    h1_in_viewport: firstH1 ? firstH1.getBoundingClientRect().top < window.innerHeight : false,
    cta_in_viewport: cta ? cta.getBoundingClientRect().top < window.innerHeight : false,
    cta_count: document.querySelectorAll('.hero-cta .btn, .block .btn, .cta-band .btn').length,
    cta_band: !!document.querySelector('.cta-band'),
    section_count: document.querySelectorAll('.block').length,
    details_count: document.querySelectorAll('details').length,
    nav_link_count: nav.length,
    nav_hrefs: nav.map(a => a.getAttribute('href')),
    img_total: imgs.length,
    img_rendered: imgsSized.length,
    img_broken: imgsSized.filter(i => !i.complete || i.naturalWidth === 0).length,
    img_empty_alt: imgs.filter(i => i.getAttribute('alt') === '' || i.getAttribute('alt') === null).length,
    overflow_px: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    links_without_text: links.filter(a => !(a.innerText || '').trim() && !a.getAttribute('aria-label')).length,
    inputs_without_label: inputs.filter(i => !i.getAttribute('aria-label') && !i.getAttribute('placeholder')).length,
    contrast_violations: violations.slice(0, 12),
    contrast_violation_count: violations.length,
    text: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 8000)
  };
}
"""

# Language marker heuristic, mirroring site_generator's check.
MARKERS = {
    "fr": (" le ", " la ", " les ", " des ", " une ", " pour ", " vous ", " votre ", " vos ",
           " avec ", " dans ", " sur ", " est ", " sont ", " plus ", " nous "),
    "nl": (" de ", " het ", " een ", " voor ", " u ", " uw ", " met ", " in ", " op ", " van ",
           " en ", " is ", " zijn ", " meer ", " bij ", " niet "),
    "en": (" the ", " a ", " an ", " for ", " you ", " your ", " with ", " in ", " on ", " of ",
           " and ", " is ", " are ", " more ", " at ", " not "),
}


def detect_language(text: str) -> str | None:
    low = f" {text.lower()} "
    scores = {k: sum(low.count(m) for m in v) for k, v in MARKERS.items()}
    best = max(scores, key=lambda k: scores[k])
    ordered = sorted(scores.values(), reverse=True)
    if scores[best] == 0 or (len(ordered) > 1 and ordered[0] - ordered[1] < 2):
        return None
    return best


def wait_ready(timeout: int = 420) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = requests.get(f"{API}/api/site/status", timeout=10).json()
        except requests.RequestException:
            time.sleep(2)
            continue
        if s.get("status") == "ready" and s.get("ready"):
            return s
        if s.get("status") == "error":
            raise RuntimeError(f"site generation failed: {s.get('error')}")
        time.sleep(2)
    raise TimeoutError("site generation timed out")


def run_iteration(pw, index: int, cfg: dict, out_dir: Path) -> dict:
    result: dict = {"iteration": index, "language": cfg["lang"], "selected": cfg["ids"],
                    "direction": cfg["direction"], "pages": [], "issues": []}
    browser = pw.chromium.launch()
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    ui = context.new_page()
    ui.goto(UI, wait_until="networkidle")
    ui.get_by_role("tab", name="Recommendations").click()
    ui.wait_for_selector(".rec-card", timeout=20000)

    cards = ui.query_selector_all(".rec-card")
    by_id = {}
    for c in cards:
        by_id[c.query_selector(".rec-id").inner_text().strip()] = c.query_selector(".rec-card-head input")

    want = set(cfg["ids"])
    # "down": start from all selected, remove the rest. "up": start from none, add.
    start_checked = True if cfg["direction"] == "down" else False
    for rid, box in by_id.items():
        if box.is_checked() != start_checked:
            box.click()
    for rid, box in by_id.items():
        target = rid in want
        if box.is_checked() != target:
            box.click()
    checked = sorted(rid for rid, box in by_id.items() if box.is_checked())
    result["checked_after_interaction"] = checked
    if checked != sorted(want):
        result["issues"].append(f"UI selection mismatch: wanted {sorted(want)}, got {checked}")

    ui.select_option(".rec-lang select", cfg["lang"])
    ui.get_by_role("button", name="Generate ING website").click()
    try:
        ui.wait_for_selector(".rec-progress", timeout=20000)
    except PWTimeout:
        result["issues"].append("progress indicator never appeared after Generate")

    s = wait_ready()
    manifest = s["manifest"]
    result["manifest_recs"] = [r["id"] for r in manifest.get("recommendations", [])]
    result["fallbacks"] = [p["slug"] for p in manifest["pages"] if p["used_fallback"]]
    if result["manifest_recs"] != sorted(want):
        result["issues"].append(f"manifest selections {result['manifest_recs']} != wanted {sorted(want)}")

    # Exercise the real Browse link and audit the site in the opened tab.
    try:
        with ui.expect_popup(timeout=15000) as pop:
            ui.get_by_role("link", name=re.compile("Browse generated website")).click()
        site = pop.value
        opened_via_button = True
    except PWTimeout:
        site = context.new_page()
        site.goto(f"{UI}/site/index.html")
        opened_via_button = False
        result["issues"].append("Browse generated website link did not open a new tab")
    result["opened_via_button"] = opened_via_button

    console_errors: list[str] = []
    failed_requests: list[str] = []
    site.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    site.on("requestfailed", lambda r: failed_requests.append(r.url))
    site.on("response", lambda r: failed_requests.append(f"{r.status} {r.url}") if r.status >= 400 else None)

    pages_data: dict[str, dict] = {}
    for p in manifest["pages"]:
        slug = p["slug"]
        site.goto(f"{UI}/site/{p['file']}", wait_until="networkidle")
        m = site.evaluate(MEASURE_JS)
        pages_data[slug] = m
        result["pages"].append({
            "slug": slug, "title": m["title"], "lang": m["lang"], "h1_count": m["h1_count"],
            "h1_in_viewport": m["h1_in_viewport"], "cta_in_viewport": m["cta_in_viewport"],
            "cta_count": m["cta_count"], "nav_link_count": m["nav_link_count"],
            "img_broken": m["img_broken"], "img_empty_alt": m["img_empty_alt"],
            "overflow_px": m["overflow_px"], "contrast_violation_count": m["contrast_violation_count"],
            "detected_language": detect_language(m["text"]),
        })
    result["console_errors"] = console_errors[:10]
    result["failed_requests"] = failed_requests[:10]

    # Mobile pass on the home page: overflow and above-fold CTA at 375px.
    site.set_viewport_size({"width": 375, "height": 812})
    site.goto(f"{UI}/site/index.html", wait_until="networkidle")
    mob = site.evaluate(MEASURE_JS)
    result["mobile"] = {
        "overflow_px": mob["overflow_px"], "h1_count": mob["h1_count"],
        "cta_in_viewport": mob["cta_in_viewport"], "nav_link_count": mob["nav_link_count"],
        "contrast_violation_count": mob["contrast_violation_count"],
    }
    if mob["overflow_px"] > 1:
        result["issues"].append(f"mobile horizontal overflow {mob['overflow_px']}px")
    if mob["h1_count"] != 1:
        result["issues"].append("mobile home page does not have exactly one h1")
    if not mob["cta_in_viewport"]:
        result["issues"].append("mobile primary CTA not visible without scrolling")
    site.screenshot(path=str(out_dir / f"iteration_{index:02d}_mobile.png"))

    # Screenshot the home page of this iteration (desktop).
    site.set_viewport_size({"width": 1440, "height": 900})
    site.goto(f"{UI}/site/index.html", wait_until="networkidle")
    shot = out_dir / f"iteration_{index:02d}_index.png"
    site.screenshot(path=str(shot))
    result["screenshot"] = str(shot.relative_to(REPO_ROOT))

    # Recommendation expression, per selected recommendation.
    recs = json.loads((REPO_ROOT / "outputs" / "web_recommendations.json").read_text())
    rec_by_id = {r["id"]: r for r in recs["recommendations"]}
    # A fallback page is explicitly *not* a generation; scoring recommendation
    # expression on it would blame the model for a page it never wrote.
    scored_pages = {k: v for k, v in pages_data.items() if k not in result["fallbacks"]}
    result["recommendation_checks"] = []
    for rid in sorted(want):
        r = rec_by_id.get(rid)
        if not r:
            continue
        checks = _feature_checks(r.get("features", []), scored_pages, r.get("page_targets", []))
        result["recommendation_checks"].append({"id": rid, "title": r["title"],
                                                "features": r.get("features", []), "checks": checks})

    browser.close()
    return result


def summarize(results: list[dict], out_dir: Path) -> dict:
    totals = {"iterations": len(results), "pages": 0, "contrast_violations": 0,
              "broken_images": 0, "empty_alt": 0, "overflow_pages": 0,
              "h1_ok": 0, "cta_above_fold_ok": 0, "nav_ok": 0,
              "wrong_language": 0, "recommendation_checks": 0, "recommendation_passes": 0,
              "mobile_ok": 0}
    for r in results:
        m = r.get("mobile", {})
        if (m.get("overflow_px", 1) <= 1 and m.get("h1_count") == 1 and m.get("cta_in_viewport")):
            totals["mobile_ok"] += 1
        for p in r["pages"]:
            totals["pages"] += 1
            totals["contrast_violations"] += p["contrast_violation_count"]
            totals["broken_images"] += p["img_broken"]
            totals["empty_alt"] += p["img_empty_alt"]
            totals["overflow_pages"] += 1 if p["overflow_px"] > 1 else 0
            totals["h1_ok"] += 1 if p["h1_count"] == 1 else 0
            totals["cta_above_fold_ok"] += 1 if p["cta_in_viewport"] else 0
            totals["nav_ok"] += 1 if p["nav_link_count"] == 10 else 0
            totals["wrong_language"] += 1 if (p["detected_language"] and p["detected_language"] != r["language"]) else 0
        for rc in r["recommendation_checks"]:
            for c in rc["checks"]:
                totals["recommendation_checks"] += 1
                totals["recommendation_passes"] += 1 if c["pass"] else 0
    return totals


def write_summary(results: list[dict], totals: dict, out_dir: Path) -> None:
    lines = ["# Browser audit — recommendations and generated website", "",
             f"Generated {time.strftime('%Y-%m-%d %H:%M')} · {totals['iterations']} iterations · "
             f"{totals['pages']} page loads.", ""]
    pct = (100 * totals["recommendation_passes"] / totals["recommendation_checks"]
           if totals["recommendation_checks"] else 0)
    lines += ["## Headline",
              f"- Recommendation expression: **{totals['recommendation_passes']}/"
              f"{totals['recommendation_checks']} checks pass ({pct:.0f}%)**",
              f"- Pages with exactly one h1: {totals['h1_ok']}/{totals['pages']}",
              f"- Pages with the primary CTA above the fold: {totals['cta_above_fold_ok']}/{totals['pages']}",
              f"- Pages with all 10 nav links: {totals['nav_ok']}/{totals['pages']}",
              f"- Wrong-language pages: {totals['wrong_language']}/{totals['pages']}",
              f"- Contrast violations (rendered text): {totals['contrast_violations']}",
              f"- Broken images: {totals['broken_images']} · images without alt: {totals['empty_alt']}",
              f"- Pages with horizontal overflow: {totals['overflow_pages']}/{totals['pages']}",
              f"- Mobile home page clean (no overflow, h1, above-fold CTA): "
              f"{totals['mobile_ok']}/{totals['iterations']}",
              ""]
    lines += ["## Per iteration", ""]
    for r in results:
        langs = {p["detected_language"] for p in r["pages"]}
        fails = [f"{rc['id']}:{c['feature']}" for rc in r["recommendation_checks"]
                 for c in rc["checks"] if not c["pass"]]
        lines.append(f"### Iteration {r['iteration']:02d} — {r['language']}, "
                     f"{len(r['selected'])} selected, {r['direction']}")
        lines.append(f"- selected: {', '.join(r['selected'])}")
        lines.append(f"- manifest: {', '.join(r['manifest_recs'])} · fallbacks: {r['fallbacks'] or 'none'}")
        lines.append(f"- page languages detected: {sorted(l for l in langs if l)}")
        lines.append(f"- recommendation checks failing: {fails or 'none'}")
        lines.append(f"- console errors: {r['console_errors'] or 'none'}")
        lines.append(f"- failed requests: {r['failed_requests'] or 'none'}")
        if r["issues"]:
            lines.append(f"- **issues**: {'; '.join(r['issues'])}")
        worst = sorted({p["contrast_violation_count"] for p in r["pages"]}, reverse=True)[:1]
        lines.append(f"- max contrast violations on a page: {worst[0] if worst else 0}")
        lines.append(f"- screenshot: `{r['screenshot']}`")
        lines.append("")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "outputs" / "browser_audit")
    parser.add_argument("--only", type=int, default=None, help="run a single iteration index")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    matrix = MATRIX if args.only is None else [MATRIX[args.only]]
    results: list[dict] = []
    with sync_playwright() as pw:
        for i, cfg in enumerate(matrix, start=1):
            idx = i if args.only is None else args.only
            print(f"[{idx}] lang={cfg['lang']} selected={len(cfg['ids'])} dir={cfg['direction']} ...",
                  flush=True)
            t0 = time.time()
            res = run_iteration(pw, idx, cfg, args.out)
            res["seconds"] = round(time.time() - t0, 1)
            results.append(res)
            (args.out / f"iteration_{idx:02d}.json").write_text(
                json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"    done in {res['seconds']}s · fallbacks={res['fallbacks']} "
                  f"· contrast={sum(p['contrast_violation_count'] for p in res['pages'])}",
                  flush=True)

    totals = summarize(results, args.out)
    (args.out / "results.json").write_text(
        json.dumps({"totals": totals, "iterations": results}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    write_summary(results, totals, args.out)
    print(json.dumps(totals, indent=2))
    print(f"\nwrote {args.out/'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
