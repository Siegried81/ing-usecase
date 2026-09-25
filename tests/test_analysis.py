"""Tests for the comparison logic.

These check that the analysis says the right thing about data whose answer is
known in advance - not that the fixture's numbers are true.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.analysis import (  # noqa: E402
    bank_vectors,
    category_comparison,
    check_deck_claims,
    cluster_banks,
    comparable_features,
    ing_vs_peers,
    insight_candidates,
    language_excluded_features,  # Audit fix, comparability enforcement
    nearest_neighbours,
    positioning_axis,
    recurring_patterns,
    similarity_matrix,
)
from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.profiles import build_all, build_profile, render_markdown  # noqa: E402


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


@pytest.fixture(scope="module")
def df(fd):
    return build_fixture(fd)


def test_provenance_never_enters_a_comparison(df, fd):
    """Page identity must not be treated as a campaign characteristic."""
    cols = comparable_features(fd, df)
    assert cols
    assert all(fd[c].dimension != "provenance" for c in cols)


def test_bank_vectors_are_one_row_per_bank(df, fd):
    vectors = bank_vectors(df, fd)
    assert len(vectors) == df["bank"].nunique()


# comparable_features() must honour `comparability`: within_language features
# (word_count, readability_score, ...) cannot be compared raw across banks
# captured in different languages. These tests pin that.
def test_within_language_features_stay_in_when_one_language(df, fd):
    """Regression: single-language data (the fixture default) is unaffected."""
    assert df["language"].nunique() == 1
    assert language_excluded_features(fd, df) == []
    cols = comparable_features(fd, df)
    assert "word_count" in cols
    assert "readability_score" in cols


def test_within_language_features_are_excluded_when_languages_mix(df, fd):
    """KBC's real captures already mix fr/nl (scripts/collection_targets.yaml) -
    this is the scenario the audit found silently mis-compared."""
    mixed = df.copy()
    half = mixed.index[: len(mixed) // 2]
    mixed.loc[half, "language"] = "fr"
    mixed.loc[mixed.index.difference(half), "language"] = "nl"

    excluded = language_excluded_features(fd, mixed)
    assert "word_count" in excluded
    assert "readability_score" in excluded
    assert all(fd[name].comparability == "within_language" for name in excluded)

    cols = comparable_features(fd, mixed)
    assert "word_count" not in cols
    assert "readability_score" not in cols
    # cross_language features are still compared - the fix is scoped, not a blanket drop.
    assert any(fd[c].comparability == "cross_language" for c in cols)


def test_accounting_reports_the_language_exclusion(fd):
    from comparator.analysis import feature_accounting, render_accounting
    from comparator.fixtures import build_fixture

    mixed = build_fixture(fd)
    half = mixed.index[: len(mixed) // 2]
    mixed.loc[half, "language"] = "fr"
    mixed.loc[mixed.index.difference(half), "language"] = "nl"

    accounting = feature_accounting(mixed, fd)
    assert "word_count" in accounting["language_excluded"]
    text = render_accounting(accounting)
    assert "mixed languages present" in text


# band_redundant_features() judges on "does the raw feature actually enter the
# comparison", not "is the raw column present in df". Otherwise word_count_band
# stays hidden as redundant even once word_count itself is excluded for mixing
# languages - and the band is precisely the cross-language substitute for it.
def test_band_becomes_available_once_its_raw_feature_is_language_excluded(fd):
    from comparator.analysis import band_redundant_features, encodable_categoricals
    from comparator.fixtures import build_fixture

    mixed = build_fixture(fd)
    half = mixed.index[: len(mixed) // 2]
    mixed.loc[half, "language"] = "fr"
    mixed.loc[mixed.index.difference(half), "language"] = "nl"

    assert "word_count_band" not in band_redundant_features(fd, mixed)
    assert "word_count_band" in encodable_categoricals(fd, mixed)


def test_positioning_puts_the_groups_on_opposite_ends(df, fd):
    """The axis is defined by the two centroids, so the groups must separate."""
    pos = positioning_axis(df, fd)
    categories = df.drop_duplicates("bank").set_index("bank")["bank_category"]
    traditional = pos.scores[categories[categories == "traditional"].index]
    challenger = pos.scores[categories[categories == "challenger"].index]
    assert traditional.max() < challenger.min()


def test_positioning_verdict_is_reported(df, fd):
    pos = positioning_axis(df, fd)
    assert pos.focus == "ing"
    assert isinstance(pos.verdict, str) and pos.verdict


def test_positioning_requires_the_focus_bank(df, fd):
    with pytest.raises(ValueError, match="cannot be positioned"):
        ing_vs_peers(df[df["bank"] != "ing"], fd)


def test_similarity_matrix_is_a_valid_distance_matrix(df, fd):
    dist = similarity_matrix(df, fd)
    assert (dist.to_numpy().diagonal() < 1e-9).all()          # self-distance is zero
    assert (dist.to_numpy() == dist.to_numpy().T).all()        # symmetric
    assert (dist.to_numpy() >= 0).all()


def test_clustering_separates_the_two_business_models(df, fd):
    clusters = cluster_banks(df, fd, n_clusters=2)
    categories = df.drop_duplicates("bank").set_index("bank")["bank_category"]
    by_category = {c: set(clusters[categories[categories == c].index]) for c in ("traditional", "challenger")}
    assert not by_category["traditional"] & by_category["challenger"]


def test_nearest_neighbours_excludes_self(df, fd):
    neighbours = nearest_neighbours(df, fd, focus="ing", k=3)
    assert "ing" not in neighbours.index
    assert len(neighbours) == 3


def test_nearest_neighbours_accepts_tier(df, fd):
    # A guard that nearest_neighbours passes `tier` through like its sibling
    # functions - not a claim about which neighbours a restricted tier returns.
    neighbours = nearest_neighbours(df, fd, focus="ing", k=3, tier="core")
    assert "ing" not in neighbours.index
    assert len(neighbours) == 3


def test_deviations_are_sorted_by_absolute_gap(df, fd):
    gaps = ing_vs_peers(df, fd)["gap_sd"].abs().tolist()
    assert gaps == sorted(gaps, reverse=True)


def test_category_comparison_reports_group_sizes(df, fd):
    comparison = category_comparison(df, fd)
    assert (comparison["n_traditional"] > 1).all()
    assert (comparison["n_challenger"] > 1).all()


def test_deck_claims_all_return_a_verdict(df, fd):
    claims = check_deck_claims(df, fd)
    assert len(claims) == 5
    assert claims["verdict"].isin({"supported", "not supported", "not testable"}).all()


# H1/H2/H5 must test word_count_band, not raw word_count:
# language_excluded_features() drops the raw feature ENTIRELY the moment >1
# language is in scope, which is the real dataset as soon as English or Dutch
# pages are in it. The band (fixed universal thresholds, cross_language)
# survives that drop.
def test_deck_claims_word_count_claims_survive_mixed_language_scope(fd):
    mixed = pd.concat([
        build_fixture(fd, banks=["belfius", "kbc", "revolut"], language="fr"),
        build_fixture(fd, banks=["ing"], language="en", seed=20260915),
    ], ignore_index=True)
    claims = check_deck_claims(mixed, fd)
    verdicts = claims.set_index("id")["verdict"]
    for claim_id in ("H1", "H2", "H5"):
        assert verdicts[claim_id] in ("supported", "not supported"), (
            f"{claim_id} should be testable via word_count_band even with mixed languages, "
            f"got {verdicts[claim_id]!r}"
        )


def test_deck_claims_lowest_traditional_does_not_crash_on_empty_subset(df, fd):
    # H2 (KBC) calls .idxmin() on a subset that can be empty - no bank tagged
    # "traditional" left in the data - which raises instead of reporting
    # "not testable" like every other untestable claim.
    no_traditional = df.copy()
    no_traditional["bank_category"] = "challenger"
    claims = check_deck_claims(no_traditional, fd)
    h2 = claims.loc[claims["id"] == "H2"].iloc[0]
    assert h2["verdict"] == "not testable"


# BO-04: recurring market-wide patterns.
def test_recurring_patterns_are_sorted_and_above_the_threshold(df, fd):
    patterns = recurring_patterns(df, fd, min_abs_corr=0.5)
    if patterns.empty:
        return
    assert (patterns["correlation"].abs() >= 0.5).all()
    corrs = patterns["correlation"].abs().tolist()
    assert corrs == sorted(corrs, reverse=True)


def test_recurring_patterns_never_pairs_a_feature_with_itself(df, fd):
    patterns = recurring_patterns(df, fd, min_abs_corr=0.0)
    assert (patterns["feature_a"] != patterns["feature_b"]).all()


def test_recurring_patterns_does_not_list_a_pair_twice(df, fd):
    patterns = recurring_patterns(df, fd, min_abs_corr=0.0)
    pairs = {frozenset((a, b)) for a, b in zip(patterns["feature_a"], patterns["feature_b"])}
    assert len(pairs) == len(patterns)


# FR-10 (M priority).
def test_insight_candidates_are_sorted_and_above_the_threshold(df, fd):
    candidates = insight_candidates(df, fd, min_gap_sd=0.5)
    assert (candidates["gap_sd"].abs() >= 0.5).all()
    gaps = candidates["gap_sd"].abs().tolist()
    assert gaps == sorted(gaps, reverse=True)


def test_insight_candidates_respects_top_n(df, fd):
    candidates = insight_candidates(df, fd, min_gap_sd=0.0, top_n=2)
    assert len(candidates) <= 2


def test_insight_candidates_cite_a_source_page(df, fd):
    candidates = insight_candidates(df, fd, min_gap_sd=0.5)
    assert not candidates.empty, "fixture should produce at least one candidate above 0.5 SD"
    assert all(candidates["example_page_ids"].apply(len) > 0)
    assert all(pid in set(df.loc[df["bank"] == "ing", "page_id"]) for ids in candidates["example_page_ids"] for pid in ids)


def test_every_profile_has_the_same_fields(df, fd):
    profiles = build_all(df, fd)
    shapes = {bank: tuple(sorted(p)) for bank, p in profiles.items()}
    assert len(set(shapes.values())) == 1, "profile cards must be identical in shape to be comparable"


def test_profile_renders_to_markdown(df, fd):
    text = render_markdown(build_profile(df, "ing", fd), fd)
    assert text.startswith("### ing")
    assert "Signature:" in text


# Persona distribution - build_fixture()'s "ing" archetype targets
# family/expat/mass_market (2 pages, both carry all three), so each should come
# back at a 100% share and nothing else should appear.
def test_profile_persona_distribution_matches_the_fixture(df, fd):
    profile = build_profile(df, "ing", fd)
    personas = {p["persona"]: p["share"] for p in profile["personas"]}
    assert personas == {"family": 1.0, "expat": 1.0, "mass_market": 1.0}
    assert all(0 <= share <= 1 for share in personas.values())


def test_profile_renders_persona_distribution_to_markdown(df, fd):
    text = render_markdown(build_profile(df, "ing", fd), fd)
    assert "| personas |" in text
    assert "family 100%" in text


def test_profile_for_unknown_bank_fails_loudly(df, fd):
    with pytest.raises(ValueError, match="no rows for bank"):
        build_profile(df, "not_a_bank", fd)


# build_profile() must not compute within_language means (word_count,
# second_person_ratio) straight from a bank's own rows, bypassing
# comparable_features(). KBC's real captures mix fr/nl pages
# (scripts/collection_targets.yaml), which is the scenario these pin.
def test_single_language_bank_profile_is_unaffected(df, fd):
    """Regression: the fixture default (one language per bank) must not change."""
    profile = build_profile(df, "ing", fd)
    assert profile["identity"]["mixed_language"] is False
    assert profile["tone"]["word_count"] is not None


def test_mixed_language_bank_profile_nulls_the_within_language_tone_fields():
    fd = load_dictionary()
    df = build_fixture(fd)
    ing_rows = df.index[df["bank"] == "ing"]
    half = ing_rows[: len(ing_rows) // 2]
    df.loc[half, "language"] = "fr"
    df.loc[ing_rows.difference(half), "language"] = "nl"

    profile = build_profile(df, "ing", fd)
    assert profile["identity"]["mixed_language"] is True
    assert profile["tone"]["word_count"] is None
    assert profile["tone"]["second_person_ratio"] is None
    # cross_language tone fields are still reported - the fix is scoped.
    assert profile["tone"]["formality_score"] is not None


# --- feature accounting (After the "50 features... and with 97?") ---
def test_accounting_adds_up_to_the_whole_dictionary(df, fd):
    """Every feature must land in exactly one bucket, or the explanation is wrong."""
    from comparator.analysis import feature_accounting

    a = feature_accounting(df, fd)
    # Every bucket feature_accounting() reports, including the two that are
    # empty on single-language, nothing-withdrawn data - leaving one out here
    # would let a real exclusion go uncounted the moment it is not empty.
    buckets = (a["provenance"] + a["free_text"] + a["band_redundant"]
               + a["language_excluded"] + a["capture_invalid"]
               + a["categorical"] + a["incomplete"] + a["constant"] + a["used"])
    assert len(buckets) == len(set(buckets)), "a feature is counted in two buckets"
    assert len(buckets) == a["dictionary_total"] == len(fd)


def test_accounting_matches_what_positioning_actually_used(df, fd):
    from comparator.analysis import feature_accounting

    assert feature_accounting(df, fd)["n_used"] == positioning_axis(df, fd).n_features


def test_bands_are_excluded_as_redundant_not_silently_lost(df, fd):
    from comparator.analysis import band_redundant_features, feature_accounting

    bands = band_redundant_features(fd, df)
    assert "word_count_band" in bands, "its raw word_count is already in the matrix"
    assert set(bands) <= set(feature_accounting(df, fd)["band_redundant"])


def test_free_text_never_enters_a_distance(df, fd):
    from comparator.analysis import feature_accounting

    assert "meta_title" in feature_accounting(df, fd)["free_text"]


def test_banking_domain_features_do_reach_the_comparison(df, fd):
    """that contribution must not be quietly sitting the analysis out."""
    from comparator.analysis import feature_accounting

    used = set(feature_accounting(df, fd)["used"])
    banking = {f.name for f in fd.select(dimension="banking_domain")}
    assert len(used & banking) >= 10, "most banking-domain features should be in play"


def test_including_categoricals_adds_columns_without_changing_the_verdict(df, fd):
    """The robustness check: the answer must not hinge on the encoding choice."""
    plain = positioning_axis(df, fd)
    encoded = positioning_axis(df, fd, include_categorical=True)
    assert encoded.n_features > plain.n_features
    assert encoded.verdict == plain.verdict


def test_a_categorical_weighs_the_same_as_one_number(df, fd):
    """A k-value categorical becomes k unit-variance columns after standardising,
    so without correction it would outvote k numeric features. 19 categoricals
    became 55 columns here and outweighed all 50 numerics - hence the 1/sqrt(k)
    correction, which only works AFTER standardisation."""
    from comparator.analysis import comparison_matrix, encodable_categoricals

    z = comparison_matrix(df, fd, include_categorical=True)
    categorical = set(encodable_categoricals(fd, df))

    numeric_cols = [c for c in z.columns if c.split("=")[0] not in categorical]
    blocks: dict[str, list[str]] = {}
    for column in z.columns:
        stem = column.split("=")[0]
        if stem in categorical:
            blocks.setdefault(stem, []).append(column)

    per_numeric = float((z[numeric_cols] ** 2).to_numpy().sum()) / len(numeric_cols)
    per_categorical = sum(float((z[cols] ** 2).to_numpy().sum()) for cols in blocks.values()) / len(blocks)
    assert per_categorical == pytest.approx(per_numeric, rel=0.02)


def test_pre_standardisation_scaling_would_not_have_worked(df, fd):
    """Guards the reasoning: z-scoring erases any constant applied beforehand."""
    from comparator.analysis import _one_hot, encodable_categoricals, standardise

    raw = _one_hot(df, fd, encodable_categoricals(fd, df))
    scaled = raw / 7.0  # any constant at all
    pd.testing.assert_frame_equal(standardise(raw), standardise(scaled))


def test_both_distance_consumers_share_one_matrix(df, fd):
    """positioning_axis and similarity_matrix built this inline, which is how the
    weighting bug survived in one and not the other."""
    from comparator.analysis import comparison_matrix

    z = comparison_matrix(df, fd)
    assert positioning_axis(df, fd).n_features == z.shape[1]
    assert similarity_matrix(df, fd).shape[0] == z.shape[0]


def test_render_accounting_names_a_reason_for_every_reduction(df, fd):
    from comparator.analysis import feature_accounting, render_accounting

    text = render_accounting(feature_accounting(df, fd))
    for reason in ("identify a page", "double-count", "carries no signal"):
        assert reason in text


# --- the focus bank can legitimately be absent ------------------
# The first live collection returned ING as an unrendered shell, so the bank the
# project exists to position was missing from its own dataset. That surfaced as
# KeyError: 'ing' from inside pandas, in three different places.
def _without_ing(df):
    return df[df["bank"] != "ing"]


def test_positioning_reports_a_missing_focus_instead_of_crashing(df, fd):
    pos = positioning_axis(_without_ing(df), fd, focus="ing")
    assert pos.has_focus is False
    assert "ing" not in pos.scores.index


def test_asking_for_the_score_of_an_absent_focus_says_why(df, fd):
    pos = positioning_axis(_without_ing(df), fd, focus="ing")
    with pytest.raises(ValueError, match="BO-01 and BO-02 are unanswerable"):
        _ = pos.focus_score


def test_the_rest_of_the_market_is_still_positioned(df, fd):
    """Losing ING must not cost us the analysis of everyone else."""
    pos = positioning_axis(_without_ing(df), fd, focus="ing")
    assert len(pos.scores) == df["bank"].nunique() - 1
    assert pos.n_features > 0


def test_nearest_neighbours_names_the_missing_bank(df, fd):
    with pytest.raises(ValueError, match="check capture_quality for ing"):
        nearest_neighbours(_without_ing(df), fd, focus="ing")


def test_has_focus_is_true_in_the_normal_case(df, fd):
    assert positioning_axis(df, fd, focus="ing").has_focus is True


# --- a gap in peer SDs is only meaningful if the peers vary -----
# brand_colour_share came back [0.0, 0.014, nan, 0.0] on the first real run:
# ING at 0.228 scored +33.8 SD and topped the headline chart. That was a peer
# spread of 0.007, not a fact about ING - the real story was that colour
# extraction had failed for most banks.
def test_a_gap_against_near_identical_peers_is_not_reportable(df, fd):
    broken = df.copy()
    broken["brand_colour_share"] = 0.0
    broken.loc[broken["bank"] == "ing", "brand_colour_share"] = 0.228

    row = ing_vs_peers(broken, fd).set_index("feature").loc["brand_colour_share"]
    assert not row["reportable"]          # pandas stores this as numpy bool_
    assert row["note"]


def test_unreportable_gaps_are_kept_with_a_reason_not_dropped(df, fd):
    """'Extraction failed for four banks' is itself worth seeing."""
    broken = df.copy()
    broken["brand_colour_share"] = 0.0
    broken.loc[broken["bank"] == "ing", "brand_colour_share"] = 0.228
    assert "brand_colour_share" in set(ing_vs_peers(broken, fd)["feature"])


def test_reportable_gaps_are_ranked_above_unreportable_ones(df, fd):
    broken = df.copy()
    broken["brand_colour_share"] = 0.0
    broken.loc[broken["bank"] == "ing", "brand_colour_share"] = 0.228

    out = ing_vs_peers(broken, fd)
    flags = out["reportable"].tolist()
    assert flags == sorted(flags, reverse=True), "reportable gaps must come first"


def test_a_feature_only_one_peer_has_is_not_reportable(df, fd):
    thin = df.copy()
    thin["cta_contrast_ratio"] = float("nan")
    thin.loc[thin["bank"] == "ing", "cta_contrast_ratio"] = 5.0
    thin.loc[thin["bank"] == "kbc", "cta_contrast_ratio"] = 4.0

    out = ing_vs_peers(thin, fd).set_index("feature")
    if "cta_contrast_ratio" in out.index:
        assert not out.loc["cta_contrast_ratio", "reportable"]


def test_a_normal_gap_stays_reportable(df, fd):
    out = ing_vs_peers(df, fd)
    assert out["reportable"].any(), "the ordinary case must still produce findings"


# A feature whose rule does not reproduce what it claims to measure describes
# the rule, not the bank, so it must leave the comparison AND be reported
# leaving it - a silent drop is how a withdrawn number creeps back into a chart.
def test_capture_invalid_features_are_excluded_from_the_comparison(df, fd):
    from comparator.analysis import CAPTURE_INVALID_FEATURES, comparable_features

    used = comparable_features(fd, df)
    for name in CAPTURE_INVALID_FEATURES:
        if name in df.columns:
            assert name not in used, f"{name} is withdrawn and must not be compared"


def test_capture_invalid_features_are_reported_not_silently_dropped(df, fd):
    from comparator.analysis import (
        CAPTURE_INVALID_FEATURES,
        feature_accounting,
        render_accounting,
    )

    accounting = feature_accounting(df, fd)
    present = sorted(n for n in CAPTURE_INVALID_FEATURES if n in fd and n in df.columns)
    assert accounting["capture_invalid"] == present
    if present:
        assert "withdrawn, measurement not the page" in render_accounting(accounting)


# --- verdicts a measure cannot support ------------------------------------
def test_a_claim_on_a_column_with_no_variation_is_not_testable(df, fd):
    # The real dataset: word_count_band is "long" for every bank, so no bank
    # can be "the most verbose" - that is untestable, not "not supported".
    flat = df.copy()
    flat["word_count_band"] = "long"
    verdicts = check_deck_claims(flat, fd).set_index("id")
    for claim_id in ("H1", "H2", "H5"):
        assert verdicts.loc[claim_id, "verdict"] == "not testable"
        assert "same word_count_band" in verdicts.loc[claim_id, "evidence"]


def test_a_claim_on_a_withdrawn_feature_says_withdrawn_not_absent(df, fd):
    h3 = check_deck_claims(df, fd).set_index("id").loc["H3"]
    assert h3["verdict"] == "not testable"
    assert "withdrawn" in h3["evidence"]


def test_insight_candidates_never_argue_from_an_unreportable_gap(df, fd):
    candidates = insight_candidates(df, fd, min_gap_sd=0.0, top_n=50)
    assert candidates["reportable"].all()


def test_positioning_refuses_a_split_with_an_empty_side(df, fd):
    one_sided = df.copy()
    one_sided["bank_category"] = "traditional"
    with pytest.raises(ValueError, match="no bank"):
        positioning_axis(one_sided, fd)


def test_category_comparison_is_empty_not_a_crash_when_a_side_is_missing(df, fd):
    one_sided = df.copy()
    one_sided["bank_category"] = "traditional"
    out = category_comparison(one_sided, fd)
    assert out.empty and "effect_size_d" in out.columns
