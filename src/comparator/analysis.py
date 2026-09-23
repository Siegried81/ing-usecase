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

# After Sieg asked why the chart said "50 features" when the
# dictionary has 97. It is a fair question and the answer was nowhere in the
# output, so the accounting below is now computed and printed rather than
# reconstructed by hand.
BAND_SUFFIX = "_band"

# A gap expressed in peer standard deviations is only meaningful if
# the peers actually vary and there are enough of them. brand_colour_share came
# back [0.0, 0.014, nan, 0.0] on the first real run: ING at 0.228 scored +33.8 SD
# and topped the headline chart. That is not a finding about ING, it is a
# division by a peer spread of 0.007 - and the real story was that colour
# extraction had failed for most banks.
MIN_PEERS_FOR_SD = 3
# Peer spread below this fraction of the peer mean is treated as no spread.
DEGENERATE_SPREAD = 0.05
# With a handful of peers, a gap this large cannot be a characteristic of the
# bank - it means the denominator collapsed. brand_colour_share produced +33.8
# SD from a peer spread of 0.007, where peers were [0.0, 0.014, 0.0].
MAX_PLAUSIBLE_SD = 8.0

# Free text and identifiers. Two pages never share a meta_title, so a distance
# over them measures nothing about how a bank communicates.
FREE_TEXT_FEATURES = {"meta_title", "primary_product", "dominant_colour_hex", "readability_formula"}


def band_redundant_features(fd: FeatureDictionary, df: pd.DataFrame) -> list[str]:
    """`X_band` features whose underlying `X` already enters the comparison.

    the bands exist to make a within_language number cross-language. They
    are a coarser view of a value already in the matrix, so including both would
    count the same signal twice and quietly double the weight of word length.

    Audit finding (MEDIUM). This used to check "is X a numeric
    column present in df", not "does X actually enter the comparison" - so
    when mixed languages excluded X (see language_excluded_features() below),
    X_band was STILL classified as redundant and stayed hidden from
    encodable_categoricals(), even though it is exactly the cross-language
    substitute for the value that just got excluded. Uses comparable_features()
    (the actual used set) instead of raw column presence, so a band becomes
    available the moment its raw number is excluded, language or otherwise.
    """
    used = set(comparable_features(fd, df))
    return sorted(
        f.name for f in fd.features
        if f.name.endswith(BAND_SUFFIX) and f.name[: -len(BAND_SUFFIX)] in used
    )


# Audit finding (HIGH) - comparable_features() picked every numeric
# feature regardless of `comparability`, so word_count/readability_score/
# avg_sentence_length/second_person_ratio/... (all `within_language` in the
# dictionary) were compared raw across banks even when their pages were
# captured in different languages. Confirmed live: collection_targets.yaml has
# KBC with both a fr and a nl page, and bank_vectors() averaged them together
# before any cross-bank comparison. CLAUDE.md: "Never compare a
# within_language feature across two banks captured in different languages
# without flagging it explicitly." This is the flag - excluded, not silently
# kept, whenever the usable pages span more than one language.
def language_excluded_features(fd: FeatureDictionary, df: pd.DataFrame) -> list[str]:
    """within_language features dropped because the usable pages span >1 language.

    Empty when the data is single-language - existing single-language runs are
    unaffected. No band substitution here: bands only enter the comparison
    through include_categorical, a separate opt-in the team controls (see
    feature_accounting()), so this is a plain exclusion, reported like every
    other reduction in render_accounting().
    """
    if "language" not in df.columns or df["language"].dropna().nunique() <= 1:
        return []
    return sorted(
        f.name for f in fd.features
        if (f.is_numeric or f.is_boolean) and f.name in df.columns and f.comparability == "within_language"
    )


def encodable_categoricals(fd: FeatureDictionary, df: pd.DataFrame) -> list[str]:
    """Categorical and list features that carry real signal and could be encoded.

    Excludes provenance, free text, and bands already represented by their raw
    number. What is left is genuinely informative and currently unused - see
    feature_accounting().
    """
    redundant = set(band_redundant_features(fd, df))
    out = []
    for f in fd.features:
        if f.dimension in PROVENANCE or f.name not in df.columns:
            continue
        if f.name in FREE_TEXT_FEATURES or f.name in redundant:
            continue
        if f.is_categorical or f.is_list:
            out.append(f.name)
    return sorted(out)


def feature_accounting(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    include_categorical: bool = False,
) -> dict:
    """Where the dictionary's features go, and why, for one comparison.

    Every number the charts quote comes out of this, so it is computed once and
    reported rather than left for a reader to reverse-engineer.
    """
    fd = fd or load_dictionary()
    provenance = [f.name for f in fd.select(dimension="provenance")]
    free_text = sorted(n for n in FREE_TEXT_FEATURES if n in fd)
    bands = band_redundant_features(fd, df)
    categoricals = encodable_categoricals(fd, df)
    # Report the within_language exclusion the same way every other
    # reduction here is reported - see language_excluded_features().
    language_excluded = language_excluded_features(fd, df)

    matrix = bank_vectors(df, fd, include_categorical=include_categorical)
    incomplete = sorted(c for c in matrix.columns if matrix[c].isna().any())
    complete = matrix.dropna(axis=1, how="any")
    used = standardise(complete)
    constant = sorted(c for c in complete.columns if c not in used.columns)

    return {
        "dictionary_total": len(fd),
        "provenance": provenance,
        "free_text": free_text,
        "band_redundant": bands,
        "language_excluded": language_excluded,
        "categorical": categoricals,
        "categorical_included": bool(include_categorical),
        "incomplete": incomplete,
        "constant": constant,
        "used": list(used.columns),
        "n_used": used.shape[1],
    }


def render_accounting(accounting: dict) -> str:
    """One readable block explaining the reduction."""
    lines = [f"{accounting['dictionary_total']} features in the dictionary"]

    def row(label: str, names: list[str], why: str) -> None:
        if names:
            lines.append(f"  -{len(names):>3}  {label:<26} {why}")

    row("provenance", accounting["provenance"], "identify a page, do not describe a campaign")
    row("free text / identifiers", accounting["free_text"], "no two pages share them")
    row("bands of a number already in", accounting["band_redundant"], "would double-count the same signal")
    # within_language features dropped because >1 language is present.
    row("within_language, mixed languages present", accounting["language_excluded"],
        "not comparable across languages (comparability in the dictionary)")
    if accounting["categorical_included"]:
        lines.append(
            f"  +{len(accounting['categorical']):>3}  categorical / list         "
            "one-hot encoded, each weighted 1/sqrt(k)"
        )
    else:
        row("categorical / list", accounting["categorical"], "not encoded - see note below")
    row("missing for some bank", accounting["incomplete"], "cannot compare what one bank lacks")
    row("no variation across banks", accounting["constant"], "identical everywhere, carries no signal")

    unit = "columns" if accounting["categorical_included"] else "features"
    lines.append(f"  ={accounting['n_used']:>3}  {unit} used in this comparison")
    if accounting["categorical_included"]:
        lines.append(
            "        (a categorical with k values becomes k columns, so this counts "
            "columns, not features)"
        )
    return "\n".join(lines)


@dataclass
class FamilyScope:
    """Which product family the comparison is restricted to, and what it costs.

    DR-04 says comparisons are only valid within one product family:
    a mortgage page and a current-account page differ because the PRODUCTS
    differ, not because the banks communicate differently. Every run so far
    pooled three families and carried that as a limitation. It does not have to
    be a limitation - it can be a filter.
    """

    family: str | None
    banks: list[str]
    traditional: list[str]
    challenger: list[str]
    dropped_banks: list[str]
    pages: int

    @property
    def comparable(self) -> bool:
        """Both sides of the traditional/challenger question need a bank in them."""
        return bool(self.traditional) and bool(self.challenger)

    def render(self) -> str:
        if self.family is None:
            return ("Comparing across ALL product families pooled together. Any cross-bank "
                    "difference is confounded by product (DR-04) - pass --product-family to fix.")
        lines = [
            f"Restricted to product family '{self.family}': {self.pages} page(s), "
            f"{len(self.banks)} bank(s).",
            f"  traditional: {', '.join(self.traditional) or 'none'}",
            f"  challenger : {', '.join(self.challenger) or 'none'}",
        ]
        if self.dropped_banks:
            lines.append(f"  dropped (no page in this family): {', '.join(self.dropped_banks)}")
        if not self.comparable:
            lines.append("  NOT comparable: one side of the traditional/challenger split is empty.")
        return "\n".join(lines)


def family_options(df: pd.DataFrame) -> pd.DataFrame:
    """Which families could be compared like-for-like, ranked by usefulness.

    A family with banks on only one side of the split cannot answer BO-02, so
    the team can see at a glance which family is worth collecting more of.
    """
    if "product_family" not in df.columns:
        return pd.DataFrame()
    rows = []
    for family, group in df.groupby("product_family", observed=True):
        banks = group.drop_duplicates("bank")
        traditional = sorted(banks[banks["bank_category"] == "traditional"]["bank"])
        challenger = sorted(banks[banks["bank_category"] == "challenger"]["bank"])
        rows.append({
            "product_family": family,
            "pages": len(group),
            "banks": len(banks),
            "traditional": len(traditional),
            "challenger": len(challenger),
            "comparable": bool(traditional and challenger),
        })
    out = pd.DataFrame(rows)
    return out.sort_values(["comparable", "banks"], ascending=[False, False]).reset_index(drop=True)


def scope_to_family(df: pd.DataFrame, family: str | None) -> tuple[pd.DataFrame, FamilyScope]:
    """Filter to one product family and describe what that leaves."""
    all_banks = sorted(df["bank"].dropna().unique()) if "bank" in df.columns else []
    if family is None:
        return df, FamilyScope(None, all_banks, [], [], [], len(df))

    subset = df[df["product_family"] == family]
    banks = subset.drop_duplicates("bank")
    kept = sorted(banks["bank"])
    return subset, FamilyScope(
        family=family,
        banks=kept,
        traditional=sorted(banks[banks["bank_category"] == "traditional"]["bank"]),
        challenger=sorted(banks[banks["bank_category"] == "challenger"]["bank"]),
        dropped_banks=sorted(set(all_banks) - set(kept)),
        pages=len(subset),
    )


def comparable_features(
    fd: FeatureDictionary,
    df: pd.DataFrame,
    *,
    tier: str | None = None,
) -> list[str]:
    """Numeric and boolean features usable in a distance calculation.

    Provenance columns are excluded - they identify a page, they do not describe
    a campaign. within_language features (word_count, readability_score, ...)
    are excluded too whenever the usable pages span more than one language -
    See language_excluded_features() above.
    """
    feats = fd.select(tier=tier, exclude_dimensions=PROVENANCE)
    excluded = set(language_excluded_features(fd, df))
    return [
        f.name for f in feats
        if (f.is_numeric or f.is_boolean) and f.name in df.columns and f.name not in excluded
    ]


def _numeric_frame(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df[columns].copy()
    for c in columns:
        out[c] = pd.to_numeric(out[c].astype("float64"), errors="coerce")
    return out


def _one_hot(df: pd.DataFrame, fd: FeatureDictionary, columns: list[str]) -> pd.DataFrame:
    """Encode categorical and list features as indicators, weight-normalised.

    Indicators only - the weighting happens AFTER standardisation, in
    comparison_matrix(). Scaling here would be pointless: standardise() z-scores
    every column, which erases any constant applied beforehand. (It was written
    that way first; measured, and every dummy still came out at unit variance.)
    """
    frames = []
    for name in columns:
        feature = fd[name]
        if feature.is_list:
            members = sorted({m for cell in df[name].dropna() for m in parse_list(cell)})
            if not members:
                continue
            data = pd.DataFrame(
                {f"{name}={m}": df[name].map(lambda c, m=m: float(m in parse_list(c))) for m in members},
                index=df.index,
            )
        else:
            values = sorted(str(v) for v in df[name].dropna().unique())
            if len(values) < 2:  # constant - no signal, and _standardise would drop it anyway
                continue
            data = pd.DataFrame(
                {f"{name}={v}": (df[name].astype("string") == v).astype("float64") for v in values},
                index=df.index,
            )
        frames.append(data)
    return pd.concat(frames, axis=1) if frames else pd.DataFrame(index=df.index)


def bank_vectors(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    tier: str | None = None,
    include_categorical: bool = False,
) -> pd.DataFrame:
    """One row per bank: the mean of its pages, on comparable features.

    include_categorical adds one-hot encoded categorical and list features. It is
    OFF by default: turning it on moves every number in the analysis, so it is a
    team decision, not a default. feature_accounting() reports what is excluded
    either way.
    """
    fd = fd or load_dictionary()
    cols = comparable_features(fd, df, tier=tier)
    numeric = _numeric_frame(df, cols)

    if include_categorical:
        encoded = _one_hot(df, fd, encodable_categoricals(fd, df))
        numeric = pd.concat([numeric, encoded], axis=1)

    numeric["bank"] = df["bank"].values
    return numeric.groupby("bank", observed=True).mean(numeric_only=True)


def standardise(matrix: pd.DataFrame) -> pd.DataFrame:
    """Z-score each column; drop columns with no variation (they carry no signal)."""
    std = matrix.std(ddof=0)
    keep = std[std > 1e-9].index
    return (matrix[keep] - matrix[keep].mean()) / std[keep]


def comparison_matrix(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    tier: str | None = None,
    include_categorical: bool = False,
) -> pd.DataFrame:
    """Bank vectors, standardised and weighted - the one input every distance uses.

    Positioning_axis() and similarity_matrix() each built this
    inline, which is how the weighting bug below survived: fixing it in one
    place would have left the other wrong.

    THE WEIGHTING. A categorical with k values becomes k columns. After
    standardisation each of those columns has unit variance, so the feature
    weighs k times as much as a single number - 19 categoricals became 55
    columns here and collectively outvoted all 50 numeric features. Each
    feature's block is therefore scaled by 1/sqrt(k) AFTER standardising, which
    makes its contribution to a squared distance comparable to one numeric
    column. Scaling before standardising does nothing at all; z-scoring erases
    it.

    sieg 22/09: audit item #1 asked for this drop to be visible rather than
    silent. It already was - feature_accounting()/render_accounting() report
    every column dropped here under "missing for some bank" on every
    run_analysis.py run, tier=None on both sides so the sets match exactly.
    A second, differently-formatted print() was added straight into this
    function on 21/09 and has been removed - one source of truth, not two.
    """
    fd = fd or load_dictionary()
    vectors = bank_vectors(df, fd, tier=tier, include_categorical=include_categorical)
    z = standardise(vectors.dropna(axis=1, how="any"))
    if not include_categorical:
        return z

    categorical = set(encodable_categoricals(fd, df))
    blocks: dict[str, list[str]] = {}
    for column in z.columns:
        stem = column.split("=")[0]
        if stem in categorical:
            blocks.setdefault(stem, []).append(column)

    weighted = z.copy()
    for columns in blocks.values():
        weighted[columns] = weighted[columns] / np.sqrt(len(columns))
    return weighted


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

        # Why a gap might not be reportable, rather than reporting it anyway.
        note = ""
        if len(peer_values) < MIN_PEERS_FOR_SD:
            note = f"only {len(peer_values)} peer(s) have this feature"
        elif peer_std <= 1e-9:
            note = "every peer has the same value - no spread to measure against"
        elif abs(peer_mean) > 1e-9 and peer_std < DEGENERATE_SPREAD * abs(peer_mean):
            note = "peer spread is negligible - an SD gap here is an artefact, not a finding"
        elif abs(peer_mean) <= 1e-9 and peer_std < 1e-3:
            note = "peers are all at or near zero - likely a failed extraction, not a real gap"

        gap = (focus_value - peer_mean) / peer_std if peer_std > 1e-9 else 0.0

        # Checked last, because it is the one that catches a collapsed
        # denominator whatever the cause: with this few peers no bank can
        # genuinely sit eight standard deviations from them.
        if not note and abs(gap) > MAX_PLAUSIBLE_SD:
            note = (f"gap of {gap:+.0f} SD from {len(peer_values)} peer(s) - the peer spread "
                    f"collapsed ({peer_std:.4g}), so this is an artefact, most likely a failed "
                    f"extraction for the peers")
        rows.append(
            {
                "feature": feature,
                "dimension": fd[feature].dimension,
                "extraction": fd[feature].extraction,
                f"{focus}_value": focus_value,
                "peer_mean": peer_mean,
                "peer_std": peer_std,
                "peer_n": len(peer_values),
                "gap_sd": gap,
                "reportable": bool(not note),
                "note": note,
                "percentile": float((peer_values < focus_value).mean() * 100),
                "direction": "above peers" if gap > 0 else "below peers",
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # Reportable gaps first, each block ranked by size. Nothing is dropped - an
    # unreportable gap is still visible with the reason attached, because
    # "colour extraction failed for four banks" is itself worth seeing.
    out = out.sort_values(
        by=["reportable", "gap_sd"],
        key=lambda col: col.abs() if col.name == "gap_sd" else col,
        ascending=[False, False],
    )
    return out.reset_index(drop=True)


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
    def has_focus(self) -> bool:
        """The focus bank can be missing for a real reason - ING's
        own page came back as an unrendered shell on the first live run and was
        excluded. The rest of the market analysis is still valid, so this is a
        state to handle, not a crash. It used to surface as KeyError: 'ing' from
        inside pandas, several frames from the cause."""
        return self.focus in self.scores.index

    def _require_focus(self) -> None:
        if not self.has_focus:
            raise ValueError(
                f"{self.focus!r} is not in the positioned banks ({list(self.scores.index)}). "
                f"BO-01 and BO-02 are unanswerable without it - check capture_quality for "
                f"{self.focus} before reading anything into the rest."
            )

    @property
    def focus_score(self) -> float:
        self._require_focus()
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
    include_categorical: bool = False,
) -> Positioning:
    """Project every bank onto the traditional-challenger axis (BO-02)."""
    fd = fd or load_dictionary()
    # Dropna(axis=1, how="any") drops a feature from EVERY bank's
    # vector the moment even one bank is missing it. Invisible on the fixture
    # (nothing is ever missing), but with the real captures a single gap on
    # one page can silently shrink the comparable feature set for everyone.
    # Reported, not silent: feature_accounting() / render_accounting() above
    # name every dropped column with its reason, run_analysis.py prints that
    # block, and outputs/charts.md carries it next to the figure. The same
    # pattern is in similarity_matrix() and profiles._distinctive(). Still no
    # imputation: a dropped feature is reported, never guessed.
    vectors = comparison_matrix(df, fd, tier=tier, include_categorical=include_categorical)
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
    include_categorical: bool = False,
) -> pd.DataFrame:
    """Pairwise euclidean distance between banks in standardised feature space."""
    fd = fd or load_dictionary()
    # See the dropna(axis=1, how="any") note in positioning_axis() above.
    vectors = comparison_matrix(df, fd, tier=tier, include_categorical=include_categorical)
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


def nearest_neighbours(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    focus: str = FOCUS_BANK,
    k: int = 3,
    tier: str | None = None,
) -> pd.Series:
    """The k banks whose communication most resembles the focus bank.

    Same guard as Positioning.focus_score - the focus bank can be
    legitimately absent (an unusable capture), and a KeyError from inside pandas
    is not a useful way to learn that.
    """
    dist = similarity_matrix(df, fd, tier=tier)
    if focus not in dist.index:
        raise ValueError(
            f"{focus!r} is not in the compared banks ({list(dist.index)}) - "
            f"check capture_quality for {focus}"
        )
    return dist.loc[focus].drop(index=focus).sort_values().head(k)


# -----------------------------------------------------------------------------
# BO-04 - recurring patterns across the whole market
# -----------------------------------------------------------------------------
# New function. Unlike category_comparison (traditional vs
# challenger) or cluster_banks (which BANKS resemble each other), BO-04 asks
# for patterns in how campaigns are built regardless of who built them -
# "pages with X tend to also have Y", market-wide. Pairwise correlation is the
# simplest honest way to surface that without claiming causation or
# significance - same descriptive-only posture as the rest of this module
# (PRD risk R-03, see module docstring).
def recurring_patterns(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    tier: str | None = None,
    min_abs_corr: float = 0.5,
) -> pd.DataFrame:
    """Strongest pairwise correlations among comparable features, market-wide (BO-04).

    Correlation, not causation, and no p-value - a description of co-occurrence
    across every bank, not a claim about why it happens.
    """
    fd = fd or load_dictionary()
    cols = comparable_features(fd, df, tier=tier)
    corr = _numeric_frame(df, cols).corr(numeric_only=True)

    rows = []
    seen: set[tuple[str, str]] = set()
    for a in corr.columns:
        for b in corr.columns:
            if a == b or (b, a) in seen:
                continue
            seen.add((a, b))
            value = corr.loc[a, b]
            if pd.isna(value) or abs(value) < min_abs_corr:
                continue
            rows.append(
                {
                    "feature_a": a,
                    "feature_b": b,
                    "correlation": float(value),
                    "direction": "move together" if value > 0 else "move opposite",
                }
            )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.reindex(out["correlation"].abs().sort_values(ascending=False).index).reset_index(drop=True)


# -----------------------------------------------------------------------------
# FR-14 - verify the kickoff-deck observations
# -----------------------------------------------------------------------------
#   claim id -> (bank, human-readable claim, feature, test)
# Ordinal scale for a categorical BAND feature, so a highest/
# lowest deck claim survives once the raw feature it used to test (word_count,
# within_language) gets dropped entirely from the comparison the moment >1
# language is in scope (language_excluded_features()). The band uses fixed,
# universal thresholds (comparability: cross_language, see bands.py) so it
# keeps meaning something across languages - this ordinal reading is used ONLY
# for ranking a deck claim, never as a reported SD gap (that stays on the raw
# feature in ing_vs_peers()).
BAND_ORDINALS: dict[str, dict[str, int]] = {
    "word_count_band": {"very_short": 1, "short": 2, "medium": 3, "long": 4},
}

DECK_CLAIMS: list[dict] = [
    dict(id="H1", bank="belfius", claim="Belfius is pretty verbose",
         feature="word_count_band", test="highest"),
    dict(id="H2", bank="kbc", claim="KBC is straight to the point",
         feature="word_count_band", test="lowest_traditional"),
    dict(id="H3", bank="ing", claim="ING is the only traditional bank using animation",
         feature="has_animation", test="only_traditional_true"),
    # Feature renamed text_image_adjacent -> text_image_layout
    # (boolean -> categorical: beside/stacked/overlaid) - "is_false" no longer
    # applies to a categorical column, replaced with "categorical_is_not".
    dict(id="H4", bank="ing", claim="ING no longer places text next to picture",
         feature="text_image_layout", test="categorical_is_not", not_value="beside"),
    dict(id="H5", bank="revolut", claim="Revolut uses very little text",
         feature="word_count_band", test="lowest"),
]


def _band_ordinal_series(df: pd.DataFrame, feature: str) -> tuple[pd.Series, dict[int, str]]:
    """Per-bank mode of a categorical band, mapped to BAND_ORDINALS. """
    ordinals = BAND_ORDINALS[feature]
    modes = df.dropna(subset=[feature]).groupby("bank", observed=True)[feature].agg(lambda s: s.mode().iat[0])
    return modes.map(ordinals).dropna(), {v: k for k, v in ordinals.items()}


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

        # Categorical claims can't go through bank_vectors (it
        # only carries numeric/boolean columns) - test the per-bank mode from
        # the raw rows directly instead.
        if test == "categorical_is_not":
            if feature in df.columns and bank in set(df["bank"]):
                raw = df.loc[df["bank"] == bank, feature].dropna()
                if raw.empty:
                    evidence = f"no {feature} values recorded for {bank}"
                else:
                    mode_value = raw.mode().iat[0]
                    not_value = claim["not_value"]
                    verdict = "supported" if mode_value != not_value else "not supported"
                    evidence = f"{bank}'s most common {feature}: {mode_value!r} (claim: not {not_value!r})"
        else:
            # A BAND feature (e.g. word_count_band) never appears in
            # vectors (numeric/boolean only) but still ranks fine as an ordinal.
            is_band = feature in BAND_ORDINALS
            if is_band and feature in df.columns:
                series, band_labels = _band_ordinal_series(df, feature)
            elif feature in vectors.columns:
                series, band_labels = vectors[feature].dropna(), None
            else:
                series, band_labels = pd.Series(dtype="float64"), None

            fmt = (lambda v: repr(band_labels[v])) if band_labels else (lambda v: f"{v:.1f}")

            # sieg 23/09: idxmax()/idxmin() pick an arbitrary bank on a tie
            # (whichever comes first in the Series), so a claim could read
            # "supported" purely by index order while an equally-tied claim
            # elsewhere read "not supported" - found live, H2 (KBC) and H5
            # (Revolut) both tied at word_count_band='long' with every other
            # bank, one called "supported", the other "not supported". A tie
            # means the data cannot single out a winner - never "supported".
            if bank not in series.index:
                pass
            elif test == "highest":
                value = series[bank]
                extreme = series.max()
                tied = sorted(series[series == extreme].index)
                verdict = "supported" if tied == [bank] else "not supported"
                evidence = (f"{bank}={fmt(value)}; highest is {fmt(extreme)}"
                            + (f", tied: {tied}" if len(tied) > 1 else f" ({tied[0]})"))
            elif test == "lowest":
                value = series[bank]
                extreme = series.min()
                tied = sorted(series[series == extreme].index)
                verdict = "supported" if tied == [bank] else "not supported"
                evidence = (f"{bank}={fmt(value)}; lowest is {fmt(extreme)}"
                            + (f", tied: {tied}" if len(tied) > 1 else f" ({tied[0]})"))
            elif test == "lowest_traditional":
                value = series[bank]
                sub = series.loc[[b for b in traditional if b in series.index]]
                if sub.empty:
                    verdict, evidence = "not testable", "no traditional banks with this feature in the dataset"
                else:
                    extreme = sub.min()
                    tied = sorted(sub[sub == extreme].index)
                    verdict = "supported" if tied == [bank] else "not supported"
                    evidence = (f"{bank}={fmt(value)}; lowest traditional is {fmt(extreme)}"
                                + (f", tied: {tied}" if len(tied) > 1 else f" ({tied[0]})"))
            elif test == "only_traditional_true":
                value = series[bank]
                others = [b for b in traditional if b != bank and b in series.index]
                others_true = [b for b in others if series[b] > 0]
                verdict = "supported" if value > 0 and not others_true else "not supported"
                evidence = f"{bank}={value:.2f}; other traditional banks above zero: {others_true or 'none'}"

        rows.append({**{k: claim[k] for k in ("id", "bank", "claim", "feature")},
                     "verdict": verdict, "evidence": evidence})

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# FR-10 / BO-06 - insights and recommendations
# -----------------------------------------------------------------------------
# This was the one PRD deliverable (FR-10, priority M - mandatory,
# not S/C) with no function behind it. ing_vs_peers already ranks every gap;
# this only filters it to the ones big enough to argue from and attaches the
# focus bank's own page_ids that show the gap, so every candidate is
# "traceable to specific features and source pages" per FR-10's own wording.
# It does NOT write the insight - "well-argued" is a human judgement call
# (the), this only makes sure nothing is argued without evidence behind it.
def insight_candidates(
    df: pd.DataFrame,
    fd: FeatureDictionary | None = None,
    *,
    focus: str = FOCUS_BANK,
    tier: str | None = None,
    top_n: int = 5,
    min_gap_sd: float = 0.5,
) -> pd.DataFrame:
    """Rank the focus bank's largest, best-evidenced gaps as insight candidates.

    Each row cites the page_id(s) whose value on that feature drove the gap, so
    a reader can go look at the actual page rather than trust the number alone.
    """
    fd = fd or load_dictionary()
    gaps = ing_vs_peers(df, fd, focus=focus, tier=tier)
    candidates = gaps[gaps["gap_sd"].abs() >= min_gap_sd].head(top_n).copy()

    def example_pages(feature: str, direction: str) -> list[str]:
        rows = df[(df["bank"] == focus) & df[feature].notna()] if feature in df.columns else df.iloc[0:0]
        if rows.empty or "page_id" not in rows.columns:
            return []
        ascending = direction == "below peers"
        return rows.sort_values(feature, ascending=ascending)["page_id"].head(2).tolist()

    candidates["example_page_ids"] = [
        example_pages(row["feature"], row["direction"]) for _, row in candidates.iterrows()
    ]
    return candidates.reset_index(drop=True)


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
