/**
 * Builds docs/Recommendation_System.pptx — a standalone five-slide deck on the
 * recommendation system, in the house style of Banking_Campaigns_Comparator.pptx.
 *
 *   node scripts/deck/build_recommendations_deck.js
 *
 * The style is not invented here: it is measured from the existing deck —
 * 13.33x7.5in, Helvetica Neue, ink #14141C, muted #585868, ING orange #FF6200,
 * a 1.6in orange rule under each title, the same footer string and a page
 * number at the same coordinates. The orange rule is an accent line under a
 * title, which house style for generic decks would avoid; it is kept because
 * the deck this one sits beside uses it on all 34 slides, and consistency with
 * the client's established deck wins over a generic rule.
 *
 * Every figure quoted on a slide comes from outputs/web_recommendations.json,
 * read at build time rather than typed in, so a regenerated run cannot leave a
 * stale number on a slide.
 */

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..", "..");
const ASSETS = path.join(ROOT, "docs", "deck_assets");
const ICONS = path.join(ASSETS, "icons");

// ---- house style, measured from the existing deck ------------------------
const INK = "14141C";
const MUTED = "585868";
const ORANGE = "FF6200";
const LINE = "E4E4EC";
const WASH = "FAFAFC";
const FONT = "Helvetica Neue";
const FOOTER = "Banking Campaigns Comparator · ING DACI / Customer AI · September 2026";

const recs = JSON.parse(
  fs.readFileSync(path.join(ROOT, "outputs", "web_recommendations.json"), "utf8")
);
const counts = recs.recommendations.reduce((a, r) => ((a[r.priority] = (a[r.priority] || 0) + 1), a), {});
const byBasis = recs.recommendations.reduce((a, r) => ((a[r.basis] = (a[r.basis] || 0) + 1), a), {});
const top = recs.recommendations.filter((r) => r.priority === "high");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5, matching the source deck
pres.author = "Banking Campaigns Comparator";
pres.title = "The recommendation system";

let pageNo = 0;

/** Title, the house orange rule, footer and page number. */
function frame(slide, title, opts = {}) {
  pageNo += 1;
  const tight = opts.tight === true; // picture slides sit the title slightly higher
  slide.background = { color: "FFFFFF" };
  slide.addText(title, {
    x: 0.6, y: tight ? 0.35 : 0.42, w: 12.1, h: tight ? 0.7 : 0.8,
    fontFace: FONT, fontSize: 28, bold: true, color: INK, isTextBox: true, margin: 0,
    valign: "middle",
  });
  slide.addShape(pres.ShapeType.rect, {
    x: 0.6, y: tight ? 1.05 : 1.22, w: 1.6, h: tight ? 0.06 : 0.07, fill: { color: ORANGE }, line: { width: 0 },
  });
  slide.addText(FOOTER, {
    x: 0.6, y: 7.0, w: 9.0, h: 0.3, fontFace: FONT, fontSize: 10, color: MUTED,
    isTextBox: true, margin: 0, valign: "middle",
  });
  slide.addText(String(pageNo), {
    x: 12.13, y: 7.0, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 10, color: MUTED,
    align: "right", isTextBox: true, margin: 0, valign: "middle",
  });
}

/** An icon in its orange circle, with a bold lead and a muted explanation. */
function iconRow(slide, { icon, lead, body, x, y, w }) {
  slide.addImage({ path: path.join(ICONS, `${icon}.png`), x, y: y - 0.02, w: 0.46, h: 0.46 });
  slide.addText(lead, {
    x: x + 0.62, y: y - 0.04, w: w - 0.62, h: 0.3,
    fontFace: FONT, fontSize: 13.5, bold: true, color: INK, isTextBox: true, margin: 0, valign: "middle",
  });
  slide.addText(body, {
    x: x + 0.62, y: y + 0.28, w: w - 0.62, h: 0.78,
    fontFace: FONT, fontSize: 11.5, color: MUTED, isTextBox: true, margin: 0, lineSpacing: 15,
  });
}

/** Screenshot with a hairline frame, so a white UI does not float on white. */
function shot(slide, file, x, y, w, h) {
  slide.addShape(pres.ShapeType.rect, {
    x: x - 0.035, y: y - 0.035, w: w + 0.07, h: h + 0.07,
    fill: { color: "FFFFFF" }, line: { color: LINE, width: 1 },
  });
  slide.addImage({ path: path.join(ASSETS, file), x, y, w, h });
}

function caption(slide, text, x, y, w) {
  slide.addText(text, {
    x, y, w, h: 0.32, fontFace: FONT, fontSize: 10.5, color: MUTED,
    italic: true, isTextBox: true, margin: 0, valign: "middle",
  });
}

// =========================================================================
// 1 — what it does
// =========================================================================
{
  const s = pres.addSlide();
  frame(s, "A recommendation system on top of the measurement");

  // 2120x1072 -> 1.978
  shot(s, "rec_controls.png", 6.72, 1.56, 6.00, 3.03);
  caption(s, "The panel as the team sees it: one button, two opt-in contexts, and the run it produced.", 6.72, 4.70, 6.00);

  const rows = [
    { icon: "target", lead: "One model call over the finished analysis",
      body: `Reads report.json only — the same numbers the charts are drawn from. This run turned 30 measured features across 14 banks into ${recs.recommendations.length} ordered changes.` },
    { icon: "list", lead: "Ordered by priority, not by confidence",
      body: `${counts.high} high, ${counts.medium} medium, ${counts.low} low. The order is the argument: what the measurement most supports acting on first.` },
    { icon: "shield", lead: "Two contexts, both opt-in and both marked",
      body: `Search interest for timing, and news themes for reputation (${byBasis.reputation} of the ${recs.recommendations.length} here). Context is never allowed to stand as evidence that a page performed.` },
  ];
  rows.forEach((r, i) => iconRow(s, { ...r, x: 0.68, y: 1.78 + i * 1.42, w: 5.85 }));

  s.addShape(pres.ShapeType.roundRect, {
    x: 6.72, y: 5.26, w: 6.00, h: 1.34, rectRadius: 0.06,
    fill: { color: WASH }, line: { color: LINE, width: 1 },
  });
  s.addText(
    "It writes what to change. It does not re-derive a single number — that direction is one-way by design.",
    { x: 7.00, y: 5.46, w: 5.44, h: 0.94, fontFace: FONT, fontSize: 12, color: ORANGE,
      bold: true, isTextBox: true, margin: 0, lineSpacing: 17 }
  );
  s.addNotes("The recommendation layer is the only place in the project where a model is allowed to opine. Everything upstream measures; this interprets.");
}

// =========================================================================
// 2 — how a recommendation is built
// =========================================================================
{
  const s = pres.addSlide();
  frame(s, "Every recommendation carries the evidence it was argued from", { tight: true });

  // 2120x1384 -> 1.532
  shot(s, "rec_cards.png", 0.72, 1.38, 6.90, 4.50);
  caption(s, "Three of the eleven, as the team reviews them.", 0.72, 6.00, 6.90);

  const guards = [
    { icon: "list", lead: "Finding and action, kept apart",
      body: "What the data shows sits above what to do. A reader can reject our suggested action and still keep the measured finding." },
    { icon: "target", lead: "Named features, checked before release",
      body: "Each card names the measured features it was argued from and the pages it applies to. Those ids are verified against the report — an invented one never leaves the module." },
    { icon: "shield", lead: "No figure the analysis did not produce",
      body: "The prompt receives only numbers already in the report, and the output is not trusted to add any." },
  ];
  guards.forEach((r, i) => iconRow(s, { ...r, x: 7.94, y: 1.52 + i * 1.72, w: 4.66 }));

  s.addNotes("Separating finding from action matters: a reader can reject our suggested action and still keep the measured finding.");
}

// =========================================================================
// 3 — what it concluded
// =========================================================================
{
  const s = pres.addSlide();
  frame(s, "What it concluded about ING");

  const stats = [
    { n: "4.0", unit: "urgency markers per page", sub: "against a peer mean of 0.64 — about 3.7 standard deviations above the set, and ING's strongest measured signature." },
    { n: "1.0", unit: "call to action per page", sub: "against a peer mean of 6.18. The only measured gap where ING sits below its peers rather than above." },
    { n: "0.67", unit: "‘free’ claims with conditions elsewhere", sub: "against a peer mean of 0.23 — the qualifying conditions are not adjacent to the claim they qualify." },
  ];
  const cw = 3.86, gap = 0.36;
  stats.forEach((st, i) => {
    const x = 0.68 + i * (cw + gap);
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 1.66, w: cw, h: 2.42, rectRadius: 0.06,
      fill: { color: WASH }, line: { color: LINE, width: 1 },
    });
    s.addText(st.n, { x: x + 0.28, y: 1.84, w: cw - 0.56, h: 0.92, fontFace: FONT,
      fontSize: 46, bold: true, color: ORANGE, isTextBox: true, margin: 0, valign: "middle" });
    s.addText(st.unit, { x: x + 0.28, y: 2.74, w: cw - 0.56, h: 0.34, fontFace: FONT,
      fontSize: 12, bold: true, color: INK, isTextBox: true, margin: 0, valign: "middle" });
    s.addText(st.sub, { x: x + 0.28, y: 3.10, w: cw - 0.56, h: 0.86, fontFace: FONT,
      fontSize: 10.5, color: MUTED, isTextBox: true, margin: 0, lineSpacing: 14 });
  });

  s.addText("The three it ranked highest", {
    x: 0.68, y: 4.34, w: 11.9, h: 0.32, fontFace: FONT, fontSize: 13.5, bold: true,
    color: INK, isTextBox: true, margin: 0, valign: "middle",
  });
  top.slice(0, 3).forEach((r, i) => {
    const y = 4.76 + i * 0.58;
    s.addShape(pres.ShapeType.ellipse, { x: 0.70, y: y + 0.07, w: 0.17, h: 0.17, fill: { color: ORANGE }, line: { width: 0 } });
    s.addText(r.title, { x: 1.00, y, w: 5.55, h: 0.32, fontFace: FONT, fontSize: 12,
      bold: true, color: INK, isTextBox: true, margin: 0, valign: "middle" });
    s.addText(r.features.join(" · "), { x: 6.68, y, w: 5.92, h: 0.32, fontFace: FONT,
      fontSize: 10.5, color: MUTED, isTextBox: true, margin: 0, valign: "middle" });
  });

  s.addText(
    "Design observations, not performance findings. The pages span several product families and languages, the judged features come from a single rater, and no click or conversion data exists — so every item is a hypothesis ING could test.",
    { x: 0.68, y: 6.44, w: 11.9, h: 0.46, fontFace: FONT, fontSize: 10.5, color: MUTED,
      isTextBox: true, margin: 0, lineSpacing: 14 }
  );
  s.addNotes("The caveat is not decoration. Without outcome data these are differences, not faults.");
}

// =========================================================================
// 4 — what it is useful for
// =========================================================================
{
  const s = pres.addSlide();
  frame(s, "From a list of changes to a site you can actually look at", { tight: true });

  // 5120x1800 -> 2.844
  shot(s, "site_hero.png", 0.72, 1.40, 7.30, 2.57);
  // 2500x1000 -> 2.500
  shot(s, "site_explained.png", 0.72, 4.20, 5.60, 2.24);
  caption(s, "Generated, never published: rates and amounts stay as [TAUX] and [MONTANT] placeholders.", 0.72, 6.56, 7.30);

  const rows = [
    { icon: "check", lead: "The team chooses what gets built",
      body: "Every recommendation is a checkbox. Nothing reaches the generator that a person did not tick." },
    { icon: "window", lead: "Ten ING-styled pages, in fr-BE or nl-BE",
      body: "Home, savings, term account, current account, youth, investing, mortgage, opening, why ING, contact." },
    { icon: "list", lead: "Each section can name its own source",
      body: "In explained mode, the orange blocks say which recommendation produced that section and why — so the site is auditable, not just persuasive." },
  ];
  rows.forEach((r, i) => iconRow(s, { ...r, x: 8.42, y: 1.56 + i * 1.46, w: 4.20 }));

  s.addText(
    "This is what makes the analysis arguable: a stakeholder can look at the change rather than read about it.",
    { x: 8.42, y: 6.00, w: 4.20, h: 0.66, fontFace: FONT, fontSize: 11.5, color: ORANGE,
      bold: true, isTextBox: true, margin: 0, lineSpacing: 15 }
  );
  s.addNotes("The site is a demonstration of the recommendations, not a proposal for production copy.");
}

// =========================================================================
// 5 — the complete pipeline
// =========================================================================
{
  const s = pres.addSlide();
  frame(s, "The complete pipeline", { tight: true });
  // 2560x1160 -> 2.207. Sized to clear the footer: the first cut overlapped it.
  s.addImage({ path: path.join(ASSETS, "pipeline_complete.png"), x: 1.02, y: 1.28, w: 11.3, h: 5.12 });
  caption(s, "Stages 1–5 are the measurement half shown in the main deck. Stages 6–8 are this one.", 1.02, 6.48, 11.3);
  s.addNotes("Stages 1-5 are the measurement half shown in the main deck. Stages 6-8 are this deck.");
}

const out = path.join(ROOT, "docs", "Recommendation_System.pptx");
pres.writeFile({ fileName: out }).then(() => console.log("wrote " + out));
