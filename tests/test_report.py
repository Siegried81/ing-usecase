"""Tests for the generated chart companion (steph 15/09).

The point of generating this file rather than writing it is that the prose
cannot drift away from the figures. These tests check that it doesn't.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator.analysis import (  # noqa: E402
    category_comparison,
    check_deck_claims,
    cluster_banks,
    ing_vs_peers,
    positioning_axis,
    similarity_matrix,
)
from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.report import build_chart_report  # noqa: E402


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


@pytest.fixture(scope="module")
def df(fd):
    return build_fixture(fd)


@pytest.fixture(scope="module")
def report(df, fd):
    categories = df.drop_duplicates("bank").set_index("bank")["bank_category"]
    return build_chart_report(
        positioning=positioning_axis(df, fd),
        categories=categories,
        deviations=ing_vs_peers(df, fd),
        comparison=category_comparison(df, fd),
        distances=similarity_matrix(df, fd),
        clusters=cluster_banks(df, fd),
        claims=check_deck_claims(df, fd),
        dataset_path="data/fixtures/synthetic_sample.csv",
        n_pages=len(df),
        n_banks=int(df["bank"].nunique()),
        synthetic=True,
    )


def test_every_chart_is_embedded(report):
    for image in ("01_positioning.png", "02_ing_vs_peers.png",
                  "03_category_separation.png", "04_similarity.png"):
        assert f"]({image})" in report, f"{image} is not referenced"


def test_image_paths_are_relative_to_the_outputs_folder(report):
    """The md sits next to the PNGs, so an absolute or nested path would break it."""
    assert "](outputs/" not in report
    assert "](/" not in report


def test_each_chart_says_what_it_measures_and_what_it_cannot(report):
    assert report.count("**What it measures.**") == 4
    assert report.count("**What it cannot tell you.**") == 4


def test_synthetic_data_is_flagged_loudly(report):
    assert "not findings" in report.lower()


def test_no_synthetic_warning_when_data_is_real(df, fd):
    categories = df.drop_duplicates("bank").set_index("bank")["bank_category"]
    text = build_chart_report(
        positioning=positioning_axis(df, fd), categories=categories,
        deviations=ing_vs_peers(df, fd), comparison=category_comparison(df, fd),
        distances=similarity_matrix(df, fd), clusters=cluster_banks(df, fd),
        synthetic=False,
    )
    assert "These numbers are not findings" not in text


def test_peer_and_group_counts_are_derived_not_hardcoded(df, fd):
    """A hardcoded count is exactly the drift this file exists to prevent."""
    subset = df[df["bank"].isin(["ing", "kbc", "revolut", "n26"])]
    categories = subset.drop_duplicates("bank").set_index("bank")["bank_category"]
    text = build_chart_report(
        positioning=positioning_axis(subset, fd), categories=categories,
        deviations=ing_vs_peers(subset, fd), comparison=category_comparison(subset, fd),
        distances=similarity_matrix(subset, fd), clusters=cluster_banks(subset, fd),
        n_pages=len(subset), n_banks=4, synthetic=True,
    )
    assert "With 3 peers" in text
    assert "With 2 bank(s) on one side and 2 on the other" in text


def test_the_focus_bank_position_matches_the_computed_one(df, fd, report):
    expected = positioning_axis(df, fd).focus_score
    assert f"**{expected:.2f}**" in report


def test_claims_appendix_warns_about_circularity_on_fixture_data(report):
    assert "Circular on fixture data" in report


def test_no_significance_language_anywhere(report):
    """The project never claims significance - the companion must not either."""
    for banned in ("p-value of", "statistically significant", "p <"):
        assert banned not in report.lower()
