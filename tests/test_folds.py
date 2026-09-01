from __future__ import annotations

import pytest

from code_ast_symbol_classifier.evaluation.folds import low_n_classes, stratified_folds


def test_every_example_is_tested_exactly_once():
    labels = ["a"] * 10 + ["b"] * 10
    tested = [index for _, test in stratified_folds(labels, n_splits=5) for index in test]

    assert sorted(tested) == list(range(20))


def test_folds_preserve_class_proportions():
    """The failure this exists to prevent.

    An earlier spike capped per-class training examples and let the overflow land
    in the test set, leaving it 75% one class. Every accuracy it reported was
    indistinguishable from always answering with the majority class.
    """
    labels = ["a"] * 10 + ["b"] * 10

    for _, test_index in stratified_folds(labels, n_splits=5):
        held_out = [labels[i] for i in test_index]
        assert held_out.count("a") == 2
        assert held_out.count("b") == 2


def test_uneven_classes_stay_proportional():
    labels = ["a"] * 15 + ["b"] * 5

    for _, test_index in stratified_folds(labels, n_splits=5):
        held_out = [labels[i] for i in test_index]
        assert held_out.count("a") == 3
        assert held_out.count("b") == 1


def test_train_and_test_never_overlap():
    labels = ["a"] * 10 + ["b"] * 10

    for train_index, test_index in stratified_folds(labels, n_splits=5):
        assert not set(train_index) & set(test_index)


def test_seed_makes_the_split_reproducible():
    labels = ["a"] * 10 + ["b"] * 10
    first = [test.tolist() for _, test in stratified_folds(labels, n_splits=5, seed=7)]
    second = [test.tolist() for _, test in stratified_folds(labels, n_splits=5, seed=7)]

    assert first == second


def test_classes_too_rare_to_split_are_flagged():
    labels = ["a"] * 10 + ["b"] * 3 + ["c"] * 1

    assert low_n_classes(labels, n_splits=5) == ("b", "c")


def test_no_class_is_flagged_when_all_are_populated():
    assert low_n_classes(["a"] * 5 + ["b"] * 5, n_splits=5) == ()


def test_too_few_examples_for_the_requested_folds():
    with pytest.raises(ValueError, match="cannot build"):
        stratified_folds(["a", "b"], n_splits=5)


def test_sample_fixture_splits_cleanly(sample_dataset):
    folds = stratified_folds(list(sample_dataset.labels), n_splits=5)
    assert len(folds) == 5
