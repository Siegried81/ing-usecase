"""Tests for the canonical bank facts.

banks.py owns the traditional-vs-challenger split that every group comparison
depends on, and it had no test: a typo in a key would have silently moved a bank
between the two groups the whole analysis contrasts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparator import banks  # noqa: E402
from comparator.analysis import lever_frequency  # noqa: E402


def test_every_bank_is_one_of_the_two_categories():
    assert set(banks.BANK_CATEGORY.values()) == {"traditional", "challenger"}


def test_both_groups_are_populated():
    """A group comparison needs both sides; an empty one would read as 'no difference'."""
    counts = pd.Series(list(banks.BANK_CATEGORY.values())).value_counts()
    assert counts["traditional"] >= 2 and counts["challenger"] >= 2


def test_every_bank_has_a_display_name():
    """run_analysis passed the raw key as the search name when one was missing."""
    missing = sorted(set(banks.BANK_CATEGORY) - set(banks.BANK_DISPLAY))
    assert missing == []


def test_keys_are_normalised():
    """Keys are matched against dataset values, so case or spaces would never match."""
    for key in banks.BANK_CATEGORY:
        assert key == key.strip().lower()
        assert " " not in key


def test_the_brands_behind_an_incumbent_stay_traditional():
    """cbc (KBC) and hellobank (BNP) are digital brands of incumbents, not challengers."""
    assert banks.BANK_CATEGORY["cbc"] == "traditional"
    assert banks.BANK_CATEGORY["hellobank"] == "traditional"
    assert banks.BANK_CATEGORY["keytrade"] == "challenger"


def test_lever_frequency_counts_levers_by_category():
    df = pd.DataFrame([
        {"bank": "ing", "bank_category": "traditional", "persuasion_levers": "authority|liking"},
        {"bank": "n26", "bank_category": "challenger", "persuasion_levers": "authority"},
    ])
    table = lever_frequency(df)
    assert table.loc["authority", "traditional"] == 1
    assert table.loc["authority", "challenger"] == 1
    assert table.loc["liking", "traditional"] == 1


def test_lever_frequency_skips_unjudged_pages():
    """An unjudged page contributes no lever, and must not become a row of its
    own in the frequency table."""
    df = pd.DataFrame([
        {"bank": "ing", "bank_category": "traditional", "persuasion_levers": None},
        {"bank": "argenta", "bank_category": "traditional", "persuasion_levers": ""},
        {"bank": "kbc", "bank_category": "traditional", "persuasion_levers": "scarcity"},
    ])
    table = lever_frequency(df)
    assert list(table.index) == ["scarcity"]
    assert table.loc["scarcity", "traditional"] == 1


def test_lever_frequency_on_no_rows_returns_the_empty_shape():
    empty = lever_frequency(pd.DataFrame(columns=["bank", "bank_category", "persuasion_levers"]))
    assert list(empty.columns) == ["lever", "traditional", "challenger"]
    assert empty.empty
