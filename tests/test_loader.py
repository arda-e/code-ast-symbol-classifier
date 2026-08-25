from __future__ import annotations

import pytest

from code_ast_symbol_classifier.data.labels import LabelSet
from code_ast_symbol_classifier.data.loader import join
from code_ast_symbol_classifier.data.records import SymbolRecord
from code_ast_symbol_classifier.errors import SchemaError, TaxonomyError


def record(symbol_id: str) -> SymbolRecord:
    return SymbolRecord(id=symbol_id, name="f", file_path="a.ts", kind="function")


def test_joins_labels_onto_symbols(taxonomy):
    dataset = join(
        [record("a"), record("b")],
        LabelSet("test", taxonomy.version, {"a": "utility"}),
        taxonomy,
    )

    assert dataset.labels == ("utility",)
    assert [r.id for r in dataset.records] == ["a"]


def test_unlabeled_symbols_are_kept_not_dropped(taxonomy):
    dataset = join(
        [record("a"), record("b")],
        LabelSet("test", taxonomy.version, {"a": "utility"}),
        taxonomy,
    )
    assert [r.id for r in dataset.unlabeled] == ["b"]


def test_labels_without_a_symbol_are_reported(taxonomy):
    dataset = join(
        [record("a")],
        LabelSet("test", taxonomy.version, {"a": "utility", "gone": "utility"}),
        taxonomy,
    )
    assert dataset.orphan_labels == ("gone",)


def test_taxonomy_version_mismatch_is_refused(taxonomy):
    """The whole reason label sets carry a version.

    The old 14-class label set joins perfectly well against these symbols and
    would train a model on classes that no longer exist.
    """
    with pytest.raises(SchemaError, match="Re-label"):
        join([record("a")], LabelSet("old", "v0", {"a": "http_handler"}), taxonomy)


def test_label_outside_the_taxonomy_is_refused(taxonomy):
    with pytest.raises(TaxonomyError):
        join([record("a")], LabelSet("test", taxonomy.version, {"a": "made_up"}), taxonomy)


def test_class_counts_are_ordered_by_frequency(taxonomy):
    dataset = join(
        [record("a"), record("b"), record("c")],
        LabelSet("test", taxonomy.version, {"a": "utility", "b": "utility", "c": "policy"}),
        taxonomy,
    )
    assert list(dataset.class_counts) == ["utility", "policy"]


def test_sample_fixture_covers_every_class(sample_dataset, taxonomy):
    assert set(sample_dataset.class_counts) == set(taxonomy.labels)
