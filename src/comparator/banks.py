"""Canonical bank facts - the things that are true regardless of any capture.

Bank -> category was living implicitly in the collection targets
file and in whatever row happened to be loaded. That is fine until a row arrives
from somewhere else (an imported manual capture, say) and has no category at
all, which fails validation on a fact nobody needed to look up.
"""

from __future__ import annotations

# A digital-first bank with no branch network is a challenger; the rest are
# incumbents. This is the split the PRD's BO-02 asks about.
BANK_CATEGORY: dict[str, str] = {
    "ing": "traditional",
    "kbc": "traditional",
    "bnp_paribas_fortis": "traditional",
    "argenta": "traditional",
    "crelan": "traditional",
    "belfius": "traditional",
    # CBC is KBC Group's francophone brand, a separate search entity in the
    # Trends benchmark but the same incumbent model.
    "cbc": "traditional",
    # Collected live in the current_account_pack family. Hello bank!
    # is BNP Paribas Fortis's digital brand, classified traditional for the same
    # reason cbc is: the institution behind it is an incumbent.
    "vdk": "traditional",
    "hellobank": "traditional",
    "beobank": "traditional",
    # Keytrade Bank is a branchless direct bank since 1998, so it sits with
    # the challengers on the business-model axis.
    "keytrade": "challenger",
    "revolut": "challenger",
    "n26": "challenger",
    "bunq": "challenger",
}


# How each bank is named to a reader, and to a news search. One home for it:
# run_analysis.py used to pass the raw key ("bnp_paribas_fortis") as the name,
# so the reputation search for BNP Paribas Fortis and Hello bank! found nothing
# while the web export, with its own copy of these names, found headlines.
BANK_DISPLAY: dict[str, str] = {
    "ing": "ING", "kbc": "KBC", "belfius": "Belfius", "argenta": "Argenta",
    "crelan": "Crelan", "bnp_paribas_fortis": "BNP Paribas Fortis",
    "revolut": "Revolut", "n26": "N26", "bunq": "bunq", "cbc": "CBC",
    "beobank": "Beobank", "hellobank": "Hello bank!", "keytrade": "Keytrade Bank",
    "vdk": "VDK Bank",
}


def display_name(bank: str) -> str:
    """The reader-facing name, or a tidied key for a bank not listed above."""
    return BANK_DISPLAY.get(bank, bank.replace("_", " ").title())


def category_for(bank: str | None) -> str | None:
    """The bank's category, or None for a bank we have not classified."""
    return BANK_CATEGORY.get(bank) if bank else None
