#!/usr/bin/env python3
"""End-to-end analysis skeleton: dataset in, profiles / comparisons / charts out.

    python3 scripts/run_analysis.py --no-strict          # real collected data
    python3 scripts/run_analysis.py --dataset <other.csv>

This is the chain the Day 6 gate asks about (Project Plan section 6): a dataset
becomes a positioned, profiled, charted comparison with no manual step in between.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd

from comparator import load_dictionary
from comparator import ai_score  # sieg 19/09
from comparator import cross_sell  # sieg 19/09
from comparator import reputation  # sieg 19/09
from comparator.analysis import (
    category_comparison,
    family_options,
    scope_to_family,
    feature_accounting,
    render_accounting,
    check_deck_claims,
    cluster_banks,
    ing_vs_peers,
    lever_frequency,
    nearest_neighbours,
    positioning_axis,
    similarity_matrix,
)
from comparator.charts import (
    category_effect_chart,
    deviation_chart,
    positioning_chart,
    similarity_heatmap,
)
from comparator.limitations import assess, render as render_limitations
from comparator.profiles import build_all, render_all_markdown
from comparator.report import build_chart_report
from comparator.schema import read_dataset
from comparator.trends import context_or_none

DEFAULT_DATASET = Path("data/processed/campaigns.csv")
DEFAULT_OUTDIR = Path("outputs")
SYNTHETIC_BANNER = (
    "=" * 78 + "\n"
    "  SYNTHETIC DATA — every value below is invented. These are NOT findings.\n"
    "  Replace with Dan's real captures before anything here reaches a deck.\n"
    + "=" * 78
)


def _header(text: str) -> None:
    print(f"\n{text}\n{'-' * len(text)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--focus", default="ing")
    parser.add_argument("--clusters", type=int, default=2)
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument(
        "--product-family", default=None,
        help="restrict the comparison to one product family (DR-04). Pooling families "
             "confounds every cross-bank difference with the product. Use 'auto' to pick "
             "the family with banks on both sides of the traditional/challenger split.",
    )
    parser.add_argument(
        "--trends-dir", type=Path, default=None,
        help="Dan's kbc-ing-benchmark/export directory. Adds search-interest CONTEXT "
             "for ING/KBC/CBC. Skipped silently when absent.",
    )
    parser.add_argument(
        "--no-strict", action="store_true",
        help="continue when the dataset is incomplete. Real collected data fails strict "
             "validation until the 13 rubric features are scored (scripts/rubric_sheet.py).",
    )
    args = parser.parse_args()

    fd = load_dictionary()
    args.outdir.mkdir(parents=True, exist_ok=True)

    # --- 1. load and validate ------------------------------------------------
    _header(f"1. Dataset — {args.dataset}")
    df, report = read_dataset(args.dataset, fd, tier="core", strict=not args.no_strict)
    print(report.render())
    if not report.ok:
        print("\n  Continuing with --no-strict. Anything the missing columns feed is absent "
              "from the results below, not estimated.")

    synthetic = "data_source" in df and (df["data_source"] == "synthetic_fixture").any()
    if synthetic:
        print(f"\n{SYNTHETIC_BANNER}")
    note = "SYNTHETIC FIXTURE DATA — not findings" if synthetic else None

    # LLM-generated rows are scored, never mixed into the bank comparison.
    banks_df = df[df["data_source"] != "llm_generated"] if "data_source" in df else df

    # steph 16/09: a maintenance page and an unrendered shell are honest
    # measurements of the wrong page. Left in, they would characterise a bank
    # from content it never showed - see collection/quality.py.
    # --- restrict to one product family (DR-04) ------------------------------
    # steph 16/09: this was carried as a limitation on every run. It does not
    # have to be one - it can be a filter.
    _header("Product families available")
    options = family_options(banks_df[banks_df.get("capture_quality", "ok") != "unusable"]
                             if "capture_quality" in banks_df.columns else banks_df)
    print(options.to_string(index=False) if not options.empty else "  (no product_family column)")

    family = args.product_family
    if family == "auto":
        usable = options[options["comparable"]] if not options.empty else options
        family = usable.iloc[0]["product_family"] if not usable.empty else None
        print(f"\n  --product-family auto -> {family!r}")

    all_banks_df = banks_df  # before exclusions - D-09 must see what was dropped
    if "capture_quality" in banks_df.columns:
        unusable = banks_df[banks_df["capture_quality"] == "unusable"]
        if not unusable.empty:
            print(f"\n  EXCLUDING {len(unusable)} unusable capture(s): "
                  f"{sorted(unusable['bank'].unique())} - see outputs/limitations.md")
            banks_df = banks_df[banks_df["capture_quality"] != "unusable"]

    banks_df, scope = scope_to_family(banks_df, family)
    print(f"\n{scope.render()}")
    if family and not scope.comparable:
        print("\n  Refusing to continue: with one side of the split empty there is no "
              "traditional-vs-challenger comparison to make.")
        return 2
    print(f"\n{len(banks_df)} page(s) · {banks_df['bank'].nunique()} banks · "
          f"{banks_df['product_family'].nunique()} product family/families")

    # --- 2. bank profiles (Plan, Appendix A) ---------------------------------
    _header("2. Bank profiles")
    profiles = build_all(banks_df, fd)
    markdown = render_all_markdown(profiles, fd)
    # sieg 17/09 audit, point 1: this file listed 7 banks while the dataset had 9,
    # with nothing on the page to say why. The scope belongs on the artefact, not
    # only in the console output of the run that produced it.
    scope_note = ""
    if scope.family:
        scope_note = (
            f"> **Scope: `{scope.family}` product family only** — {len(scope.banks)} of "
            f"{len(scope.banks) + len(scope.dropped_banks)} banks with usable captures.\n"
        )
        if scope.dropped_banks:
            scope_note += (
                f"> Not shown: {', '.join(scope.dropped_banks)} — usable captures, but no page in "
                "this family. Comparing across families would confound every difference with the "
                "product (DR-04).\n"
            )
        scope_note += "\n"
    (args.outdir / "bank_profiles.md").write_text(
        (f"> **{note}**\n\n" if note else "") + scope_note + "# Bank profile cards\n\n" + markdown,
        encoding="utf-8",
    )
    (args.outdir / "bank_profiles.json").write_text(
        json.dumps({"_scope": {"product_family": scope.family,
                               "banks_included": scope.banks,
                               "banks_excluded_no_page_in_family": scope.dropped_banks},
                    "profiles": profiles}, indent=2, default=str), encoding="utf-8")
    for bank, profile in profiles.items():
        signature = ", ".join(f"{n} {z:+.1f}SD" for n, z in profile["signature"])
        print(f"  {bank:<20} {profile['identity']['category']:<12} {signature}")

    # --- 3. where the dictionary's features go -------------------------------
    # steph 15/09, after Sieg asked why a chart said "50 features" with 97 in the
    # dictionary. The reduction was legitimate but invisible; now it is printed
    # on every run and carried next to the figure in charts.md.
    _header("3. Feature accounting")
    accounting = feature_accounting(banks_df, fd)
    print(render_accounting(accounting))

    # --- 3b. AI Score (sieg 19/09) --------------------------------------------
    # Deterministic, from features already in the dataset - no new LLM call.
    # See comparator/ai_score.py's module docstring for the formulas and caveats.
    _header("3b. AI Score (Digital / Trust / Cross-sell / Personalisation / Innovation / Simplicity)")
    scores = ai_score.score_all(banks_df)
    for bank, axes in scores.items():
        rendered = ", ".join(f"{axis}={value if value is not None else '-'}" for axis, value in axes.items())
        print(f"  {bank:<20} {rendered}")
    pd.DataFrame(scores).T.to_csv(args.outdir / "ai_score.csv", index_label="bank")

    # --- 3c. Cross-sell (sieg 19/09) -------------------------------------------
    # cross_sold_products / possible other products, plus the product co-
    # occurrence matrix - see comparator/cross_sell.py for the exact formulas.
    _header("3c. Cross-sell score and product matrix")
    cross_sell_scores = cross_sell.score_all(banks_df, fd)
    for bank, score in cross_sell_scores.items():
        print(f"  {bank:<20} {score if score is not None else '-'}")
    pd.Series(cross_sell_scores, name="cross_sell_score").to_csv(args.outdir / "cross_sell_score.csv", index_label="bank")
    matrix = cross_sell.cross_sell_matrix(banks_df, fd)
    matrix.to_csv(args.outdir / "cross_sell_matrix.csv", index_label="product_family")
    top_pairs = cross_sell.most_associated(matrix, n=3)
    if top_pairs:
        print("  most associated: " + ", ".join(f"{a}+{b} ({n})" for a, b, n in top_pairs))
    never = cross_sell.never_paired(matrix, banks_df.groupby("product_family").size())
    print(f"  never paired: {len(never['confirmed'])} confirmed, "
          f"{len(never['insufficient_data'])} not enough data to say")

    # --- 4. BO-02 positioning ------------------------------------------------
    _header("4. Positioning on the traditional ↔ challenger axis (BO-02)")
    positioning = positioning_axis(banks_df, fd, focus=args.focus)
    for bank, score in positioning.scores.items():
        marker = "  <-- focus" if bank == args.focus else ""
        print(f"  {bank:<20} {score:6.2f}{marker}")
    if positioning.has_focus:
        print(f"\n  {args.focus.upper()} scores {positioning.focus_score:.2f} — {positioning.verdict}.")
    else:
        print(f"\n  {args.focus.upper()} IS NOT IN THE USABLE DATA — BO-01 and BO-02 cannot be "
              f"answered.\n  Everything below describes the market without us in it.")
    print(f"  (0 = traditional centroid, 1 = challenger centroid, {positioning.n_features} features)")

    categories = banks_df.drop_duplicates("bank").set_index("bank")["bank_category"]
    positioning_chart(positioning, categories, args.outdir / "01_positioning.png", note=note)

    # --- 5. BO-01 ING vs peers -----------------------------------------------
    _header(f"5. {args.focus.upper()} against its peers (BO-01)")
    if not positioning.has_focus:
        print(f"  skipped - no usable {args.focus} page. See outputs/limitations.md.")
        deviations = None
    else:
        deviations = ing_vs_peers(banks_df, fd, focus=args.focus)
        print(deviations.head(args.top_n).to_string(
            index=False,
            columns=["feature", "dimension", f"{args.focus}_value", "peer_mean", "gap_sd"],
            float_format=lambda v: f"{v:,.2f}",
        ))
        deviations.to_csv(args.outdir / "ing_vs_peers.csv", index=False)
        deviation_chart(deviations, args.outdir / "02_ing_vs_peers.png",
                        focus=args.focus, top_n=args.top_n, note=note)

    # --- 6. traditional vs challenger ----------------------------------------
    _header("6. Traditional vs challenger")
    comparison = category_comparison(banks_df, fd)
    print(comparison.head(args.top_n).to_string(
        index=False,
        columns=["feature", "traditional_mean", "challenger_mean", "effect_size_d"],
        float_format=lambda v: f"{v:,.2f}",
    ))
    comparison.to_csv(args.outdir / "category_comparison.csv", index=False)
    category_effect_chart(comparison, args.outdir / "03_category_separation.png", top_n=args.top_n, note=note)

    # --- 7. BO-03 similarity -------------------------------------------------
    _header("7. Which banks communicate alike (BO-03)")
    distances = similarity_matrix(banks_df, fd)
    clusters = cluster_banks(banks_df, fd, n_clusters=args.clusters)
    for label in sorted(clusters.unique()):
        members = ", ".join(clusters[clusters == label].index)
        print(f"  cluster {label}: {members}")
    if positioning.has_focus:
        print(f"\n  nearest to {args.focus}:")
        for bank, distance in nearest_neighbours(banks_df, fd, focus=args.focus).items():
            print(f"    {bank:<20} {distance:.2f}")
    else:
        print(f"\n  nearest to {args.focus}: skipped - no usable {args.focus} page.")
    distances.to_csv(args.outdir / "similarity_matrix.csv")
    similarity_heatmap(distances, args.outdir / "04_similarity.png", note=note)

    # --- 8. FR-14 deck claims ------------------------------------------------
    _header("8. Kickoff-deck observations, tested (FR-14)")
    claims = check_deck_claims(banks_df, fd)
    if synthetic:
        print("  CIRCULAR ON FIXTURE DATA: the fixture archetypes were built FROM these\n"
              "  claims, so they will always come back supported. This section only means\n"
              "  something against real captures.\n")
    print(claims.to_string(index=False, columns=["id", "claim", "verdict", "evidence"]))
    claims.to_csv(args.outdir / "deck_claims.csv", index=False)

    # --- 9. the chart companion ----------------------------------------------
    # steph 15/09: every figure ships with the mechanic behind it and its limits,
    # generated from the same objects the charts are drawn from so the prose
    # cannot drift away from the picture.
    _header("9. Chart companion")
    companion = build_chart_report(
        positioning=positioning, categories=categories,
        deviations=deviations if deviations is not None else pd.DataFrame(
            columns=["feature", "dimension", f"{args.focus}_value", "peer_mean", "gap_sd"]),
        comparison=comparison, distances=distances, clusters=clusters, claims=claims,
        focus=args.focus, dataset_path=str(args.dataset),
        n_pages=len(banks_df), n_banks=int(banks_df["bank"].nunique()),
        synthetic=synthetic, accounting=accounting,
    )
    (args.outdir / "charts.md").write_text(companion, encoding="utf-8")
    print(f"  wrote {args.outdir / 'charts.md'} ({len(companion.splitlines())} lines)")

    # --- 12. persuasion levers ------------------------------------------------
    # --- 10. D-09 limitations ------------------------------------------------
    # steph 16/09: I am R on D-09. Generated from the dataset so an inconvenient
    # limitation cannot be quietly forgotten while writing the deck on Day 9.
    _header("10. Limitations (D-09)")
    # steph 16/09: the UNFILTERED frame. Passing the filtered one made D-09 stop
    # mentioning the excluded banks entirely - the limitation disappeared because
    # we had acted on it, which is exactly backwards.
    assessment = assess(all_banks_df, fd, focus=args.focus, scope=scope)
    (args.outdir / "limitations.md").write_text(
        render_limitations(assessment, synthetic=synthetic), encoding="utf-8")
    for label in ("blocking", "material"):
        for item in assessment[label]:
            flat = " ".join(item.replace("**", "").split())
            print(f"  [{label}] {flat[:150]}")
    print(f"  -> {args.outdir / 'limitations.md'}")

    # --- 11. search-interest context (Dan's Google Trends benchmark) ---------
    # steph 16/09: CONTEXT, never an outcome. See src/comparator/trends.py for
    # why joining this to page features would be the worst error available to us.
    _header("11. Search interest context (Dan's trends benchmark)")
    trends_ctx = (context_or_none(banks_df, args.trends_dir) if args.trends_dir
                  else context_or_none(banks_df))
    if trends_ctx is None:
        print("  exports not present - skipped. Nothing else is affected.")
    else:
        print(trends_ctx.render())
        (args.outdir / "search_interest_context.md").write_text(
            "# Search interest context\n\n"
            "> Google Trends, via Dan's kbc-ing-benchmark. **Context, not performance.**\n"
            "> This is what people searched for, not what any campaign achieved, and the\n"
            "> pages captured are today's pages - not the pages live during an older spike.\n\n"
            "```\n" + trends_ctx.render() + "\n```\n", encoding="utf-8")

    # --- 11b. bank reputation (NewsAPI, optional) -----------------------------
    # sieg 19/09: same optional/degrade-gracefully shape as the trends step
    # above. Themes only, never sentiment - see comparator/reputation.py.
    _header("11b. Bank reputation (NewsAPI, optional)")
    rep_banks = [(b, b) for b in sorted(banks_df["bank"].unique())]
    reputation_dashboard = reputation.build_dashboard(rep_banks)
    if not reputation_dashboard["available"]:
        print("  NEWSAPI_KEY not set - skipped. Nothing else is affected.")
    else:
        for bank, snapshot in reputation_dashboard["banks"].items():
            if snapshot is None:
                print(f"  {bank:<20} no headlines found")
            else:
                themes = ", ".join(f"{t}={c}" for t, c in snapshot["themes"].items() if c)
                print(f"  {bank:<20} {snapshot['headline_count']} headlines - {themes or 'no theme detected'}")
        (args.outdir / "reputation.json").write_text(
            json.dumps(reputation_dashboard, indent=2, ensure_ascii=False), encoding="utf-8")

    _header("12. Persuasion levers by category")
    levers = lever_frequency(banks_df)
    if not levers.empty:
        print(levers.to_string())
        levers.to_csv(args.outdir / "persuasion_levers.csv")

    _header("Done")
    for path in sorted(args.outdir.iterdir()):
        print(f"  {path}")
    if synthetic:
        print(f"\n{SYNTHETIC_BANNER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
