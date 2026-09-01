"""What a symbol set and a label set become once joined."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .records import SymbolRecord


@dataclass(frozen=True)
class LabeledDataset:
    """Symbols that have a label, alongside what was left over.

    The leftovers are kept rather than dropped: `unlabeled` is the prediction
    target once a model exists, and `orphan_labels` — labels whose symbol is
    missing — usually means the labels and the extraction came from different
    revisions, which is worth reporting and not worth crashing on.
    """

    records: tuple[SymbolRecord, ...]
    labels: tuple[str, ...]
    unlabeled: tuple[SymbolRecord, ...]
    orphan_labels: tuple[str, ...]
    taxonomy_version: str
    labelset_id: str

    def __len__(self) -> int:
        return len(self.records)

    @property
    def class_counts(self) -> dict[str, int]:
        counts = Counter(self.labels)
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
