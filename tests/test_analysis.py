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
    # sieg 14/09: nearest_neighbours used to be the only sibling function
    # without a tier passthrough - this is a regression guard, not a claim
    # about which neighbours a restricted tier should return.
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


def test_deck_claims_lowest_traditional_does_not_crash_on_empty_subset(df, fd):
    # sieg 14/09: H2 (KBC) used to call .idxmin() on a subset that could be
    # empty (e.g. no bank tagged "traditional" left in the data), which raises
    # instead of reporting "not testable" like every other untestable claim.
    no_traditional = df.copy()
    no_traditional["bank_category"] = "challenger"
    claims = check_deck_claims(no_traditional, fd)
    h2 = claims.loc[claims["id"] == "H2"].iloc[0]
    assert h2["verdict"] == "not testable"


# sieg 15/09: new function, new tests - BO-04 (recurring market-wide patterns)
# had no function behind it before this.
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


# sieg 15/09: new function, new tests - FR-10 (M priority) had no function
# behind it before this.
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


def test_profile_for_unknown_bank_fails_loudly(df, fd):
    with pytest.raises(ValueError, match="no rows for bank"):
        build_profile(df, "not_a_bank", fd)


# --- feature accounting (steph 15/09, after Sieg's "50 features... and with 97?") ---
def test_accounting_adds_up_to_the_whole_dictionary(df, fd):
    """Every feature must land in exactly one bucket, or the explanation is wrong."""
    from comparator.analysis import feature_accounting

    a = feature_accounting(df, fd)
    buckets = (a["provenance"] + a["free_text"] + a["band_redundant"]
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
    """Sieg's contribution must not be quietly sitting the analysis out."""
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
