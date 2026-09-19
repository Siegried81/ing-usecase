#!/usr/bin/env python3
"""Export one JSON the business web UI renders.

    python3 scripts/export_web_report.py --dataset data/processed/campaigns_scored.csv \
        --product-family auto

steph 17/09. The UI reads a single snapshot file and needs no server, which is
deliberate: a browser talking to a laptop is the wrong thing to depend on five
minutes before a stakeholder presentation, and a snapshot is the honest shape
for a finding anyway - it is true for one dataset at one capture date.

Reads the LIBRARY, not the output files. Re-parsing our own CSVs and markdown
would be a second, lossier definition of every number on the screen.

Everything the deck must not drop travels with the data: the scope, the capture
window, the sample sizes, the excluded banks and the limitations. The UI cannot
render a number without being handed what qualifies it.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap  # noqa: F401

import pandas as pd

from comparator import load_dictionary
from comparator import ai_score  # sieg 19/09
from comparator import cross_sell  # sieg 19/09
from comparator import reputation  # sieg 19/09
from comparator.analysis import (
    category_comparison,
    check_deck_claims,
    cluster_banks,
    family_options,
    ing_vs_peers,
    nearest_neighbours,
    positioning_axis,
    scope_to_family,
    similarity_matrix,
)
from comparator.limitations import assess
from comparator.profiles import build_all
from comparator.schema import read_dataset
from comparator.trends import build_trends_dashboard

DEFAULT_DATASET = Path("data/processed/campaigns_scored.csv")
DEFAULT_OUT = Path("web/public/report.json")

# Plain-language names for the features a business reader will actually see.
# The dictionary's own definitions are precise and unreadable in a deck; these
# are the same features said out loud.
LABELS = {
    "word_count": "Words on the page",
    "sentence_count": "Sentences",
    "avg_sentence_length": "Words per sentence",
    "readability_score": "Readability",
    "numeric_claim_count": "Figures and percentages quoted",
    "second_person_ratio": "Speaks to “you” rather than “we”",
    "first_person_plural_count": "Talks about “we”",
    "question_count": "Questions asked",
    "urgency_marker_count": "Urgency and deadline language",
    "image_count": "Images",
    "total_image_area_ratio": "Share of the page that is imagery",
    "hero_image_area_ratio": "Size of the opening image",
    "has_animation": "Uses animation",
    "animated_asset_count": "Animated elements",
    "page_height_px": "Page length",
    "cta_count": "Calls to action",
    "cta_above_fold": "Call to action visible without scrolling",
    "cta_contrast_ratio": "Call-to-action contrast",
    "text_to_image_ratio": "Words per image",
    "section_count": "Content sections",
    "above_fold_element_count": "Elements visible without scrolling",
    "brand_colour_share": "Brand colour on the page",
    "background_luminance": "Page brightness",
    "disclaimer_word_share": "Share of words that are legal small print",
    "disclaimer_present": "Carries legal small print",
    "formality_score": "Formality of tone",
    "clarity_score": "Clarity",
    "value_prop_clarity": "Clarity of the offer",
    "aida_coverage_score": "Campaign structure completeness (AIDA)",
    "aida_attention": "Opens with something that stops the reader",
    "aida_interest": "Gives a reason to keep reading",
    "aida_desire": "Makes the offer feel worth having",
    "aida_action": "Has an unmistakable next step",
    "rate_prominence": "How prominently the rate is shown",
    "text_image_layout": "Text and image arrangement",
    "layout_archetype": "Page layout pattern",
    "accent_locations": "Where the brand colour appears",
    "mobile_first_design_signal": "Designed mobile-first",
    "green_product_specific_benefit": "Names a concrete green benefit",
    "secondary_bank_positioning": "Positions as a second bank",
    "branch_network_cited_as_benefit": "Cites its branch network",
    "accent_colour_count": "Distinct accent colours",
    "hero_image_present": "Opens with a large image",
    "persuasion_lever_count": "Persuasion techniques used",
    "rate_shown": "Shows a rate",
    "rate_value_pct": "Headline rate",
    "images_have_alt_text": "Images carry alt text",
    "is_bundled_offer": "Sells a bundle",
    "youth_student_targeting": "Targets students or young people",
    "expat_cross_border_targeting": "Targets expats",
    "institutional_trust_signal_present": "Invokes institutional trust",
    "mentions_loyalty_or_referral": "Mentions loyalty or referral",
    "fast_digital_onboarding_claim": "Promises fast digital sign-up",
    "senior_preretirement_targeting": "Targets pre-retirement",
    "first_time_investor_targeting": "Targets first-time investors",
    "has_comparison_table": "Includes a comparison table",
    "hidden_conditions_behind_free_claim": "“Free” with conditions attached",
    # sieg 19/09: AI Score axis labels (comparator/ai_score.py).
    "digital": "Digital",
    "trust": "Trust",
    "cross_sell": "Cross-sell",
    "personalisation": "Personalisation",
    "innovation": "Innovation",
    "simplicity": "Simplicity",
}

# sieg 19/09: display labels for the target_personas taxonomy (feature_dictionary.yaml).
PERSONA_LABELS = {
    "student": "Student",
    "family": "Family",
    "entrepreneur_self_employed": "Entrepreneur / self-employed",
    "expat": "Expat",
    "investor": "Investor",
    "retiree": "Retiree",
    "digital_nomad": "Digital nomad",
    "mass_market": "Mass market",
}

BANK_NAMES = {
    "ing": "ING", "kbc": "KBC", "belfius": "Belfius", "argenta": "Argenta",
    "crelan": "Crelan", "bnp_paribas_fortis": "BNP Paribas Fortis",
    "revolut": "Revolut", "n26": "N26", "bunq": "bunq", "cbc": "CBC",
}

FAMILY_NAMES = {
    "current_account_pack": "Current-account packs",
    "savings_account": "Savings accounts",
    "term_account": "Term accounts",
    "mortgage": "Mortgages",
    "investment": "Investment",
    "other": "Other",
}


# steph 17/09: a derived feature inherits the trust of what it is derived FROM.
# aida_coverage_score is computed, so the dictionary calls it "derived" - but it
# is computed from four rubric judgements, and it produced the most eye-catching
# number on the page (ING 0.00 against a peer mean of 2.42) with no caveat
# attached. See derive.py for the sources.
DERIVED_FROM_JUDGEMENT = {"aida_coverage_score", "persuasion_lever_count"}


def extraction_of(feature: str, fd) -> str:
    """How a reader should trust this number."""
    if feature in DERIVED_FROM_JUDGEMENT:
        return "rubric"
    return fd[feature].extraction if feature in fd else "automatic"


def label(feature: str) -> str:
    return LABELS.get(feature, feature.replace("_", " ").capitalize())


def bank_name(bank: str) -> str:
    return BANK_NAMES.get(bank, bank.replace("_", " ").title())


def _clean(value):
    """JSON cannot carry NaN, and a silent NaN renders as a confident 'null'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _rows(df: pd.DataFrame, columns: list[str]) -> list[dict]:
    return [{c: _clean(r[c]) for c in columns if c in df.columns} for _, r in df.iterrows()]


def build_report(dataset: Path, *, family: str | None, focus: str, top_n: int,
                 trends_dir: Path | None) -> tuple[dict, dict | None]:
    fd = load_dictionary()
    df, validation = read_dataset(dataset, fd, tier="core", strict=False)

    all_rows = df[df["data_source"] != "llm_generated"] if "data_source" in df else df
    usable = all_rows[all_rows.get("capture_quality", "ok") != "unusable"] \
        if "capture_quality" in all_rows.columns else all_rows

    options = family_options(usable)
    if family == "auto":
        comparable = options[options["comparable"]] if not options.empty else options
        family = comparable.iloc[0]["product_family"] if not comparable.empty else None

    compared, scope = scope_to_family(usable, family)

    positioning = positioning_axis(compared, fd, focus=focus)
    categories = compared.drop_duplicates("bank").set_index("bank")["bank_category"]
    deviations = ing_vs_peers(compared, fd, focus=focus) if positioning.has_focus else pd.DataFrame()
    separation = category_comparison(compared, fd)
    distances = similarity_matrix(compared, fd)
    clusters = cluster_banks(compared, fd, n_clusters=2)
    profiles = build_all(compared, fd)
    ai_scores = ai_score.score_all(compared)  # sieg 19/09
    cross_sell_scores = cross_sell.score_all(compared, fd)  # sieg 19/09
    cross_sell_matrix_df = cross_sell.cross_sell_matrix(compared, fd)  # sieg 19/09
    # sieg 19/09: optional, degrades to {"available": False} without NEWSAPI_KEY.
    reputation_dashboard = reputation.build_dashboard(
        [(b, bank_name(b)) for b in sorted(compared["bank"].unique())]
    )
    assessment = assess(all_rows, fd, focus=focus, scope=scope)

    stamps = pd.to_datetime(compared["captured_at"], errors="coerce", utc=True).dropna()

    reportable = deviations[deviations["reportable"]] if "reportable" in deviations.columns else deviations
    excluded_gaps = deviations[~deviations["reportable"]] if "reportable" in deviations.columns else pd.DataFrame()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": str(dataset),
        "scope": {
            "product_family": scope.family,
            "product_family_label": FAMILY_NAMES.get(scope.family, scope.family or "All families"),
            "pages": int(len(compared)),
            "banks": [bank_name(b) for b in scope.banks],
            "traditional": [bank_name(b) for b in scope.traditional],
            "challenger": [bank_name(b) for b in scope.challenger],
            "excluded": [
                {"bank": bank_name(b),
                 "reason": "has a usable capture, but no page in this product family"}
                for b in scope.dropped_banks
            ],
            "uncollectable": [
                {"bank": bank_name(r["bank"]), "reason": str(r.get("capture_quality_note", ""))}
                for _, r in all_rows[all_rows.get("capture_quality", "ok") == "unusable"].iterrows()
            ] if "capture_quality" in all_rows.columns else [],
            "languages": sorted(compared["language"].dropna().unique().tolist()),
            "captured_from": stamps.min().isoformat() if not stamps.empty else None,
            "captured_to": stamps.max().isoformat() if not stamps.empty else None,
            "total_collected": int(len(all_rows)),
            "n_features": int(positioning.n_features),
        },
        "headline": {
            "focus": bank_name(focus),
            "score": round(positioning.focus_score, 3) if positioning.has_focus else None,
            "verdict": positioning.verdict if positioning.has_focus else None,
            "has_focus": bool(positioning.has_focus),
        },
        "positioning": [
            {"bank": bank_name(b), "key": b,
             "category": categories.get(b, "traditional"),
             "score": round(float(s), 3),
             "isFocus": b == focus}
            for b, s in positioning.scores.items()
        ],
        "peerGaps": [
            {"feature": r["feature"], "label": label(r["feature"]),
             "dimension": r["dimension"],
             "extraction": extraction_of(r["feature"], fd),
             "focusValue": _clean(r.get(f"{focus}_value")),
             "peerMean": _clean(r.get("peer_mean")),
             "gapSd": round(float(r["gap_sd"]), 2),
             "direction": "above" if r["gap_sd"] > 0 else "below"}
            for _, r in reportable.head(top_n).iterrows()
        ],
        "excludedGaps": [
            {"label": label(r["feature"]), "note": r.get("note", "")}
            for _, r in excluded_gaps.iterrows()
        ],
        "separation": [
            {"feature": r["feature"], "label": label(r["feature"]),
             "extraction": extraction_of(r["feature"], fd),
             "traditional": _clean(r["traditional_mean"]),
             "challenger": _clean(r["challenger_mean"]),
             "effect": round(float(r["effect_size_d"]), 2),
             "higherAt": "challenger" if r["effect_size_d"] > 0 else "traditional"}
            for _, r in separation.head(top_n).iterrows()
        ],
        "banks": [],
        # sieg 19/09: legend for the AI Score radar - one entry per axis in comparator/ai_score.py.
        "aiScoreAxes": [{"key": a, "label": label(a)} for a in ai_score.AXES],
        # sieg 19/09: the cross-sell "graph", flattened to a co-occurrence matrix - see cross_sell.py.
        "crossSellMatrix": {
            "products": [FAMILY_NAMES.get(p, p) for p in cross_sell_matrix_df.index],
            "matrix": cross_sell_matrix_df.to_numpy().tolist(),
            "mostAssociated": [
                {"from": FAMILY_NAMES.get(a, a), "to": FAMILY_NAMES.get(b, b), "count": n}
                for a, b, n in cross_sell.most_associated(cross_sell_matrix_df, n=5)
            ],
            # sieg 19/09: "confirmed never" (row family has enough pages to trust
            # the zero) vs "insufficient_data" (too few pages, a 0 is a data gap,
            # not a finding) - see cross_sell.py::never_paired().
            "neverPaired": {
                kind: [{"from": FAMILY_NAMES.get(a, a), "to": FAMILY_NAMES.get(b, b)} for a, b in pairs]
                for kind, pairs in cross_sell.never_paired(
                    cross_sell_matrix_df, compared.groupby("product_family").size()
                ).items()
            },
        },
        "similarity": {
            "banks": [bank_name(b) for b in distances.index],
            "matrix": [[round(float(v), 2) for v in row] for row in distances.to_numpy()],
        },
        "clusters": [
            {"cluster": int(c), "banks": [bank_name(b) for b in clusters[clusters == c].index]}
            for c in sorted(clusters.unique())
        ],
        "nearestToFocus": (
            [{"bank": bank_name(b), "distance": round(float(d), 2)}
             for b, d in nearest_neighbours(compared, fd, focus=focus).items()]
            if positioning.has_focus else []
        ),
        "deckClaims": _rows(check_deck_claims(compared, fd),
                            ["id", "bank", "claim", "verdict", "evidence"]),
        "limitations": {
            "blocking": assessment["blocking"],
            "material": assessment["material"],
            "standing": assessment["standing"],
        },
        "validation": {
            "ok": validation.ok,
            "warnings": validation.warnings[:6],
        },
        "generated": [],
        "trends": None,
        "reputation": reputation_dashboard,  # sieg 19/09
    }

    for bank, profile in profiles.items():
        report["banks"].append({
            "key": bank,
            "name": bank_name(bank),
            "category": profile["identity"]["category"],
            "pages": profile["identity"]["pages_analysed"],
            "signature": [
                {"label": label(name), "sd": round(float(z), 1),
                 "direction": "above" if z > 0 else "below"}
                for name, z in profile["signature"]
            ],
            "tone": {label(k): _clean(v) for k, v in profile["tone"].items()},
            "imagery": {label(k): _clean(v) for k, v in profile["imagery"].items()},
            "layout": {label(k): _clean(v) for k, v in profile["layout"].items()},
            "valueProposition": {label(k): _clean(v) for k, v in profile["value_proposition"].items()},
            "palette": {
                "dominant": profile["palette"].get("dominant_colour"),
                "brandShare": _clean(profile["palette"].get("brand_colour_share")),
                "backgroundLuminance": _clean(profile["palette"].get("background_luminance")),
            },
            "marketing": {label(k): _clean(v) for k, v in profile["marketing_principles"].items()},
            # sieg 19/09: personas + AI Score, additive - see comparator/profiles.py and ai_score.py.
            "personas": [
                {"persona": p["persona"], "label": PERSONA_LABELS.get(p["persona"], p["persona"]), "share": round(p["share"], 3)}
                for p in profile["personas"]
            ],
            "aiScore": ai_scores.get(bank, {}),
            "crossSellScore": cross_sell_scores.get(bank),
        })

    generated_dir = Path("outputs/generated")
    for variant in ("on_brand", "challenger_style"):
        campaign_path = generated_dir / f"{variant}.json"
        scorecard_path = generated_dir / f"{variant}_scorecard.csv"
        if not campaign_path.is_file():
            continue
        campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
        scorecard = []
        if scorecard_path.is_file():
            sc = pd.read_csv(scorecard_path)
            scorecard = [
                {"label": label(r["feature"]), "target": r["target"],
                 "actual": _clean(r["actual"]), "result": r["result"]}
                for _, r in sc.iterrows()
            ]
        hits = [s for s in scorecard if s["result"] == "hit"]
        measured = [s for s in scorecard if s["result"] in ("hit", "miss")]
        report["generated"].append({
            "variant": variant,
            "title": "On brand" if variant == "on_brand" else "Challenger style",
            "headline": campaign.get("headline"),
            "subheading": campaign.get("subheading"),
            "body": campaign.get("body_paragraphs", []),
            "cta": campaign.get("cta_label"),
            "additionalCtas": campaign.get("additional_cta_labels", []),
            "layout": campaign.get("layout_archetype"),
            "background": campaign.get("background_style"),
            "accent": campaign.get("accent_colour_hex"),
            "imageBriefs": campaign.get("image_briefs", []),
            "disclaimer": campaign.get("disclaimer_placeholder"),
            "levers": campaign.get("persuasion_levers_used", []),
            "model": campaign.get("_model"),
            "promptHash": campaign.get("_prompt_sha256_16"),
            "scorecard": scorecard,
            "hitRate": round(len(hits) / len(measured), 2) if measured else None,
        })

    context = build_trends_dashboard(compared, trends_dir)
    if context:
        series_points = sum(
            len(t["points"]) for b in context["banks"] for p in b["products"] for t in p["terms"]
        )
        anomaly_count = sum(
            len(t["anomalies"]) for b in context["banks"] for p in b["products"] for t in p["terms"]
        )
        report["trends"] = {
            "available": True,
            "source": context["source"],
            "window": context["window"],
            "covered": context["coverage"]["covered"],
            "uncovered": context["coverage"]["uncovered"],
            "n_series": series_points,
            "n_anomalies": anomaly_count,
            "n_campaigns": context["campaigns"]["catalogued"],
            "data_url": "trends.json",
        }

    return report, context


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--product-family", default="auto")
    parser.add_argument("--focus", default="ing")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--trends-dir", type=Path, default=None)
    args = parser.parse_args()

    report, trends = build_report(args.dataset, family=args.product_family, focus=args.focus,
                                  top_n=args.top_n, trends_dir=args.trends_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    trends_path = args.out.parent / "trends.json"
    if trends:
        trends_path.write_text(json.dumps(trends, ensure_ascii=False), encoding="utf-8")

    scope = report["scope"]
    print(f"wrote {args.out}")
    print(f"  scope   : {scope['product_family_label']} — {scope['pages']} pages, "
          f"{len(scope['banks'])} banks, {scope['n_features']} features")
    print(f"  excluded: {[e['bank'] for e in scope['excluded']] or 'none'}")
    print(f"  headline: {report['headline']['focus']} {report['headline']['score']} "
          f"({report['headline']['verdict']})")
    print(f"  generated variants: {len(report['generated'])}")
    t = report.get("trends")
    if t:
        print(f"  trends  : {t['n_series']} weekly points, {t['n_anomalies']} anomalies, "
              f"{t['n_campaigns']} campaigns -> {trends_path.name}")
    else:
        print("  trends  : Dan's export not present - Trends tab will show an empty state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
