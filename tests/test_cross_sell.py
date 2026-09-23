"""Tests for the cross-sell score and product co-occurrence matrix."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import cross_sell  # noqa: E402
from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.schema import format_list  # noqa: E402


@pytest.fixture(scope="module")
def fd():
    return load_dictionary()


@pytest.fixture(scope="module")
def df(fd):
    return build_fixture(fd)


def test_score_bank_is_the_mean_share_of_possible_other_products(fd):
    # taxonomy has 7 values, so 2 cross-sold products / 6 possible = 0.333...
    rows = pd.DataFrame({"cross_sold_products": [format_list(["mortgage", "pension"])]})
    assert cross_sell.score_bank(rows, fd) == pytest.approx(2 / 6, rel=1e-3)


def test_score_bank_is_none_when_the_column_is_missing():
    rows = pd.DataFrame({"bank": ["ing"]})
    fd = load_dictionary()
    assert cross_sell.score_bank(rows, fd) is None


def test_score_bank_is_none_when_every_page_cross_sells_nothing(fd):
    rows = pd.DataFrame({"cross_sold_products": [format_list([]), format_list([])]})
    # An explicit empty list still counts as "measured, ratio 0",
    # not "unmeasured" - dropna() keeps it, so the mean is 0.0, not None.
    assert cross_sell.score_bank(rows, fd) == 0.0


def test_score_all_matches_the_fixture_for_a_bundled_bank(df, fd):
    # ing's archetype cross-sells current_account_pack + investment on every page.
    scores = cross_sell.score_all(df, fd)
    assert scores["ing"] == pytest.approx(2 / 6, rel=1e-3)


def test_score_all_is_zero_for_a_challenger_with_no_bundle(df, fd):
    scores = cross_sell.score_all(df, fd)
    assert scores["revolut"] == 0.0


def test_cross_sell_matrix_counts_pages_by_family_and_cross_sold_product(fd):
    df = pd.DataFrame({
        "product_family": ["mortgage", "mortgage", "savings_account"],
        "cross_sold_products": [format_list(["investment"]), format_list(["investment"]), format_list([])],
    })
    matrix = cross_sell.cross_sell_matrix(df, fd)
    assert matrix.loc["mortgage", "investment"] == 2
    assert matrix.loc["savings_account"].sum() == 0


def test_most_associated_ranks_the_largest_off_diagonal_cells(fd):
    df = pd.DataFrame({
        "product_family": ["mortgage", "mortgage", "mortgage", "investment"],
        "cross_sold_products": [
            format_list(["investment"]), format_list(["investment"]), format_list(["pension"]), format_list(["mortgage"]),
        ],
    })
    matrix = cross_sell.cross_sell_matrix(df, fd)
    top = cross_sell.most_associated(matrix, n=1)
    assert top == [("mortgage", "investment", 2)]


def test_never_paired_excludes_the_diagonal_and_any_seen_pair(fd):
    df = pd.DataFrame({
        "product_family": ["mortgage"] * 3,
        "cross_sold_products": [format_list(["investment"]), format_list([]), format_list([])],
    })
    matrix = cross_sell.cross_sell_matrix(df, fd)
    page_counts = df.groupby("product_family").size()
    result = cross_sell.never_paired(matrix, page_counts)
    all_pairs = result["confirmed"] + result["insufficient_data"]
    assert ("mortgage", "investment") not in all_pairs
    assert ("mortgage", "mortgage") not in all_pairs  # diagonal excluded
    assert ("mortgage", "pension") in result["confirmed"]  # 3 pages, enough to trust the zero


# The exact scenario that prompted the split - 1 page in a family
# is not enough to call its zero cells a real "never".
def test_never_paired_flags_a_thin_family_as_insufficient_data(fd):
    df = pd.DataFrame({
        "product_family": ["pension"],
        "cross_sold_products": [format_list([])],
    })
    matrix = cross_sell.cross_sell_matrix(df, fd)
    page_counts = df.groupby("product_family").size()
    result = cross_sell.never_paired(matrix, page_counts)
    assert result["confirmed"] == []
    assert ("pension", "mortgage") in result["insufficient_data"]
