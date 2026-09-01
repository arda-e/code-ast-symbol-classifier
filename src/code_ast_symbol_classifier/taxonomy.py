"""Reads the label set from its contract file.

No module hardcodes the class list. The taxonomy has already changed once and
will change again while the per-class definitions are being settled; when it
does, only `contracts/taxonomy.v1.yaml` and a version number move.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .config import TAXONOMY_PATH
from .errors import TaxonomyError


@dataclass(frozen=True)
class TaxonomyClass:
    label: str
    definition: str
    summary: str
    discriminating_question: str
    confusable_with: tuple[str, ...]

    @property
    def is_defined(self) -> bool:
        """Whether someone has written what this class actually means.

        Labelling against an undefined class produces disagreement between
        labellers that looks like human error but is a missing definition.
        """
        return bool(self.definition.strip())


@dataclass(frozen=True)
class Taxonomy:
    version: str
    classes: tuple[TaxonomyClass, ...]
    accept_threshold: float
    tentative_threshold: float

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(c.label for c in self.classes)

    def validate_label(self, label: str) -> str:
        if label not in self.labels:
            raise TaxonomyError(
                f"{label!r} is not in taxonomy {self.version}. "
                f"Known labels: {', '.join(self.labels)}"
            )
        return label

    @property
    def undefined_classes(self) -> tuple[str, ...]:
        return tuple(c.label for c in self.classes if not c.is_defined)


def load_taxonomy(path: Path | None = None) -> Taxonomy:
    raw = yaml.safe_load((path or TAXONOMY_PATH).read_text(encoding="utf-8"))

    entries = raw.get("classes")
    if not entries:
        raise TaxonomyError("taxonomy file declares no classes")

    classes = tuple(
        TaxonomyClass(
            label=entry["label"],
            definition=entry.get("definition") or "",
            summary=entry.get("summary") or "",
            discriminating_question=entry.get("discriminating_question") or "",
            confusable_with=tuple(entry.get("confusable_with") or ()),
        )
        for entry in entries
    )

    seen = [c.label for c in classes]
    duplicates = {label for label in seen if seen.count(label) > 1}
    if duplicates:
        raise TaxonomyError(f"duplicate labels in taxonomy: {', '.join(sorted(duplicates))}")

    thresholds = raw.get("thresholds") or {}
    return Taxonomy(
        version=raw["taxonomyVersion"],
        classes=classes,
        accept_threshold=float(thresholds.get("accept", 0.85)),
        tentative_threshold=float(thresholds.get("tentative", 0.65)),
    )
