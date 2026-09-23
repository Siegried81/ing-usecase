"""Cross-sell score and product co-occurrence matrix.

the "cross-sell score/graph" from the AI Marketing
Intelligence brief, built on `cross_sold_products` (feature_dictionary.yaml,
extracted by the same single structured call as `target_personas`). No new
LLM call here either - the score and matrix below are pure arithmetic over
that one column, same spirit as `ai_score.py`.

SCORE: the brief's own formula, "products offered / products possible", kept
as a literal 0-1 ratio (not rescaled to 0-10 like ai_score.py's axes, since
this already IS a share, not a composite index). Per page: len(cross_sold_
products) / (taxonomy size - 1) - the page's own product_family is excluded
from the denominator, since a page cannot cross-sell itself. A bank's score is
the mean across its pages; None (never a fabricated 0) if the column is absent
or entirely empty for that bank.

MATRIX (the "graph"): this repo has no graph-drawing library, and one wasn't
worth adding for 7 nodes - a co-occurrence table already answers the brief's
two questions directly: the largest cells are "products most associated", the
zero cells (see `never_paired`) are "missed opportunities" / products never
offered together.

`never_paired` split into confirmed vs insufficient_data. With
only 1-2 real pages in a product family (mortgage, pension, savings_account
today), a "0" in that row is almost always "we never had the chance to see
it", not "these two products are genuinely never combined" - the same small-N
honesty `analysis.py::ing_vs_peers()` already applies (MIN_PEERS_FOR_SD). A
row family needs at least MIN_PAGES_FOR_CONFIDENT_NEVER pages before its zero
cells are reported as a real finding rather than a data gap.
"""

from __future__ import annotations

import pandas as pd

from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.schema import parse_list


MIN_PAGES_FOR_CONFIDENT_NEVER = 3  # Same threshold as analysis.py's MIN_PEERS_FOR_SD


def _taxonomy(fd: FeatureDictionary) -> list[str]:
    return list(fd["cross_sold_products"].values or [])


def score_bank(rows: pd.DataFrame, fd: FeatureDictionary) -> float | None:
    """Mean, across this bank's pages, of cross-sold products / possible other products."""
    if "cross_sold_products" not in rows.columns:
        return None
    taxonomy_size = len(_taxonomy(fd))
    if taxonomy_size <= 1:
        return None
    denominator = taxonomy_size - 1
    ratios = [len(parse_list(cell)) / denominator for cell in rows["cross_sold_products"].dropna()]
    if not ratios:
        return None
    return round(sum(ratios) / len(ratios), 3)


def score_all(df: pd.DataFrame, fd: FeatureDictionary | None = None) -> dict[str, float | None]:
    fd = fd or load_dictionary()
    return {bank: score_bank(df[df["bank"] == bank], fd) for bank in sorted(df["bank"].unique())}


def cross_sell_matrix(df: pd.DataFrame, fd: FeatureDictionary | None = None) -> pd.DataFrame:
    """rows = a page's own product_family, columns = what else it cross-sells, cells = page count."""
    fd = fd or load_dictionary()
    taxonomy = _taxonomy(fd)
    matrix = pd.DataFrame(0, index=taxonomy, columns=taxonomy, dtype=int)
    if "cross_sold_products" not in df.columns or "product_family" not in df.columns:
        return matrix
    for _, row in df.dropna(subset=["product_family"]).iterrows():
        family = row["product_family"]
        if family not in matrix.index:
            continue
        for other in parse_list(row.get("cross_sold_products")):
            if other in matrix.columns:
                matrix.loc[family, other] += 1
    return matrix


def most_associated(matrix: pd.DataFrame, n: int = 5) -> list[tuple[str, str, int]]:
    """Top N (family, cross_sold_with, count) pairs, off-diagonal, count > 0."""
    pairs = [
        (row, col, int(matrix.loc[row, col]))
        for row in matrix.index for col in matrix.columns
        if row != col and matrix.loc[row, col] > 0
    ]
    return sorted(pairs, key=lambda p: p[2], reverse=True)[:n]


def never_paired(
    matrix: pd.DataFrame, page_counts: pd.Series, min_pages: int = MIN_PAGES_FOR_CONFIDENT_NEVER
) -> dict[str, list[tuple[str, str]]]:
    """Off-diagonal (family, other) pairs with zero observed co-occurrence, split by
    whether the row family had enough pages to trust the "never" - see the module
    docstring. `page_counts` is the page count per product_family (its row axis),
    e.g. `df.groupby("product_family").size()`.
    """
    confirmed: list[tuple[str, str]] = []
    insufficient_data: list[tuple[str, str]] = []
    for row in matrix.index:
        bucket = confirmed if page_counts.get(row, 0) >= min_pages else insufficient_data
        for col in matrix.columns:
            if row != col and matrix.loc[row, col] == 0:
                bucket.append((row, col))
    return {"confirmed": confirmed, "insufficient_data": insufficient_data}
