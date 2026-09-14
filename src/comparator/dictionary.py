"""Load and query the feature dictionary.

PRD: FR-06. The dictionary defines every column of the campaign dataset - its
type, how it is produced, and how far it can be compared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DICTIONARY = REPO_ROOT / "config" / "feature_dictionary.yaml"

# Types that carry a magnitude and can go into a distance calculation.
NUMERIC_TYPES = {"integer", "float"}
LIST_TYPES = {"list[string]"}
LIST_SEPARATOR = "|"


@dataclass(frozen=True)
class Feature:
    """One column of the campaign dataset."""

    name: str
    dimension: str
    definition: str
    type: str
    extraction: str
    source: str
    comparability: str
    tier: str
    required: bool
    nullable: bool
    values: list[str] | None = None
    range: list[Any] | None = None
    unit: str | None = None
    notes: str | None = None
    rubric: dict[int, str] | None = None
    primary_key: bool = False

    @property
    def is_numeric(self) -> bool:
        return self.type in NUMERIC_TYPES

    @property
    def is_boolean(self) -> bool:
        return self.type == "boolean"

    @property
    def is_categorical(self) -> bool:
        return self.type == "categorical"

    @property
    def is_list(self) -> bool:
        return self.type in LIST_TYPES

    @property
    def is_core(self) -> bool:
        return self.tier == "core"

    @property
    def is_judgement_based(self) -> bool:
        """Rubric and model-assisted features carry a trust caveat (NFR-05)."""
        return self.extraction in {"rubric", "model_assisted"}

    @property
    def min(self) -> float | None:
        return None if not self.range else self.range[0]

    @property
    def max(self) -> float | None:
        return None if not self.range else self.range[1]


@dataclass
class FeatureDictionary:
    """The parsed dictionary, with lookups the rest of the code needs."""

    meta: dict[str, Any]
    dimensions: dict[str, dict[str, str]]
    extraction_methods: dict[str, dict[str, str]]
    comparability: dict[str, dict[str, str]]
    tiers: dict[str, str]
    features: list[Feature] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._by_name = {f.name: f for f in self.features}

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, name: str) -> Feature:
        return self._by_name[name]

    def __contains__(self, name: str) -> bool:
        return name in self._by_name

    @property
    def names(self) -> list[str]:
        return [f.name for f in self.features]

    @property
    def primary_key(self) -> str:
        keys = [f.name for f in self.features if f.primary_key]
        if len(keys) != 1:
            raise ValueError(f"dictionary must define exactly one primary key, found {keys}")
        return keys[0]

    def select(
        self,
        *,
        tier: str | None = None,
        dimension: str | None = None,
        extraction: str | None = None,
        kind: str | None = None,
        exclude_dimensions: set[str] | None = None,
    ) -> list[Feature]:
        """Filter features. `kind` is one of numeric / boolean / categorical / list."""
        out = self.features
        if tier:
            out = [f for f in out if f.tier == tier]
        if dimension:
            out = [f for f in out if f.dimension == dimension]
        if extraction:
            out = [f for f in out if f.extraction == extraction]
        if exclude_dimensions:
            out = [f for f in out if f.dimension not in exclude_dimensions]
        if kind:
            attr = f"is_{kind}"
            out = [f for f in out if getattr(f, attr)]
        return out

    def columns(self, tier: str | None = None) -> list[str]:
        """Dataset columns in dictionary order. tier='core' gives the MVP minimum."""
        if tier is None:
            return self.names
        wanted = {"core"} if tier == "core" else {"core", "extended"}
        return [f.name for f in self.features if f.tier in wanted]


def _parse_feature(raw: dict[str, Any]) -> Feature:
    known = set(Feature.__dataclass_fields__)
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"feature {raw.get('name')!r} has unknown keys: {sorted(unknown)}")
    return Feature(**raw)


def load_dictionary(path: str | Path = DEFAULT_DICTIONARY) -> FeatureDictionary:
    """Read the YAML dictionary and check it is internally consistent."""
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    features = [_parse_feature(f) for f in raw["features"]]
    fd = FeatureDictionary(
        meta=raw["meta"],
        dimensions=raw["dimensions"],
        extraction_methods=raw["extraction_methods"],
        comparability=raw["comparability"],
        tiers=raw["tiers"],
        features=features,
    )
    _check_consistency(fd)
    return fd


def _check_consistency(fd: FeatureDictionary) -> None:
    """Fail loudly on a malformed dictionary - it is the contract for three people."""
    seen: set[str] = set()
    for f in fd.features:
        if f.name in seen:
            raise ValueError(f"duplicate feature name: {f.name}")
        seen.add(f.name)

        if f.dimension not in fd.dimensions:
            raise ValueError(f"{f.name}: unknown dimension {f.dimension!r}")
        if f.extraction not in fd.extraction_methods:
            raise ValueError(f"{f.name}: unknown extraction method {f.extraction!r}")
        if f.comparability not in fd.comparability:
            raise ValueError(f"{f.name}: unknown comparability {f.comparability!r}")
        if f.tier not in fd.tiers:
            raise ValueError(f"{f.name}: unknown tier {f.tier!r}")
        if f.is_categorical and not f.values:
            raise ValueError(f"{f.name}: categorical feature must list allowed values")
        if f.required and f.tier != "core":
            raise ValueError(f"{f.name}: a required feature must be in the core tier")
        if f.primary_key and f.nullable:
            raise ValueError(f"{f.name}: the primary key cannot be nullable")

    fd.primary_key  # raises unless exactly one is defined
