"""Comparative analysis: ING positioning, group differences, similarity.

PRD: FR-08 (compare banks consistently), FR-09 (position ING), FR-14 (verify the
kickoff-deck hypotheses). BO-01, BO-02, BO-03.

Every function here is descriptive. Sample sizes are small by design (PRD risk
R-03), so nothing in this module computes a p-value or claims significance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.schema import parse_list

PROVENANCE = {"provenance"}
FOCUS_BANK = "ing"


def comparable_features(
    fd: FeatureDictionary,
    df: pd.DataFrame,
    *,
    tier: str | None = None,
) -> list[str]:
    """Numeric and boolean features usable in a distance calculation.

    Provenance columns are excluded - they identify a page, they do not describe
    a campaign.
    """
    feats = fd.select(tier=tier, exclude_dimensions=PROVENANCE)
    return [f.name for f in feats if (f.is_numeric or f.is_boolean) and f.name in df.columns]


def _numeric_frame(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df[columns].copy()
    for c in columns:
        out[c] = pd.to_numeric(out[c].astype("float64"), errors="coerce")
    return out


def bank_vectors(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    tier: str | None = None,
) -> pd.DataFrame:
    """One row per bank: the mean of its pages, on comparable features."""
    fd = fd or load_dictionary()
    cols = comparable_features(fd, df, tier=tier)
    numeric = _numeric_frame(df, cols)
    numeric["bank"] = df["bank"].values
    return numeric.groupby("bank", observed=True).mean(numeric_only=True)


def standardise(matrix: pd.DataFrame) -> pd.DataFrame:
    """Z-score each column; drop columns with no variation (they carry no signal)."""
    std = matrix.std(ddof=0)
    keep = std[std > 1e-9].index
    return (matrix[keep] - matrix[keep].mean()) / std[keep]


# -----------------------------------------------------------------------------
# BO-01 - where does ING stand?
# -----------------------------------------------------------------------------
def ing_vs_peers(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    focus: str = FOCUS_BANK,
    tier: str | None = None,
) -> pd.DataFrame:
    """Per feature: the focus bank's value, the peer mean, and the gap in SDs.

    The gap is expressed in peer standard deviations so features on different
    scales (word_count, ratios, booleans) can sit in one table.
    """
    fd = fd or load_dictionary()
    vectors = bank_vectors(df, fd, tier=tier)
    if focus not in vectors.index:
        raise ValueError(f"{focus!r} is not in the dataset - it cannot be positioned (BO-01)")

    peers = vectors.drop(index=focus)
    rows = []
    for feature in vectors.columns:
        peer_values = peers[feature].dropna()
        focus_value = vectors.loc[focus, feature]
        if peer_values.empty or pd.isna(focus_value):
            continue
        peer_mean = peer_values.mean()
        peer_std = peer_values.std(ddof=0)
        gap = (focus_value - peer_mean) / peer_std if peer_std > 1e-9 else 0.0
        rows.append(
            {
                "feature": feature,
                "dimension": fd[feature].dimension,
                "extraction": fd[feature].extraction,
                f"{focus}_value": focus_value,
                "peer_mean": peer_mean,
                "peer_std": peer_std,
                "gap_sd": gap,
                "percentile": float((peer_values < focus_value).mean() * 100),
                "direction": "above peers" if gap > 0 else "below peers",
            }
        )

    out = pd.DataFrame(rows)
    return out.reindex(out["gap_sd"].abs().sort_values(ascending=False).index).reset_index(drop=True)


# -----------------------------------------------------------------------------
# BO-02 - traditional or challenger?
# -----------------------------------------------------------------------------
def category_comparison(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    tier: str | None = None,
) -> pd.DataFrame:
    """Traditional vs challenger group means, with a standardised effect size.

    Cohen's d is reported as an effect size only - a description of separation
    between two tiny groups, never a significance claim.
    """
    fd = fd or load_dictionary()
    cols = comparable_features(fd, df, tier=tier)
    numeric = _numeric_frame(df, cols)
    numeric["bank_category"] = df["bank_category"].values

    trad = numeric[numeric["bank_category"] == "traditional"][cols]
    chal = numeric[numeric["bank_category"] == "challenger"][cols]

    rows = []
    for feature in cols:
        a, b = trad[feature].dropna(), chal[feature].dropna()
        if len(a) < 2 or len(b) < 2:
            continue
        pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
        d = (b.mean() - a.mean()) / pooled if pooled > 1e-9 else 0.0
        rows.append(
            {
                "feature": feature,
                "dimension": fd[feature].dimension,
                "traditional_mean": a.mean(),
                "challenger_mean": b.mean(),
                "difference": b.mean() - a.mean(),
                "effect_size_d": d,
                "n_traditional": len(a),
                "n_challenger": len(b),
            }
        )

    out = pd.DataFrame(rows)
    return out.reindex(out["effect_size_d"].abs().sort_values(ascending=False).index).reset_index(drop=True)


@dataclass
class Positioning:
    """Where each bank sits on the traditional <-> challenger axis.

    The axis is the line between the two group centroids in standardised feature
    space. Each bank is projected onto it and rescaled so that 0 = the traditional
    centroid and 1 = the challenger centroid. A bank can fall outside [0, 1].
    """

    scores: pd.Series
    focus: str
    n_features: int

    @property
    def focus_score(self) -> float:
        return float(self.scores[self.focus])

    @property
    def verdict(self) -> str:
        s = self.focus_score
        if s < 0.35:
            return "clearly with the traditional banks"
        if s < 0.5:
            return "traditional, but leaning towards the challengers"
        if s < 0.65:
            return "between the two groups, closer to the challengers"
        return "clearly with the challengers"


def positioning_axis(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    focus: str = FOCUS_BANK,
    tier: str | None = None,
) -> Positioning:
    """Project every bank onto the traditional-challenger axis (BO-02)."""
    fd = fd or load_dictionary()
    vectors = standardise(bank_vectors(df, fd, tier=tier).dropna(axis=1, how="any"))
    categories = df.drop_duplicates("bank").set_index("bank")["bank_category"]

    trad_centroid = vectors.loc[categories[categories == "traditional"].index].mean()
    chal_centroid = vectors.loc[categories[categories == "challenger"].index].mean()

    axis = (chal_centroid - trad_centroid).to_numpy()
    norm = float(np.dot(axis, axis))
    if norm < 1e-9:
        raise ValueError("the two groups have identical centroids - no axis to project onto")

    origin = trad_centroid.to_numpy()
    scores = vectors.apply(lambda row: float(np.dot(row.to_numpy() - origin, axis) / norm), axis=1)
    return Positioning(scores=scores.sort_values(), focus=focus, n_features=vectors.shape[1])


# -----------------------------------------------------------------------------
# BO-03 - which banks communicate alike?
# -----------------------------------------------------------------------------
def similarity_matrix(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    tier: str | None = None,
) -> pd.DataFrame:
    """Pairwise euclidean distance between banks in standardised feature space."""
    fd = fd or load_dictionary()
    vectors = standardise(bank_vectors(df, fd, tier=tier).dropna(axis=1, how="any"))
    banks = vectors.index.tolist()
    data = vectors.to_numpy()
    dist = np.linalg.norm(data[:, None, :] - data[None, :, :], axis=-1)
    return pd.DataFrame(dist, index=banks, columns=banks)


def cluster_banks(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    n_clusters: int = 2,
    tier: str | None = None,
) -> pd.Series:
    """Group banks by communication style using hierarchical clustering (Ward)."""
    dist = similarity_matrix(df, fd, tier=tier)
    links = linkage(squareform(dist.to_numpy(), checks=False), method="ward")
    labels = fcluster(links, t=n_clusters, criterion="maxclust")
    return pd.Series(labels, index=dist.index, name="cluster")


def nearest_neighbours(df: pd.DataFrame, fd: FeatureDictionary | None = None, *, focus: str = FOCUS_BANK, k: int = 3) -> pd.Series:
    """The k banks whose communication most resembles the focus bank."""
    dist = similarity_matrix(df, fd)
    return dist.loc[focus].drop(index=focus).sort_values().head(k)


# -----------------------------------------------------------------------------
# FR-14 - verify the kickoff-deck observations
# -----------------------------------------------------------------------------
#   claim id -> (bank, human-readable claim, feature, test)
DECK_CLAIMS: list[dict] = [
    dict(id="H1", bank="belfius", claim="Belfius is pretty verbose",
         feature="word_count", test="highest"),
    dict(id="H2", bank="kbc", claim="KBC is straight to the point",
         feature="word_count", test="lowest_traditional"),
    dict(id="H3", bank="ing", claim="ING is the only traditional bank using animation",
         feature="has_animation", test="only_traditional_true"),
    dict(id="H4", bank="ing", claim="ING no longer places text next to picture",
         feature="text_image_adjacent", test="is_false"),
    dict(id="H5", bank="revolut", claim="Revolut uses very little text",
         feature="word_count", test="lowest"),
]


def check_deck_claims(df: pd.DataFrame, fd: FeatureDictionary | None = None) -> pd.DataFrame:
    """Test each kickoff-deck observation against the data (FR-14).

    A claim the data does not support is a finding, not a failure - saying so
    plainly is part of the deliverable.
    """
    fd = fd or load_dictionary()
    vectors = bank_vectors(df, fd)
    categories = df.drop_duplicates("bank").set_index("bank")["bank_category"]
    traditional = categories[categories == "traditional"].index

    rows = []
    for claim in DECK_CLAIMS:
        feature, bank, test = claim["feature"], claim["bank"], claim["test"]
        verdict, evidence = "not testable", "feature absent from the dataset"

        if feature in vectors.columns and bank in vectors.index:
            series = vectors[feature].dropna()
            value = series.get(bank)

            if test == "highest":
                winner = series.idxmax()
                verdict = "supported" if winner == bank else "not supported"
                evidence = f"{bank}={value:.1f}; highest is {winner}={series.max():.1f}"
            elif test == "lowest":
                winner = series.idxmin()
                verdict = "supported" if winner == bank else "not supported"
                evidence = f"{bank}={value:.1f}; lowest is {winner}={series.min():.1f}"
            elif test == "lowest_traditional":
                sub = series.loc[[b for b in traditional if b in series.index]]
                winner = sub.idxmin()
                verdict = "supported" if winner == bank else "not supported"
                evidence = f"{bank}={value:.1f}; lowest traditional is {winner}={sub.min():.1f}"
            elif test == "only_traditional_true":
                others = [b for b in traditional if b != bank and b in series.index]
                others_true = [b for b in others if series[b] > 0]
                verdict = "supported" if value > 0 and not others_true else "not supported"
                evidence = f"{bank}={value:.2f}; other traditional banks above zero: {others_true or 'none'}"
            elif test == "is_false":
                verdict = "supported" if value < 0.5 else "not supported"
                evidence = f"{bank}={value:.2f} (0 = never adjacent, 1 = always)"

        rows.append({**{k: claim[k] for k in ("id", "bank", "claim", "feature")},
                     "verdict": verdict, "evidence": evidence})

    return pd.DataFrame(rows)


def lever_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """How often each Cialdini lever appears, by bank category."""
    rows = []
    for _, row in df.iterrows():
        for lever in parse_list(row.get("persuasion_levers")):
            rows.append({"bank": row["bank"], "bank_category": row["bank_category"], "lever": lever})
    if not rows:
        return pd.DataFrame(columns=["lever", "traditional", "challenger"])
    long = pd.DataFrame(rows)
    table = long.pivot_table(index="lever", columns="bank_category", values="bank", aggfunc="count").fillna(0)
    return table.astype(int)
