"""Tests for the comparison logic.

These check that the analysis says the right thing about data whose answer is
known in advance - not that the fixture's numbers are true.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.analysis import (  # noqa: E402
    bank_vectors,
    category_comparison,
    check_deck_claims,
    cluster_banks,
    comparable_features,
    ing_vs_peers,
    nearest_neighbours,
    positioning_axis,
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
