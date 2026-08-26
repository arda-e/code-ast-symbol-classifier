"""STAGE 4 — join the two blocks into one vector.

    uv run pytest tests/spec/test_stage4_build.py

You are writing `FeatureBuilder` in `features/build.py`. It glues stage 2 and
stage 3 together:

    [0,0,...,1,...,1,...,0]  +  [4, 3, 4, 3, 1, ...]
    └── 4096 buckets, 0/1 ──┘    └── 67 numbers, scaled ──┘
                        4163 numbers

Nothing is added or mixed. The model learns a separate weight per position and
does not care where a position came from.

WHY SCALING. The hashed half is only ever 0 or 1. The numeric half is not: a
symbol called from 47 places puts a 47 next to four thousand zeros and ones, and
during training that one number shouts loudly enough to drown the rest.
Standardising the numeric block — subtract the mean, divide by the spread — puts
everything on comparable footing. The fitted mean and spread ship inside the
model artifact, because inference has to repeat the identical transform.

WHY `fit` AND `transform` ARE SEPARATE. The scaler must learn its mean from the
TRAINING rows only. Fit it on everything and the held-out rows have quietly
influenced the numbers used to score them; every result comes out better than
the model really is, and nothing warns you. This split is the only thing
preventing that.

VARIANTS. `A` is names only, `B-local` file-local facts, `B-global` the degree
fields, `C` everything. A disabled block contributes no columns — that is what
makes the ablation table an honest comparison.

READ FIRST: `contracts/feature-spec.v1.json` -> `numeric.scaling` and
`ablationVariants`.

DONE WHEN: the eight tests below pass. `make ablate` then prints four real rows
instead of four errors.
"""

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
    """ "Does this token appear?" — not how many times.

    Repetition is already represented in the numeric block by outDegree and
    distinctCallees. Encoding it twice does not help the model.
    """
    _, matrix = build(spec, sample_dataset.records, "A")

    assert set(np.unique(matrix.toarray())) <= {0.0, 1.0}


def test_scaler_is_fitted_on_training_records_only(spec, sample_dataset):
    """The leak this prevents does not raise — it only flatters the score."""
    records = list(sample_dataset.records)
    builder = FeatureBuilder(spec=spec, variant="B-global").fit(records[:20])
    mean_after_fit = list(builder.scaler_params[0])

    builder.transform(records[20:])

    assert list(builder.scaler_params[0]) == mean_after_fit


def test_lexical_only_variant_has_no_scaler(spec, sample_dataset):
    builder, _ = build(spec, sample_dataset.records, "A")

    assert builder.scaler_params is None


def test_the_same_records_always_produce_the_same_matrix(spec, sample_dataset):
    """Feature building is deterministic. Nothing here learns or drifts."""
    _, first = build(spec, sample_dataset.records, "C")
    _, second = build(spec, sample_dataset.records, "C")

    assert (first != second).nnz == 0
