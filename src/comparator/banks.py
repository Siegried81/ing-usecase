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
    # CBC is KBC Group's francophone brand (traditional, like cbc's
    # own entry above); Keytrade Bank is a branchless direct bank since 1998,
    # so it sits with the challengers on the business-model axis.
    "keytrade": "challenger",
    "revolut": "challenger",
    "n26": "challenger",
    "bunq": "challenger",
}


def category_for(bank: str | None) -> str | None:
    """The bank's category, or None for a bank we have not classified."""
    return BANK_CATEGORY.get(bank) if bank else None
