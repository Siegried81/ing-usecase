"""Charts for the comparison.

Palette and form choices follow the project's data-visualisation rules:

  * Categorical identity uses two slots only - traditional #2a78d6, challenger
    #eb6834 - validated all-pairs on the light surface (CVD dE 24.7, normal 33.6,
    both >= 3:1 contrast). Two series is well inside the safe band.
  * Colour follows the entity, never its rank: a bank keeps its category hue in
    every chart. ING is emphasised with a ring and a bold label, never a third hue.
  * Sequential magnitude (the distance matrix) uses ONE hue, light -> dark.
  * Never a dual axis. Features on different scales are standardised or faceted.
  * A legend is always present for two series, and every mark is direct-labelled.
  * Text wears ink tokens, never the series colour.

These are static PNGs for a light-background deck, so light mode is a deliberate
single-mode commitment rather than an oversight.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from comparator.analysis import Positioning

mpl.use("Agg")

# --- design tokens -----------------------------------------------------------
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#8a8984"
GRID = "#e8e7e3"
NEUTRAL = "#c9c8c3"

CATEGORY_COLOUR = {"traditional": "#2a78d6", "challenger": "#eb6834"}
FOCUS_RING = "#0b0b0b"

# Documented blue ramp, light -> dark, for sequential magnitude only.
BLUE_RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQUENTIAL = LinearSegmentedColormap.from_list("comparator_blue", BLUE_RAMP)


def _style(ax: plt.Axes) -> plt.Axes:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9, length=0)
    ax.title.set_color(INK_PRIMARY)
    return ax


def _figure(width: float, height: float) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(width, height), facecolor=SURFACE)
    _style(ax)
    return fig, ax


def _title(ax: plt.Axes, title: str, subtitle: str | None = None) -> None:
    """Title and subtitle as stacked axes-fraction text, so they never collide."""
    title_y = 1.075 if subtitle else 1.03
    ax.text(0, title_y, title, transform=ax.transAxes, fontsize=13,
            fontweight="bold", color=INK_PRIMARY, va="bottom", ha="left")
    if subtitle:
        ax.text(0, 1.018, subtitle, transform=ax.transAxes, fontsize=9.5,
                color=INK_SECONDARY, va="bottom", ha="left")


def _save(fig: plt.Figure, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def _label(name: str) -> str:
    return name.replace("_", " ")


# -----------------------------------------------------------------------------
def positioning_chart(
    positioning: Positioning,
    categories: pd.Series,
    path: str | Path,
    *,
    note: str | None = None,
) -> Path:
    """Every bank on the traditional <-> challenger axis (BO-02).

    One axis, one dimension - the question is 'which side is ING on', so the
    chart answers exactly that and nothing else.
    """
    scores = positioning.scores
    fig, ax = _figure(9.5, 0.42 * len(scores) + 2.4)

    for x, label in ((0.0, "traditional\ncentroid"), (1.0, "challenger\ncentroid")):
        ax.axvline(x, color=NEUTRAL, lw=1, ls=(0, (4, 3)), zorder=1)
        ax.text(x, len(scores) - 0.3, label, ha="center", va="bottom",
                fontsize=8.5, color=INK_MUTED)

    for i, (bank, score) in enumerate(scores.items()):
        category = categories.get(bank, "traditional")
        colour = CATEGORY_COLOUR[category]
        is_focus = bank == positioning.focus
        ax.plot([0, score], [i, i], color=GRID, lw=1, zorder=2)
        ax.scatter([score], [i], s=190 if is_focus else 120, color=colour,
                   edgecolor=FOCUS_RING if is_focus else SURFACE,
                   linewidth=2.0 if is_focus else 1.5, zorder=3)
        ax.text(score, i + 0.33, f"{bank}  {score:.2f}",
                ha="center", va="bottom", fontsize=9,
                fontweight="bold" if is_focus else "normal",
                color=INK_PRIMARY if is_focus else INK_SECONDARY)

    ax.set_yticks([])
    ax.set_ylim(-0.8, len(scores) + 0.2)
    ax.set_xlim(min(-0.25, scores.min() - 0.15), max(1.25, scores.max() + 0.15))
    ax.set_xlabel("position on the traditional ↔ challenger axis", fontsize=9.5, color=INK_SECONDARY)
    ax.grid(axis="x", color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)

    handles = [plt.Line2D([], [], marker="o", ls="", markersize=8, color=c, label=k)
               for k, c in CATEGORY_COLOUR.items()]
    ax.legend(handles=handles, frameon=False, fontsize=9, loc="lower right",
              bbox_to_anchor=(1, 1.005), labelcolor=INK_SECONDARY, ncols=2)

    # steph 16/09: the focus bank can be legitimately absent (unusable capture).
    # A chart titled "Where does ING sit?" with no ING on it reads as a finding
    # to anyone who sees the PNG without the companion text - and the PNG is the
    # thing that ends up in a deck.
    if positioning.focus in scores.index:
        _title(ax, f"Where does {positioning.focus.upper()} sit?",
               note or f"projection onto the line between group centroids · "
                       f"{positioning.n_features} features")
    else:
        _title(ax, f"The market, without {positioning.focus.upper()}",
               note or f"{positioning.focus.upper()} had no usable capture, so it is not on this "
                       f"chart · {positioning.n_features} features")
        ax.text(0.5, -0.16, f"{positioning.focus.upper()} IS MISSING — this chart cannot answer "
                            f"where {positioning.focus.upper()} stands.",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=9.5, color=CATEGORY_COLOUR["challenger"], fontweight="bold")
    return _save(fig, path)


def deviation_chart(
    deviations: pd.DataFrame,
    path: str | Path,
    *,
    focus: str = "ing",
    top_n: int = 12,
    note: str | None = None,
) -> Path:
    """Diverging bars: how far the focus bank sits from the peer mean (BO-01).

    The job is 'above or below a baseline', so the form is a diverging bar with a
    neutral zero. Poles keep the category hues used everywhere else, so a reader
    who has seen one chart can read this one.
    """
    data = deviations.head(top_n).iloc[::-1]
    fig, ax = _figure(9.5, 0.36 * len(data) + 2.2)

    colours = [CATEGORY_COLOUR["challenger"] if g > 0 else CATEGORY_COLOUR["traditional"]
               for g in data["gap_sd"]]
    y = np.arange(len(data))
    ax.barh(y, data["gap_sd"], color=colours, height=0.6, zorder=3)
    ax.axvline(0, color=INK_SECONDARY, lw=1.1, zorder=4)

    for i, (gap, value) in enumerate(zip(data["gap_sd"], data[f"{focus}_value"])):
        offset = 0.08 if gap >= 0 else -0.08
        ax.text(gap + offset, i, f"{gap:+.1f} SD · {value:,.2f}",
                va="center", ha="left" if gap >= 0 else "right",
                fontsize=8.5, color=INK_SECONDARY)

    ax.set_yticks(y, [_label(f) for f in data["feature"]], fontsize=9)
    span = float(np.abs(data["gap_sd"]).max()) * 1.42
    ax.set_xlim(-span, span)
    ax.set_xlabel("gap from the peer mean, in peer standard deviations",
                  fontsize=9.5, color=INK_SECONDARY)
    ax.grid(axis="x", color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)

    _title(ax, f"{focus.upper()} against its peers, feature by feature",
           note or f"the {top_n} features with the largest gap · positive = above the peer mean")
    return _save(fig, path)


def category_effect_chart(
    comparison: pd.DataFrame,
    path: str | Path,
    *,
    top_n: int = 12,
    note: str | None = None,
) -> Path:
    """Which features separate traditional banks from challengers, and how far."""
    data = comparison.head(top_n).iloc[::-1]
    fig, ax = _figure(9.5, 0.36 * len(data) + 2.2)

    colours = [CATEGORY_COLOUR["challenger"] if d > 0 else CATEGORY_COLOUR["traditional"]
               for d in data["effect_size_d"]]
    y = np.arange(len(data))
    ax.barh(y, data["effect_size_d"], color=colours, height=0.6, zorder=3)
    ax.axvline(0, color=INK_SECONDARY, lw=1.1, zorder=4)

    for i, row in enumerate(data.itertuples()):
        d = row.effect_size_d
        offset = 0.12 if d >= 0 else -0.12
        ax.text(d + offset, i,
                f"{row.traditional_mean:,.2f} → {row.challenger_mean:,.2f}",
                va="center", ha="left" if d >= 0 else "right",
                fontsize=8.5, color=INK_SECONDARY)

    ax.set_yticks(y, [_label(f) for f in data["feature"]], fontsize=9)
    span = float(np.abs(data["effect_size_d"]).max()) * 1.55
    ax.set_xlim(-span, span)
    ax.set_xlabel("effect size (Cohen's d) — descriptive separation, not a significance test",
                  fontsize=9.5, color=INK_SECONDARY)
    ax.grid(axis="x", color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)

    handles = [plt.Line2D([], [], marker="s", ls="", markersize=8, color=c, label=f"higher for {k}s")
               for k, c in CATEGORY_COLOUR.items()]
    ax.legend(handles=handles, frameon=False, fontsize=9, loc="lower right",
              bbox_to_anchor=(1, 1.005), labelcolor=INK_SECONDARY, ncols=2)

    _title(ax, "What separates traditional banks from challengers",
           note or f"the {top_n} features with the largest separation")
    return _save(fig, path)


def similarity_heatmap(
    distances: pd.DataFrame,
    path: str | Path,
    *,
    note: str | None = None,
) -> Path:
    """Pairwise distance between banks (BO-03). One hue, near = light, far = dark."""
    fig, ax = _figure(0.72 * len(distances) + 3.4, 0.72 * len(distances) + 2.8)

    data = distances.to_numpy()
    mesh = ax.imshow(data, cmap=SEQUENTIAL, vmin=0, vmax=float(data.max()))

    labels = [_label(b) for b in distances.index]
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(labels)), labels, fontsize=9)

    # Every cell is direct-labelled, so the chart doubles as its own table view.
    threshold = float(data.max()) * 0.55
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{data[i, j]:.1f}", ha="center", va="center", fontsize=8,
                    color="#ffffff" if data[i, j] > threshold else INK_PRIMARY)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    bar = fig.colorbar(mesh, ax=ax, fraction=0.045, pad=0.03)
    bar.set_label("distance in standardised feature space", fontsize=9, color=INK_SECONDARY)
    bar.ax.tick_params(labelsize=8, colors=INK_SECONDARY, length=0)
    bar.outline.set_visible(False)

    _title(ax, "Which banks communicate alike", note or "lower = more similar · diagonal is self-distance")
    return _save(fig, path)
