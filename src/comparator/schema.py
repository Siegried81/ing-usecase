"""Dataset schema and validation, derived from the feature dictionary.

PRD: FR-07 (produce the campaign dataset), DR-07 (consistent feature coverage),
DR-10 (machine-readable output), LC-01 (compliance evidence travels with the row).

The validator is deliberately strict. The dataset is the contract between three
people working in parallel for ten days; a silent schema drift on day 6 costs
more than a loud failure on day 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from comparator.dictionary import LIST_SEPARATOR, FeatureDictionary, load_dictionary

# Values accepted when reading a boolean column back from CSV.
_TRUE = {"true", "yes", "1", "t", "y"}
_FALSE = {"false", "no", "0", "f", "n"}


@dataclass
class ValidationReport:
    """Outcome of validating a dataset against the dictionary."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rows: int = 0
    columns_checked: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def raise_if_failed(self) -> None:
        if not self.ok:
            joined = "\n  - ".join(self.errors)
            raise ValueError(f"dataset failed validation:\n  - {joined}")

    def render(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        lines = [
            f"Schema validation: {status}",
            f"  rows checked    : {self.rows}",
            f"  columns checked : {self.columns_checked}",
        ]
        for e in self.errors:
            lines.append(f"  ERROR   {e}")
        for w in self.warnings:
            lines.append(f"  WARNING {w}")
        if self.ok and not self.warnings:
            lines.append("  no issues")
        return "\n".join(lines)


def parse_list(value: object) -> list[str]:
    """List-valued columns are stored pipe-separated so the dataset stays plain CSV."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(LIST_SEPARATOR) if part.strip()]


def format_list(values: list[str] | None) -> str:
    return "" if not values else LIST_SEPARATOR.join(values)


def _coerce_boolean(series: pd.Series) -> pd.Series:
    def one(v: object) -> object:
        if isinstance(v, bool) or v is None or (isinstance(v, float) and pd.isna(v)):
            return v
        text = str(v).strip().lower()
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
        return pd.NA

    return series.map(one)


def coerce_types(df: pd.DataFrame, fd: FeatureDictionary) -> pd.DataFrame:
    """Bring a freshly-read frame to the dictionary's types. Does not validate."""
    out = df.copy()
    for name in out.columns:
        if name not in fd:
            continue
        feature = fd[name]
        if feature.is_numeric:
            out[name] = pd.to_numeric(out[name], errors="coerce")
            if feature.type == "integer":
                out[name] = out[name].astype("Int64")
        elif feature.is_boolean:
            out[name] = _coerce_boolean(out[name]).astype("boolean")
        elif feature.type == "datetime":
            # Format="ISO8601" rather than letting pandas infer.
            # The live path writes microseconds and the manual-capture importer
            # did not, and a column mixing the two silently coerced the odd ones
            # to NaT - captured_at then failed validation as "missing" on rows
            # that had a perfectly good timestamp.
            out[name] = pd.to_datetime(out[name], errors="coerce", utc=True, format="ISO8601")
        elif feature.is_list:
            out[name] = out[name].map(parse_list)
        else:
            out[name] = out[name].astype("string")
    return out


def validate(df: pd.DataFrame, fd: FeatureDictionary, *, tier: str = "core") -> ValidationReport:
    """Check a dataset against the dictionary.

    `tier='core'` requires only the MVP columns, so the pipeline can be validated
    before the extended features exist.
    """
    report = ValidationReport(rows=len(df))
    required = [f for f in fd.features if f.tier == "core"] if tier == "core" else list(fd.features)

    missing = [f.name for f in required if f.required and f.name not in df.columns]
    if missing:
        report.errors.append(f"missing required columns: {missing}")

    unknown = [c for c in df.columns if c not in fd]
    if unknown:
        report.errors.append(
            f"columns absent from the feature dictionary: {unknown}. "
            "Add them to config/feature_dictionary.yaml or drop them - the dictionary is the contract."
        )

    present = [f for f in fd.features if f.name in df.columns]
    report.columns_checked = len(present)

    pk = fd.primary_key
    if pk in df.columns:
        dupes = df[pk][df[pk].duplicated()].tolist()
        if dupes:
            report.errors.append(f"duplicate {pk} values: {sorted(set(dupes))}")

    for feature in present:
        series = df[feature.name]

        if not feature.nullable and series.isna().any():
            n = int(series.isna().sum())
            report.errors.append(f"{feature.name}: {n} missing value(s) but the feature is not nullable")

        non_null = series.dropna()
        if non_null.empty:
            if feature.required:
                report.warnings.append(f"{feature.name}: required feature is entirely empty")
            continue

        if feature.is_categorical:
            allowed = set(feature.values or [])
            bad = sorted({str(v) for v in non_null.unique()} - allowed)
            if bad:
                report.errors.append(f"{feature.name}: values outside the allowed set: {bad}")

        elif feature.is_list and feature.values:
            allowed = set(feature.values)
            seen: set[str] = set()
            for cell in non_null:
                seen.update(parse_list(cell))
            bad = sorted(seen - allowed)
            if bad:
                report.errors.append(f"{feature.name}: list members outside the allowed set: {bad}")

        elif feature.is_numeric and feature.range:
            lo, hi = feature.min, feature.max
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if lo is not None and (numeric < lo).any():
                report.errors.append(f"{feature.name}: values below the minimum of {lo}")
            if hi is not None and (numeric > hi).any():
                report.errors.append(f"{feature.name}: values above the maximum of {hi}")

    # --- compliance and provenance gates -------------------------------------
    if "robots_allowed" in df.columns:
        blocked = df.loc[df["robots_allowed"] == False, "url"].tolist()  # noqa: E712
        if blocked:
            report.errors.append(
                f"COMPLIANCE: {len(blocked)} row(s) were collected from paths robots.txt disallows "
                f"({blocked[:3]}...). These must be removed from the dataset (LC-01)."
            )

    if "data_source" in df.columns:
        counts = df["data_source"].value_counts().to_dict()
        if counts.get("synthetic_fixture"):
            report.warnings.append(
                f"{counts['synthetic_fixture']} synthetic fixture row(s) present - "
                "results from this dataset are NOT findings."
            )
        if counts.get("llm_generated"):
            report.warnings.append(
                f"{counts['llm_generated']} LLM-generated row(s) present - "
                "exclude them from bank comparisons, score them separately."
            )

    # --- is each row even the page we meant to collect? ----------------------
    # See collection/quality.py. These rows are not invalid, they
    # are honest measurements of the wrong page - which is worse, because every
    # range check passes.
    if "capture_quality" in df.columns:
        for verdict, label in (("unusable", "MUST be excluded from analysis"),
                               ("suspect", "needs a human look before use")):
            bad = df[df["capture_quality"] == verdict]
            if not bad.empty:
                names = sorted(bad["bank"].unique()) if "bank" in bad.columns else []
                report.warnings.append(
                    f"{len(bad)} row(s) have capture_quality={verdict} ({names}) - {label}. "
                    "See capture_quality_note for why."
                )

    # --- one judge for every bank (NFR-02) -----------------------------------
    # Decision 6. The model_assisted features are ~a quarter of the
    # dictionary. If Groq rate-limits halfway through a run and the chain falls
    # back, half the banks get labelled by a different model - and the resulting
    # "difference between ING and Revolut" is partly a difference between two
    # LLMs. That is not something to discover while writing the deck.
    if "extraction_model" in df.columns:
        models = sorted(str(m) for m in df["extraction_model"].dropna().unique())
        if len(models) > 1:
            detail = models
            if "bank" in df.columns:
                by_model = (
                    df.dropna(subset=["extraction_model"])
                    .groupby("extraction_model", observed=True)["bank"]
                    .apply(lambda s: sorted(set(s)))
                    .to_dict()
                )
                detail = [f"{m}: {banks}" for m, banks in by_model.items()]
            report.warnings.append(
                "model_assisted features were produced by MORE THAN ONE model "
                f"({'; '.join(str(d) for d in detail)}). Cross-bank comparisons on those "
                "features are partly a comparison between models - either re-run the odd "
                "banks on the pinned model, or report it as a limitation (D-09, NFR-02)."
            )

    # --- coverage: same features attempted for every bank (DR-07) -------------
    if "bank" in df.columns:
        core_feats = [f.name for f in fd.select(tier="core") if f.name in df.columns]
        for bank, group in df.groupby("bank", observed=True):
            empty = [c for c in core_feats if group[c].isna().all()]
            if empty:
                report.warnings.append(
                    f"{bank}: core feature(s) entirely missing: {empty[:5]}"
                    f"{' ...' if len(empty) > 5 else ''} - record a reason (DR-07)"
                )

    return report


def read_dataset(
    path: str | Path,
    fd: FeatureDictionary | None = None,
    *,
    tier: str = "core",
    strict: bool = True,
) -> tuple[pd.DataFrame, ValidationReport]:
    """Read a dataset CSV, coerce it to the dictionary's types, and validate it."""
    fd = fd or load_dictionary()
    df = pd.read_csv(path, keep_default_na=True)
    df = coerce_types(df, fd)
    report = validate(df, fd, tier=tier)
    if strict:
        report.raise_if_failed()
    return df, report


def write_dataset(df: pd.DataFrame, path: str | Path, fd: FeatureDictionary | None = None) -> Path:
    """Write a dataset to CSV in dictionary column order, list columns flattened."""
    fd = fd or load_dictionary()
    out = df.copy()
    for name in out.columns:
        if name in fd and fd[name].is_list:
            out[name] = out[name].map(lambda v: format_list(parse_list(v)))
    ordered = [c for c in fd.names if c in out.columns] + [c for c in out.columns if c not in fd]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out[ordered].to_csv(path, index=False)
    return path
