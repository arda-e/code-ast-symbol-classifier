"""Reading symbols and labels off disk, and joining them."""

from __future__ import annotations

import json
from pathlib import Path

from ..errors import SchemaError
from ..taxonomy import Taxonomy
from .dataset import LabeledDataset
from .labels import LabelSet
from .records import SymbolRecord, parse_jsonl


def load_symbols(path: Path) -> list[SymbolRecord]:
    return parse_jsonl(path.read_text(encoding="utf-8"), source=path.name)


def load_labelset(path: Path) -> LabelSet:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return LabelSet.from_json(payload, source=path.name)


def join(
    records: list[SymbolRecord],
    labelset: LabelSet,
    taxonomy: Taxonomy,
) -> LabeledDataset:
    """Attach labels to symbols, refusing a taxonomy mismatch.

    The refusal is the point. A label set written against the old 14-class list
    joins cleanly against these symbols and trains a model on classes that no
    longer exist, and nothing downstream notices.
    """
    _reject_version_mismatch(labelset, taxonomy)

    by_id = {record.id: record for record in records}
    labeled: list[SymbolRecord] = []
    labels: list[str] = []

    for symbol_id, label in labelset.labels.items():
        taxonomy.validate_label(label)
        record = by_id.get(symbol_id)
        if record is not None:
            labeled.append(record)
            labels.append(label)

    labeled_ids = {record.id for record in labeled}
    return LabeledDataset(
        records=tuple(labeled),
        labels=tuple(labels),
        unlabeled=tuple(record for record in records if record.id not in labeled_ids),
        orphan_labels=tuple(sorted(set(labelset.labels) - set(by_id))),
        taxonomy_version=taxonomy.version,
        labelset_id=labelset.labelset_id,
    )


def _reject_version_mismatch(labelset: LabelSet, taxonomy: Taxonomy) -> None:
    if labelset.taxonomy_version == taxonomy.version:
        return
    raise SchemaError(
        f"label set {labelset.labelset_id!r} targets taxonomy {labelset.taxonomy_version!r}, "
        f"but the loaded taxonomy is {taxonomy.version!r}. Re-label against the current "
        "taxonomy rather than reusing the old set."
    )
