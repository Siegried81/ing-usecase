"""Generate the chart companion: what each chart measures, and what it does not.

steph 15/09, new module. A chart in a deck gets read by someone who was not in
the room when it was made, so every figure this project produces ships with the
mechanic behind it, the reading instructions, and its limits.

GENERATED, not hand-written, for two reasons:
  * outputs/ is wiped on every run - a hand-written note would not survive.
  * the "what this run shows" paragraphs are built from the same objects the
    charts are drawn from, so the prose cannot drift away from the picture.

Each section also carries a small table of the values behind the chart. That is
the accessibility fallback for the figure (colour is never the only carrier of
meaning) and it doubles as the number a reader wants to quote.
"""

from __future__ import annotations

import pandas as pd

from comparator.analysis import Positioning, render_accounting

SYNTHETIC_WARNING = (
    "> ### These numbers are not findings\n"
    ">\n"
    "> Every value below comes from `data/fixtures/synthetic_sample.csv`, which is\n"
    "> **invented**. Its per-bank archetypes were written from the claims in the ING\n"
    "> kickoff deck, so the charts are shaped like real results and are not real\n"
    "> results. They exist to prove the chain works end to end before the real\n"
    "> captures land.\n"
)


def _fmt(value: object, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "-"
    if isinstance(value, float):
        return f"{value:,.{digits}f}" if abs(value) < 1000 else f"{value:,.0f}"
    return str(value)


def _table(df: pd.DataFrame, columns: list[str], headers: list[str], rows: int = 6) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in df.head(rows).itertuples():
        out.append("| " + " | ".join(_fmt(getattr(row, c)) for c in columns) + " |")
    return out


def _positioning_section(positioning: Positioning, categories: pd.Series) -> list[str]:
    scores = positioning.scores
    focus = positioning.focus
    # steph 16/09: the focus bank can be legitimately absent - ING's own capture
    # came back an unrendered shell on the first live run. The market section is
    # still worth writing; the ING answer is not available, and says so.
    focus_score = positioning.focus_score if positioning.has_focus else None

    traditional = scores[[b for b in scores.index if categories.get(b) == "traditional"]]
    challenger = scores[[b for b in scores.index if categories.get(b) == "challenger"]]
    gap = challenger.min() - traditional.max()

    lines = [
        "## 1. Where does ING sit?",
        "",
        "![Banks positioned on the traditional-challenger axis](01_positioning.png)",
        "",
        "**What it measures.** Every bank is reduced to a vector of standardised features, "
        "and the two business models are reduced to their centroids — the average traditional "
        "bank and the average challenger. The line between those two points is the axis. Each "
        "bank is projected onto it and rescaled so **0 is the traditional centroid and 1 is the "
        "challenger centroid**. A bank can land outside 0–1 by being more typical of its group "
        "than the group average.",
        "",
        "**Why an axis and not a cluster.** The stakeholders asked a directional question — "
        "\"are we closer to traditional banks or to challenger banks?\" A cluster label answers "
        "*which group*; this answers *how far along*, which is the question actually asked (BO-02).",
        "",
        "**How to read it.** Left is traditional, right is challenger. Colour carries the bank's "
        "declared category, so a dot far from its own colour's cluster is the interesting case. "
        f"{focus.upper()} is ringed and bold.",
        "",
    ]

    if focus_score is None:
        lines += [
            f"**{focus.upper()} IS NOT IN THIS CHART.** Its capture was unusable, so it was "
            "excluded from the dataset. **BO-01 and BO-02 cannot be answered from this run** — "
            "everything here describes the market without us in it. See `limitations.md`.",
            "",
            f"The axis is still computed over {positioning.n_features} features and still "
            "separates the two groups, so it is ready the moment a usable page exists.",
            "",
        ]
    else:
        lines += [
            f"**What this run shows.** {focus.upper()} scores **{focus_score:.2f}** — "
            f"{positioning.verdict}. Computed over {positioning.n_features} features.",
            "",
        ]

    if len(traditional) and len(challenger):
        lines += [
            f"The two groups do not overlap: the most challenger-like incumbent sits at "
            f"{traditional.max():.2f} and the most traditional challenger at {challenger.min():.2f}, "
            f"a gap of {gap:.2f}. That separation is what makes the axis meaningful — if the groups "
            "interleaved, the projection would be measuring noise.",
            "",
        ]

    lines += ["| Bank | Category | Position |", "| --- | --- | --- |"]
    for bank, score in scores.items():
        marker = " **(focus)**" if bank == focus else ""
        lines.append(f"| {bank}{marker} | {categories.get(bank, '?')} | {score:.2f} |")

    lines += [
        "",
        "**What it cannot tell you.** The axis is defined by the banks in this dataset. Add or "
        "remove a bank and the centroids move, so a score is a position *within this sample*, not "
        "an absolute coordinate. It also says nothing about which end is better.",
        "",
    ]
    return lines


def _deviation_section(deviations: pd.DataFrame, focus: str, n_peers: int) -> list[str]:
    if deviations.empty:
        return [
            f"## 2. {focus.upper()} against its peers, feature by feature",
            "",
            f"**Not produced.** There is no usable {focus.upper()} page in this dataset, so there "
            "is nothing to compare against its peers. See `limitations.md`.",
            "",
        ]
    top = deviations.head(3)
    lines = [
        f"## 2. {focus.upper()} against its peers, feature by feature",
        "",
        f"![{focus.upper()} deviation from the peer mean](02_ing_vs_peers.png)",
        "",
        "**What it measures.** For each feature: the focus bank's value minus the mean of every "
        "other bank, divided by the peer standard deviation. The result is a **gap in peer standard "
        "deviations**, which is what lets word counts, ratios and yes/no features sit in one chart "
        "without a second axis.",
        "",
        "**How to read it.** Bars right mean above the peer mean, bars left mean below. The zero "
        "line is the peer average, not zero of the underlying feature. Features are ranked by the "
        "size of the gap, so the top of the chart is where this bank is least like the others.",
        "",
        "**A gap is not a fault.** Being 2 SD from the peer mean might be a deliberate brand "
        "choice or a weakness. The chart finds where to look; deciding which is a judgement call "
        "that belongs in the business narrative.",
        "",
    ]
    if len(top):
        first = top.iloc[0]
        lines += [
            f"**What this run shows.** The largest gap is **{first['feature'].replace('_', ' ')}** "
            f"at {first['gap_sd']:+.1f} SD ({focus} {_fmt(first[f'{focus}_value'])} against a peer "
            f"mean of {_fmt(first['peer_mean'])}).",
            "",
        ]
    lines += _table(
        deviations, ["feature", "dimension", f"{focus}_value", "peer_mean", "gap_sd"],
        ["Feature", "Dimension", f"{focus}", "Peer mean", "Gap (SD)"], rows=8,
    )
    lines += [
        "",
        f"**What it cannot tell you.** With {n_peers} peers the standard deviation is estimated "
        "from a handful of values, so a large gap on a feature where peers happen to agree "
        "closely is easy to overstate. Read the raw values in the table, not only the SD.",
        "",
    ]
    return lines


def _category_section(comparison: pd.DataFrame, n_traditional: int, n_challenger: int) -> list[str]:
    lines = [
        "## 3. What separates traditional banks from challengers",
        "",
        "![Features ranked by separation between the two groups](03_category_separation.png)",
        "",
        "**What it measures.** For each feature, the difference between the two group means, "
        "expressed as **Cohen's d** — the difference divided by the pooled standard deviation. "
        "Standardising this way makes features on wildly different scales rankable against each "
        "other.",
        "",
        "**How to read it.** Bars right are higher at challengers, bars left are higher at "
        "traditional banks. The label on each bar gives the two raw group means, so the effect "
        "size never has to be taken on trust. Order is by size of separation.",
        "",
        "**This is descriptive, not a significance test.** Cohen's d is being used here purely as "
        f"a *ranking device* for which features separate the groups most. With {n_traditional} "
        f"bank(s) on one side and {n_challenger} on the other, no p-value would be meaningful, and "
        "none is computed anywhere in this project (PRD risk R-03).",
        "",
    ]
    if len(comparison):
        first = comparison.iloc[0]
        lines += [
            f"**What this run shows.** The sharpest separator is "
            f"**{first['feature'].replace('_', ' ')}** (traditional {_fmt(first['traditional_mean'])} "
            f"vs challenger {_fmt(first['challenger_mean'])}, d = {first['effect_size_d']:+.2f}).",
            "",
        ]
    lines += _table(
        comparison, ["feature", "traditional_mean", "challenger_mean", "effect_size_d"],
        ["Feature", "Traditional", "Challenger", "Cohen's d"], rows=8,
    )
    lines += [
        "",
        "**What it cannot tell you.** A feature can separate the groups perfectly and still be "
        "irrelevant — the split is by business model, so anything that correlates with being a "
        "digital-first bank will show up here whether or not it is a communication choice.",
        "",
    ]
    return lines


def _similarity_section(distances: pd.DataFrame, clusters: pd.Series, focus: str) -> list[str]:
    lines = [
        "## 4. Which banks communicate alike",
        "",
        "![Pairwise distance between banks](04_similarity.png)",
        "",
        "**What it measures.** Euclidean distance between every pair of banks in standardised "
        "feature space. Each bank's pages are averaged into one vector first, so this compares "
        "banks, not pages.",
        "",
        "**How to read it.** One hue, light to dark: **light means similar, dark means far apart**. "
        "The diagonal is a bank against itself and is always 0. The matrix is symmetric, so it "
        "reads the same in either direction. Every cell is labelled, so the figure is also its own "
        "table.",
        "",
        "**Why a single hue.** Distance is a magnitude, not an identity — a categorical palette "
        "here would imply the banks are categories of distance, which they are not.",
        "",
    ]
    if focus in distances.index:
        nearest = distances.loc[focus].drop(index=focus).sort_values()
        lines += [
            f"**What this run shows.** The banks closest to {focus.upper()} are "
            + ", ".join(f"**{b}** ({d:.1f})" for b, d in nearest.head(3).items())
            + ".",
            "",
        ]
    lines += ["| Cluster | Banks |", "| --- | --- |"]
    for label in sorted(clusters.unique()):
        lines.append(f"| {label} | {', '.join(clusters[clusters == label].index)} |")
    lines += [
        "",
        "Clusters come from hierarchical clustering (Ward linkage) on the same distances.",
        "",
        "**What it cannot tell you.** Distance is unweighted — every feature counts the same, so "
        "a dozen correlated layout features will outvote a single strong tone feature. Clustering "
        "always returns clusters, including when there is no real structure to find; the cluster "
        "labels are only interesting because they were *not* told which bank is which.",
        "",
    ]
    return lines


def build_chart_report(
    *,
    positioning: Positioning,
    categories: pd.Series,
    deviations: pd.DataFrame,
    comparison: pd.DataFrame,
    distances: pd.DataFrame,
    clusters: pd.Series,
    claims: pd.DataFrame | None = None,
    focus: str = "ing",
    dataset_path: str = "",
    n_pages: int = 0,
    n_banks: int = 0,
    synthetic: bool = False,
    accounting: dict | None = None,
) -> str:
    """Build the markdown companion for the four charts."""
    lines = [
        "# What the charts measure",
        "",
        "Companion to the figures in this folder. Each section says what the chart is "
        "actually computing, how to read it, what this particular run shows, and what it "
        "cannot support — in that order.",
        "",
        f"*Generated by `scripts/run_analysis.py` from `{dataset_path}` — "
        f"{n_pages} pages across {n_banks} banks.*",
        "",
    ]
    if synthetic:
        lines += [SYNTHETIC_WARNING, ""]

    if accounting:
        lines += ["---", "", "## Why the charts use fewer features than the dictionary has", "",
                  "The dictionary defines "
                  f"{accounting['dictionary_total']} features. The comparisons here use "
                  f"**{accounting['n_used']}**. Nothing is thrown away quietly — this is the "
                  "whole reduction:",
                  "", "```", render_accounting(accounting), "```", ""]
        if not accounting["categorical_included"]:
            lines += [
                f"**The line worth arguing about is the {len(accounting['categorical'])} "
                "categorical and list features.** They are not free text and not redundant — "
                "things like `benefit_framing`, `fab_level`, `layout_archetype`, "
                "`dominant_image_type`, `persuasion_levers`, and seven of the banking-domain "
                "dimensions. A euclidean distance cannot take a raw category, so they sit out "
                "of every distance and positioning calculation today.",
                "",
                "They *can* be included (`include_categorical=True`), one-hot encoded with each "
                "feature's indicators scaled by 1/√k so a 5-value category does not silently "
                "outweigh five numbers. It is off by default because switching it on moves "
                "every number in the analysis, which is a team decision rather than a default.",
                "",
            ]
        lines += [
            "The four bands (`word_count_band` and friends) are excluded on purpose: each is a "
            "coarser view of a number already in the matrix, so counting both would double the "
            "weight of that signal.",
            "",
        ]

    lines += ["---", ""]
    lines += _positioning_section(positioning, categories)
    lines += ["---", ""]
    n_peers = max(0, len(positioning.scores) - 1)
    n_traditional = int((categories == "traditional").sum())
    n_challenger = int((categories == "challenger").sum())
    lines += _deviation_section(deviations, focus, n_peers)
    lines += ["---", ""]
    lines += _category_section(comparison, n_traditional, n_challenger)
    lines += ["---", ""]
    lines += _similarity_section(distances, clusters, focus)
    lines += ["---", ""]

    if claims is not None and len(claims):
        lines += [
            "## Appendix — the kickoff-deck observations",
            "",
            "Not a chart, but the same discipline: the deck's five eyeball observations, "
            "tested against the data (FR-14).",
            "",
        ]
        if synthetic:
            lines += [
                "> **Circular on fixture data.** The fixture archetypes were written *from* these "
                "claims, so they always come back supported. This table only means something "
                "against real captures.",
                "",
            ]
        lines += ["| # | Claim | Verdict | Evidence |", "| --- | --- | --- | --- |"]
        for row in claims.itertuples():
            lines.append(f"| {row.id} | {row.claim} | {row.verdict} | {row.evidence} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## Reading any of these honestly",
        "",
        "- **Sample size.** A handful of pages per bank. Everything here is descriptive; "
        "nothing in this project computes a p-value or claims significance.",
        "- **One moment in time.** Campaign pages change without notice. Every conclusion is "
        "valid for the capture date recorded in the dataset and no later.",
        "- **Judgement-based features.** Rubric-scored and model-assisted features carry the "
        "opinion of a rubric or a model. They are marked as such in the feature dictionary, and "
        "the model that produced them is recorded per row.",
        "- **No performance data.** Nothing here links a design choice to a click, a conversion "
        "or a sale. Where a difference is found, the honest framing is a hypothesis ING could "
        "test, never a cause.",
        "",
    ]
    return "\n".join(lines)
