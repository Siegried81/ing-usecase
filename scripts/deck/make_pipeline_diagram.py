#!/usr/bin/env python3
"""Render the complete-pipeline diagram for the recommendations deck.

    python3 scripts/deck/make_pipeline_diagram.py

Matches the house diagram style already in Banking_Campaigns_Comparator.pptx:
white ground, rounded cards with a thick coloured top rule, bold stage name over
grey detail, coloured arrows, grey guardrail band at the foot. Palette sampled
from that deck rather than guessed - #FF6200 / #000066 / #00757F / #1F7A3F on
#14141C ink.

Arial, not Helvetica Neue: only the 400 weight of Helvetica Neue is registered
with matplotlib here, so `fontweight="bold"` silently rendered regular and every
heading came out light. Arial carries a real 700 and is metrically close enough
that the slide still reads as one deck.

The existing deck's diagram stops at "Surfaces". This one carries the same flow
through the two stages that deck never showed - recommendations written from the
analysis, and a site generated from the ones a human selected. The measurement
half is drawn compactly and the new half large, so the shape of the picture says
which part is new.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

W, H = 25.60, 11.60                       # inches at 100 dpi -> 2560x1160
#   no title inside the image: the slide provides it, and repeating it here cost
#   a third of the canvas and shrank every box.
INK, MUTED, LINE = "#14141C", "#585868", "#D8D8E0"
ORANGE, NAVY, TEAL, GREEN = "#FF6200", "#000066", "#00757F", "#1F7A3F"
BAND = "#F3F3F6"
F = "Arial"

M = 0.85                                  # page margin
USABLE = W - 2 * M

UPSTREAM = [
    ("1", "Sources",  "bank campaign pages\nGoogle Trends · news", ORANGE),
    ("2", "Capture",  "robots gate · render\nLLM extract · quality", ORANGE),
    ("3", "Dataset",  "campaigns.csv\n+ human rubric scores", NAVY),
    ("4", "Analysis", "profiles · positioning\nsimilarity · AI score", TEAL),
    ("5", "Surfaces", "report.json\nbusiness web UI", GREEN),
]

DOWNSTREAM = [
    ("6", "Recommendations", "list", [
        "one model call over report.json",
        "11 ordered changes, high to low",
        "each names the features it argues from",
        "no figure the analysis did not produce",
    ], "outputs/web_recommendations.json"),
    ("7", "Human selection", "check", [
        "every recommendation is a checkbox",
        "the team unticks what it will not build",
        "reputation items marked as context",
        "nothing proceeds unchosen",
    ], "11 of 11 selected"),
    ("8", "Generated site", "window", [
        "ten ING-styled pages, fr-BE or nl-BE",
        "implements exactly the selected set",
        "every section can name its source",
        "rates and amounts stay placeholders",
    ], "outputs/site/"),
]


def card(ax, x, y, w, h, colour, rule=0.09):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                linewidth=1.1, edgecolor=LINE, facecolor="white", zorder=2))
    ax.add_patch(FancyBboxPatch((x + 0.06, y + h - rule), w - 0.12, rule,
                                boxstyle="round,pad=0,rounding_size=0.03",
                                linewidth=0, facecolor=colour, zorder=3))


def arrow(ax, x1, y1, x2, y2, colour, lw=2.6, size=18):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=size,
                                 linewidth=lw, color=colour, zorder=5, shrinkA=0, shrinkB=0))


def draw_glyph(ax, kind, cx, cy, c=ORANGE):
    """Icons as geometry, not characters - Arial has no glyph for the symbols
    these cards want, and a missing glyph renders as a tofu box."""
    if kind == "list":                       # three ranked rules, longest first
        for i, w in enumerate((0.34, 0.26, 0.18)):
            y = cy + 0.13 - i * 0.13
            ax.plot([cx - 0.17, cx - 0.17 + w], [y, y], color=c, linewidth=2.2,
                    solid_capstyle="round", zorder=5)
    elif kind == "check":
        ax.plot([cx - 0.16, cx - 0.045, cx + 0.18], [cy + 0.01, cy - 0.13, cy + 0.15],
                color=c, linewidth=2.6, solid_capstyle="round",
                solid_joinstyle="round", zorder=5)
    elif kind == "window":                   # a browser frame
        ax.add_patch(FancyBboxPatch((cx - 0.20, cy - 0.16), 0.40, 0.32,
                                    boxstyle="round,pad=0,rounding_size=0.04",
                                    linewidth=2.0, edgecolor=c, facecolor="none", zorder=5))
        ax.plot([cx - 0.20, cx + 0.20], [cy + 0.06] * 2, color=c, linewidth=1.8, zorder=5)


def eyebrow(ax, x, y, text, colour):
    ax.text(x, y, " ".join(text), fontsize=10, fontweight="bold", color=colour,
            family=F, va="center")


def main() -> None:
    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    # --- measurement: compact chain ----------------------------------------
    eyebrow(ax, M, H - 0.42, "MEASUREMENT", MUTED)
    gap, bh = 0.62, 2.05
    bw = (USABLE - 4 * gap) / 5
    top = H - 0.86
    for i, (num, title, body, colour) in enumerate(UPSTREAM):
        x = M + i * (bw + gap)
        card(ax, x, top - bh, bw, bh, colour)
        ax.text(x + bw / 2, top - 0.54, f"{num}   {title}", ha="center", va="center",
                fontsize=15.5, fontweight="bold", color=INK, family=F, zorder=4)
        ax.text(x + bw / 2, top - 0.96, body, ha="center", va="top", fontsize=10.5,
                color=MUTED, family=F, linespacing=1.55, zorder=4)
        if i < 4:
            arrow(ax, x + bw + 0.08, top - bh / 2, x + bw + gap - 0.08, top - bh / 2,
                  colour, lw=2.4, size=15)

    # --- connector ----------------------------------------------------------
    cx = M + USABLE / 2
    arrow(ax, cx, top - bh - 0.16, cx, top - bh - 0.90, ORANGE, lw=3.2, size=21)
    ax.text(cx + 0.24, top - bh - 0.53, "report.json", fontsize=10.5, color=MUTED,
            family=F, va="center", style="italic")

    # --- the half this deck is about ---------------------------------------
    eyebrow(ax, M, top - bh - 1.36, "FROM ANALYSIS TO A THING YOU CAN LOOK AT", ORANGE)
    dgap, dh = 0.80, 4.55
    dw = (USABLE - 2 * dgap) / 3
    dtop = top - bh - 1.78
    for i, (num, title, glyph, bullets, artefact) in enumerate(DOWNSTREAM):
        x = M + i * (dw + dgap)
        card(ax, x, dtop - dh, dw, dh, ORANGE, rule=0.11)

        ax.add_patch(Circle((x + 0.78, dtop - 0.82), 0.34, facecolor="#FFF1E8",
                            edgecolor=ORANGE, linewidth=1.4, zorder=4))
        draw_glyph(ax, glyph, x + 0.78, dtop - 0.82)
        ax.text(x + 1.36, dtop - 0.68, num, fontsize=11, fontweight="bold",
                color=ORANGE, family=F, va="center", zorder=4)
        ax.text(x + 1.36, dtop - 1.02, title, fontsize=17, fontweight="bold",
                color=INK, family=F, va="center", zorder=4)

        for j, line in enumerate(bullets):
            yy = dtop - 1.80 - j * 0.52
            ax.add_patch(Circle((x + 0.62, yy + 0.015), 0.045, facecolor=ORANGE,
                                edgecolor="none", zorder=4))
            ax.text(x + 0.86, yy, line, fontsize=11, color=MUTED, family=F,
                    va="center", zorder=4)

        ax.plot([x + 0.55, x + dw - 0.55], [dtop - dh + 0.72] * 2, color=LINE,
                linewidth=1, zorder=4)
        ax.text(x + 0.55, dtop - dh + 0.42, artefact, fontsize=10, color=ORANGE,
                family=F, va="center", zorder=4, style="italic")

        if i < 2:
            arrow(ax, x + dw + 0.10, dtop - dh / 2, x + dw + dgap - 0.10, dtop - dh / 2,
                  ORANGE, lw=3.0, size=19)

    # --- guardrails ---------------------------------------------------------
    band_h, band_y = 1.78, 0.42
    ax.add_patch(FancyBboxPatch((M, band_y), USABLE, band_h,
                                boxstyle="round,pad=0,rounding_size=0.12",
                                linewidth=0, facecolor=BAND, zorder=1))
    ax.text(W / 2, band_y + band_h - 0.46, "What holds across the last two stages",
            ha="center", va="center", fontsize=14, fontweight="bold", color=INK,
            family=F, zorder=2)
    for i, line in enumerate([
        "the model sees only numbers already in the analysis and may not introduce one of its own  ·  "
        "every recommendation names the features it was argued from, checked before it leaves the module",
        "nothing is built that a human did not tick  ·  news-theme items are context, never evidence  ·  "
        "no performance data exists, so nothing here claims a cause",
    ]):
        ax.text(W / 2, band_y + band_h - 0.98 - i * 0.44, line, ha="center", va="center",
                fontsize=10.5, color=MUTED, family=F, zorder=2)

    out = Path("docs/deck_assets/pipeline_complete.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
