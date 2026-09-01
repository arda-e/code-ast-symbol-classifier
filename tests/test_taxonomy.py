from __future__ import annotations

import pytest

from code_ast_symbol_classifier.taxonomy import TaxonomyError, load_taxonomy


def test_taxonomy_declares_ten_classes(taxonomy):
    assert len(taxonomy.classes) == 10


def test_labels_are_unique(taxonomy):
    assert len(set(taxonomy.labels)) == len(taxonomy.labels)


def test_unknown_label_is_rejected(taxonomy):
    with pytest.raises(TaxonomyError):
        taxonomy.validate_label("http_handler")


def test_rejects_duplicate_labels(tmp_path):
    path = tmp_path / "taxonomy.yaml"
    path.write_text(
        "taxonomyVersion: test\nclasses:\n  - label: utility\n  - label: utility\n",
        encoding="utf-8",
    )
    with pytest.raises(TaxonomyError, match="duplicate"):
        load_taxonomy(path)


def test_class_definitions_are_still_missing(taxonomy):
    """Guards the project's top blocker rather than the code.

    Nobody has written what these classes mean. Labelling against an undefined
    class produces disagreement that reads as labeller error. When the
    definitions land, this test flips to asserting the opposite — and that flip
    is the signal that labelling can start.
    """
    assert taxonomy.undefined_classes == taxonomy.labels
