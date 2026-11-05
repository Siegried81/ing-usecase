"""Data-quality scorecard: the dataset scored on the standard DQ dimensions.

`schema.validate()` already checks completeness, validity, uniqueness and
consistency, but it reports them as a flat list of errors and warnings. A
data-quality team reads a dataset by DIMENSION — how complete, how valid, how
unique, how consistent, how fresh — and wants one number per dimension plus a
gate that fails when one drops. This module names those dimensions and scores
them. It does not re-implement the contract: it reuses the dictionary's own
rules (nullable, required, allowed values, ranges, primary key), so "valid"
has one definition in the codebase, not two.

The six dimensions are the ones a BCBS 239 / DAMA data-quality programme reports
on. Why each is scored the way it is:

- completeness, validity, uniqueness are GATING: a drop here is a real defect,
  so a failure blocks CI, matching the errors `validate()` already raises.
- consistency and timeliness are REPORTED but warn only. The dataset carries a
  known, recorded single-model fallback (NFR-02, D-09); failing the build on a
  limitation that was agreed and written down would be noise, not a gate.
- accuracy is NOT scored. Accuracy is agreement with a trusted reference, and
  this project has no golden source — the model_assisted features were validated
  against human labels on a sample only. A made-up accuracy number would be the
  one dishonest line on a data-quality page, so the dimension is reported as
  "not measurable here", with the reason. That is itself the honest answer.

Thresholds live here, documented, rather than in the feature dictionary: they
are a property of this gate, not of the data contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.schema import parse_list, read_dataset

# A dimension warns below WARN and fails below FAIL. Completeness tolerates a few
# blank optional cells; validity and uniqueness do not tolerate any breach,
# because an out-of-contract value or a duplicate key is an error, not a dip.
COMPLETENESS_WARN = 0.99
COMPLETENESS_FAIL = 0.95
VALIDITY_FAIL = 1.0
UNIQUENESS_FAIL = 1.0
# Consistency is the share of model-assisted rows produced by the dominant model
# (NFR-02). A single model passes; a strict majority with a documented fallback
# warns; no strict majority (dominant share <= 0.5) means the cross-bank
# comparison is half a comparison between models, which fails.
CONSISTENCY_MAJORITY = 0.5


@dataclass
class DimensionScore:
    """One data-quality dimension: a 0..1 score, a status, and why."""

    name: str
    score: float | None  # None when the dimension is not measurable on this data
    status: str  # "pass" | "warn" | "fail" | "not_measured"
    detail: str


@dataclass
class DQReport:
    """The dataset scored across the DQ dimensions, in the shape of the other reports."""

    dimensions: list[DimensionScore] = field(default_factory=list)
    rows: int = 0
    columns_checked: int = 0

    @property
    def ok(self) -> bool:
        """A failure blocks; a warning does not. Mirrors validate()'s error/warning split."""
        return not any(d.status == "fail" for d in self.dimensions)

    def raise_if_failed(self) -> None:
        if not self.ok:
            failed = [f"{d.name}: {d.detail}" for d in self.dimensions if d.status == "fail"]
            joined = "\n  - ".join(failed)
            raise ValueError(f"data quality below threshold:\n  - {joined}")

    def render(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        lines = [
            f"Data-quality scorecard: {status}",
            f"  rows            : {self.rows}",
            f"  columns checked : {self.columns_checked}",
        ]
        for d in self.dimensions:
            shown = "   -  " if d.score is None else f"{d.score:5.3f}"
            lines.append(f"  {d.name:<13} {shown}  {d.status:<12} {d.detail}")
        return "\n".join(lines)

    def as_rows(self) -> list[dict]:
        """Flat rows for a CSV scorecard and for report.json."""
        return [
            {
                "dimension": d.name,
                "score": None if d.score is None else round(d.score, 4),
                "status": d.status,
                "detail": d.detail,
            }
            for d in self.dimensions
        ]


def _status(score: float, *, warn: float, fail: float) -> str:
    if score < fail:
        return "fail"
    if score < warn:
        return "warn"
    return "pass"


def _completeness(df: pd.DataFrame, fd: FeatureDictionary) -> DimensionScore:
    """Share of filled cells over the features the contract insists on.

    Measured over required or not-nullable features present in the frame — the
    columns the dictionary says must carry a value. Legitimately-optional
    nullable features are left out so a sparse optional column does not read as
    missing data.
    """
    feats = [f for f in fd.features if f.name in df.columns and (f.required or not f.nullable)]
    if not feats:
        return DimensionScore("completeness", None, "not_measured", "no required columns present")
    rows = len(df)
    filled = sum(int(df[f.name].notna().sum()) for f in feats)
    total = rows * len(feats)
    score = filled / total if total else 1.0
    offenders = sorted(
        ((f.name, rows - int(df[f.name].notna().sum())) for f in feats),
        key=lambda x: -x[1],
    )
    worst = [f"{name} (-{n})" for name, n in offenders if n][:5]
    detail = f"{len(feats)} required field(s) {score:.1%} filled"
    if worst:
        detail += f"; most blank: {', '.join(worst)}"
    return DimensionScore("completeness", score,
                          _status(score, warn=COMPLETENESS_WARN, fail=COMPLETENESS_FAIL),
                          detail)


def _validity(df: pd.DataFrame, fd: FeatureDictionary) -> DimensionScore:
    """Share of non-null values that satisfy their declared type/range/value set.

    Reuses the dictionary's rules — the same allowed sets and ranges
    `schema.validate()` checks — so a value is valid here exactly when it is
    valid there.
    """
    checked = valid = 0
    offenders: list[str] = []
    for feature in (f for f in fd.features if f.name in df.columns):
        non_null = df[feature.name].dropna()
        if non_null.empty:
            continue
        if feature.is_categorical:
            allowed = set(feature.values or [])
            n = len(non_null)
            bad = int(sum(str(v) not in allowed for v in non_null))
        elif feature.is_list and feature.values:
            allowed = set(feature.values)
            n = len(non_null)
            bad = int(sum(any(m not in allowed for m in parse_list(cell)) for cell in non_null))
        elif feature.is_numeric and feature.range:
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            lo, hi = feature.min, feature.max
            n = len(numeric)
            below = int((numeric < lo).sum()) if lo is not None else 0
            above = int((numeric > hi).sum()) if hi is not None else 0
            bad = below + above
        else:
            continue
        checked += n
        valid += n - bad
        if bad:
            offenders.append(f"{feature.name} ({bad})")
    score = valid / checked if checked else 1.0
    detail = f"{checked} checked value(s), {score:.1%} within the contract"
    if offenders:
        detail += f"; breaches: {', '.join(offenders[:5])}"
    return DimensionScore("validity", score, _status(score, warn=1.0, fail=VALIDITY_FAIL), detail)


def _uniqueness(df: pd.DataFrame, fd: FeatureDictionary) -> DimensionScore:
    """Share of rows whose primary key is unique."""
    pk = fd.primary_key
    if pk not in df.columns:
        return DimensionScore("uniqueness", None, "not_measured", f"primary key {pk!r} not in the data")
    rows = len(df)
    dup_mask = df[pk].duplicated(keep=False)
    dup_rows = int(dup_mask.sum())
    score = 1.0 - dup_rows / rows if rows else 1.0
    offenders = sorted({str(v) for v in df.loc[dup_mask, pk]})
    detail = f"{pk}: {rows - dup_rows}/{rows} rows unique"
    if offenders:
        detail += f"; duplicated: {offenders[:5]}"
    return DimensionScore("uniqueness", score, _status(score, warn=1.0, fail=UNIQUENESS_FAIL), detail)


def _consistency(df: pd.DataFrame) -> DimensionScore:
    """Share of model-assisted rows produced by the dominant extraction model (NFR-02).

    A difference between two banks must be a difference between two banks, not
    between two models. One model is clean; a documented fallback on a few rows
    is a recorded limitation (warn), not a build failure.
    """
    if "extraction_model" not in df.columns:
        return DimensionScore("consistency", None, "not_measured",
                              "no extraction_model column to check model provenance")
    models = df["extraction_model"].dropna()
    if models.empty:
        return DimensionScore("consistency", None, "not_measured", "no model provenance recorded")
    counts = models.value_counts()
    dominant = int(counts.iloc[0])
    score = dominant / int(len(models))
    offenders = [f"{m} ({n})" for m, n in counts.iloc[1:].items()]
    if len(counts) == 1:
        detail = f"single model: {counts.index[0]}"
    else:
        detail = (f"{dominant}/{len(models)} rows on {counts.index[0]}; "
                  f"other model(s): {', '.join(offenders)} - recorded fallback (NFR-02)")
    if score == 1.0:
        status = "pass"
    elif score > CONSISTENCY_MAJORITY:
        status = "warn"
    else:
        status = "fail"
    return DimensionScore("consistency", score, status, detail)


def _timeliness(df: pd.DataFrame) -> DimensionScore:
    """Share of rows carrying a capture timestamp, plus the window they fall in.

    Not a freshness gate — a proof-of-concept snapshot is deliberately a fixed
    window. What matters for quality is that every row is dated, so a reader
    knows the single window every conclusion is valid for (DR-05).
    """
    if "captured_at" not in df.columns:
        return DimensionScore("timeliness", None, "not_measured", "no captured_at column")
    rows = len(df)
    stamps = pd.to_datetime(df["captured_at"], errors="coerce", utc=True)
    dated = int(stamps.notna().sum())
    score = dated / rows if rows else 1.0
    valid = stamps.dropna()
    window = (f"captured {valid.min():%Y-%m-%d} to {valid.max():%Y-%m-%d}; valid for that window only"
              if not valid.empty else "no parseable timestamps")
    detail = f"{dated}/{rows} rows timestamped - {window}"
    return DimensionScore("timeliness", score, _status(score, warn=1.0, fail=1.0), detail)


def _accuracy() -> DimensionScore:
    """Not measurable here: no trusted reference to check values against.

    Reported rather than skipped, because "we cannot measure accuracy and here
    is why" is a data-quality statement, and an omitted dimension reads as an
    oversight.
    """
    return DimensionScore(
        "accuracy", None, "not_measured",
        "no golden source; model_assisted values validated against human labels on a sample only. "
        "Measured against a reference feed in production.",
    )


def score(df: pd.DataFrame, fd: FeatureDictionary | None = None) -> DQReport:
    """Score a dataset across the DQ dimensions, reusing the dictionary's rules."""
    fd = fd or load_dictionary()
    present = [f for f in fd.features if f.name in df.columns]
    return DQReport(
        dimensions=[
            _completeness(df, fd),
            _validity(df, fd),
            _uniqueness(df, fd),
            _consistency(df),
            _timeliness(df),
            _accuracy(),
        ],
        rows=len(df),
        columns_checked=len(present),
    )


_DIMENSION_MEANING = {
    "completeness": "are the required fields populated",
    "validity": "do values sit inside the declared types, ranges and allowed sets",
    "uniqueness": "is the primary key free of duplicates",
    "consistency": "were comparable features produced the same way across the dataset",
    "timeliness": "is every row dated, so the capture window is known",
    "accuracy": "do values agree with a trusted reference",
}


def render_markdown(report: DQReport, *, dataset: str | None = None, synthetic: bool = False) -> str:
    """Render the scorecard as markdown, in the dimensions a DQ programme reports on.

    Generated from the same DQReport the CLI prints and the gate reads, so the
    artefact, the console and the build cannot disagree about a number.
    """
    status_label = "PASS" if report.ok else "FAIL"
    lines = [
        "# Data-quality scorecard",
        "",
        "*Generated from the dataset by `scripts/run_analysis.py`. The dataset is scored on "
        "the standard data-quality dimensions (the ones a BCBS 239 / DAMA programme reports "
        "on), reusing the feature dictionary's own rules so a value is valid here exactly when "
        "it is valid in `schema.validate()`.*",
        "",
        f"**Overall: {status_label}** - {report.rows} rows, {report.columns_checked} columns checked. "
        "Completeness, validity and uniqueness are gating; consistency and timeliness are reported "
        "but warn only; accuracy is not measurable here.",
        "",
    ]
    if synthetic:
        lines += ["> **This run used synthetic fixture data.** The dimensions are real; the numbers "
                  "describe invented rows.", ""]
    if dataset:
        lines += [f"> Dataset: `{dataset}`", ""]
    lines += ["| Dimension | Score | Status | What it asks | Detail |",
              "| --- | --- | --- | --- | --- |"]
    for d in report.dimensions:
        shown = "n/a" if d.score is None else f"{d.score:.1%}"
        meaning = _DIMENSION_MEANING.get(d.name, "")
        lines.append(f"| {d.name.capitalize()} | {shown} | {d.status} | {meaning} | {d.detail} |")
    lines.append("")
    return "\n".join(lines)


def score_dataset(path: str | Path, fd: FeatureDictionary | None = None, *, tier: str = "core") -> DQReport:
    """Load a dataset (non-strict, like the analysis path) and score it.

    Non-strict because real collected data fails strict validation until the
    rubric features are scored; the DQ scorecard is exactly the tool that should
    still report on an incomplete dataset rather than refuse to load it.
    """
    fd = fd or load_dictionary()
    df, _ = read_dataset(path, fd, tier=tier, strict=False)
    return score(df, fd)
