"""The feature contract, loaded and enforced.

The hash primitive itself lives in `hashing.py`; this module is about the shape
of the vector — which namespaces exist, which numeric fields exist, in what
order, and which of them each ablation variant switches on.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..config import FEATURE_SPEC_PATH
from ..errors import FeatureSpecError
from .hashing import HashConfig

SUPPORTED_HASH_ALGORITHM = "murmur3_x86_32"


@dataclass(frozen=True)
class NumericField:
    name: str
    group: str
    stage: str
    description: str = ""

    @property
    def is_graph_global(self) -> bool:
        """Whether this field needs the whole graph rather than one file.

        The distinction decides whether classification can run per-file and
        incrementally: a symbol nobody touched can still change class when a
        different file starts calling it.
        """
        return self.stage == "post-graph"


@dataclass(frozen=True)
class VariantConfig:
    """Which blocks one ablation variant switches on."""

    name: str
    use_lexical: bool
    numeric_groups: tuple[str, ...]


@dataclass(frozen=True)
class FeatureSpec:
    version: str
    hash: HashConfig
    namespaces: tuple[str, ...]
    numeric_fields: tuple[NumericField, ...]
    variants: dict[str, VariantConfig]

    @property
    def numeric_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.numeric_fields)

    @property
    def vector_size(self) -> int:
        return self.hash.buckets + len(self.numeric_fields)

    def fields_in_groups(self, groups: tuple[str, ...]) -> tuple[NumericField, ...]:
        wanted = set(groups)
        return tuple(field for field in self.numeric_fields if field.group in wanted)

    def variant(self, name: str) -> VariantConfig:
        if name not in self.variants:
            known = ", ".join(sorted(self.variants))
            raise FeatureSpecError(f"unknown ablation variant {name!r}; known variants: {known}")
        return self.variants[name]


def load_feature_spec(path: Path | None = None) -> FeatureSpec:
    raw = json.loads((path or FEATURE_SPEC_PATH).read_text(encoding="utf-8"))

    return FeatureSpec(
        version=raw["featureVersion"],
        hash=_read_hash_config(raw["hash"]),
        namespaces=tuple(namespace["prefix"] for namespace in raw["lexical"]["namespaces"]),
        numeric_fields=_read_numeric_fields(raw["numeric"]["fields"]),
        variants=_read_variants(raw["ablationVariants"]),
    )


def _read_variants(raw: dict) -> dict[str, VariantConfig]:
    """Skips non-variant entries such as the spec's own `rationale` note."""
    return {
        name: VariantConfig(
            name=name,
            use_lexical=bool(value.get("lexical")),
            numeric_groups=tuple(str(group) for group in value.get("numericGroups") or ()),
        )
        for name, value in raw.items()
        if isinstance(value, dict)
    }


def _read_hash_config(raw: dict) -> HashConfig:
    if raw["algorithm"] != SUPPORTED_HASH_ALGORITHM:
        raise FeatureSpecError(
            f"unsupported hash algorithm {raw['algorithm']!r}; changing it requires a new "
            "featureVersion and a regenerated golden fixture"
        )
    return HashConfig(
        algorithm=raw["algorithm"],
        seed=int(raw["seed"]),
        buckets=int(raw["buckets"]),
        signed=bool(raw["signed"]),
        encoding=raw["encoding"],
        occurrence=raw["occurrence"],
    )


def _read_numeric_fields(raw: list[dict]) -> tuple[NumericField, ...]:
    fields = tuple(
        NumericField(
            name=field["name"],
            group=field["group"],
            stage=field["stage"],
            description=field.get("description", ""),
        )
        for field in raw
    )

    names = [field.name for field in fields]
    duplicates = {name for name in names if names.count(name) > 1}
    if duplicates:
        raise FeatureSpecError(f"duplicate numeric fields: {', '.join(sorted(duplicates))}")
    return fields
