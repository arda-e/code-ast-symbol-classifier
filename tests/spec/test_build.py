"""Specification for features/build.py — expected to fail until it is written."""

from __future__ import annotations

import numpy as np
import pytest

from code_ast_symbol_classifier.features.build import FeatureBuilder

pytestmark = pytest.mark.spec


def build(spec, records, variant: str):
    builder = FeatureBuilder(spec=spec, variant=variant)
    return builder, builder.fit_transform(list(records))


def test_variant_c_uses_the_full_vector(spec, sample_dataset):
    _, matrix = build(spec, sample_dataset.records, "C")

    assert matrix.shape == (len(sample_dataset), spec.vector_size)


def test_variant_a_has_no_numeric_columns(spec, sample_dataset):
    _, matrix = build(spec, sample_dataset.records, "A")

    assert matrix.shape[1] == spec.hash.buckets


def test_variant_b_global_carries_only_the_degree_fields(spec, sample_dataset):
    _, matrix = build(spec, sample_dataset.records, "B-global")

    assert matrix.shape[1] == len(spec.fields_in_groups(("degree",)))


def test_b_local_and_b_global_together_equal_the_numeric_block(spec, sample_dataset):
    _, local = build(spec, sample_dataset.records, "B-local")
    _, graph_global = build(spec, sample_dataset.records, "B-global")

    assert local.shape[1] + graph_global.shape[1] == len(spec.numeric_fields)


def test_hashed_block_is_binary(spec, sample_dataset):
    _, matrix = build(spec, sample_dataset.records, "A")

    assert set(np.unique(matrix.toarray())) <= {0.0, 1.0}


def test_scaler_is_fitted_on_training_records_only(spec, sample_dataset):
    """Fitting on everything leaks the test fold into training.

    The leak does not raise; it just makes every reported number better than the
    model really is.
    """
    records = list(sample_dataset.records)
    builder = FeatureBuilder(spec=spec, variant="B-global").fit(records[:20])
    mean_after_fit = list(builder.scaler_params[0])

    builder.transform(records[20:])

    assert list(builder.scaler_params[0]) == mean_after_fit


def test_lexical_only_variant_has_no_scaler(spec, sample_dataset):
    builder, _ = build(spec, sample_dataset.records, "A")

    assert builder.scaler_params is None


def test_the_same_records_always_produce_the_same_matrix(spec, sample_dataset):
    _, first = build(spec, sample_dataset.records, "C")
    _, second = build(spec, sample_dataset.records, "C")

    assert (first != second).nnz == 0
