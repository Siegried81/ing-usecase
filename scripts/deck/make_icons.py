#!/usr/bin/env python3
"""Small orange-on-cream icons for the recommendations deck.

Drawn as geometry rather than set as characters: Arial and Helvetica Neue have
no glyph for the symbols these slides want, and a missing glyph renders as a
tofu box. Same shapes as the pipeline diagram, so the deck reads as one motif.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

ORANGE, WASH = "#FF6200", "#FFF1E8"
OUT = Path("docs/deck_assets/icons")


def canvas():
    fig = plt.figure(figsize=(2.56, 2.56), dpi=100)
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Circle((0.5, 0.5), 0.46, facecolor=WASH, edgecolor=ORANGE, linewidth=5))
    return fig, ax


def draw(name, fn):
    fig, ax = canvas(); fn(ax)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=100, transparent=True)
    plt.close(fig)
    print(f"  {name}.png")


def ranked_list(ax):
    for i, w in enumerate((0.40, 0.31, 0.22)):
        y = 0.63 - i * 0.13
        ax.plot([0.30, 0.30 + w], [y, y], color=ORANGE, lw=7, solid_capstyle="round")


def check(ax):
    ax.plot([0.30, 0.45, 0.72], [0.52, 0.36, 0.66], color=ORANGE, lw=8,
            solid_capstyle="round", solid_joinstyle="round")


def window(ax):
    ax.add_patch(FancyBboxPatch((0.28, 0.32), 0.44, 0.36,
                                boxstyle="round,pad=0,rounding_size=0.05",
                                linewidth=6, edgecolor=ORANGE, facecolor="none"))
    ax.plot([0.28, 0.72], [0.585, 0.585], color=ORANGE, lw=5)


def target(ax):
    ax.add_patch(Circle((0.5, 0.5), 0.22, facecolor="none", edgecolor=ORANGE, linewidth=6))
    ax.add_patch(Circle((0.5, 0.5), 0.07, facecolor=ORANGE, edgecolor="none"))


def shield(ax):
    ax.plot([0.5, 0.29, 0.29, 0.5, 0.71, 0.71, 0.5],
            [0.74, 0.64, 0.42, 0.26, 0.42, 0.64, 0.74],
            color=ORANGE, lw=6, solid_capstyle="round", solid_joinstyle="round")


def main():
    for name, fn in (("list", ranked_list), ("check", check), ("window", window),
                     ("target", target), ("shield", shield)):
        draw(name, fn)


if __name__ == "__main__":
    main()
