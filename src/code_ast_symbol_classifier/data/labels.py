"""Hand labels, and the taxonomy version they were produced against.

Labels are versioned separately from symbols because a person produced them
against a specific class list. A set built for one taxonomy cannot be silently
reused for another, so the version travels with the labels rather than being
assumed at the call site.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..errors import SchemaError


@dataclass(frozen=True)
class LabelSet:
    labelset_id: str
    taxonomy_version: str
    labels: dict[str, str]

    def __len__(self) -> int:
        return len(self.labels)

    @staticmethod
    def from_json(payload: dict[str, Any], *, source: str = "<memory>") -> LabelSet:
        labels = payload.get("labels")
        if not isinstance(labels, dict):
            raise SchemaError(f"{source}: label set must carry a 'labels' object of id -> label")

        return LabelSet(
            labelset_id=payload.get("labelsetId", source),
            taxonomy_version=payload.get("taxonomyVersion", "unknown"),
            labels=dict(labels),
        )
