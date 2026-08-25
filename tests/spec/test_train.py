"""Specification for model/train.py and the end-to-end path — expected to fail
until the feature slots and the training call are written.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from code_ast_symbol_classifier.config import TrainingConfig
from code_ast_symbol_classifier.model.train import train_classifier
from code_ast_symbol_classifier.pipeline import cross_validate, train_final

pytestmark = pytest.mark.spec


@pytest.fixture
def separable():
    features = csr_matrix(np.array([[1.0, 0.0], [1.0, 0.1], [0.0, 1.0], [0.1, 1.0]]))
    return features, ["a", "a", "b", "b"]


def test_returns_a_fitted_estimator(separable):
    features, labels = separable
    estimator = train_classifier(features, labels, TrainingConfig())

    assert sorted(estimator.classes_) == ["a", "b"]
    assert estimator.coef_.shape[1] == 2


def test_learns_a_separable_problem(separable):
    features, labels = separable
    estimator = train_classifier(features, labels, TrainingConfig())

    assert list(estimator.predict(features)) == labels


def test_config_settings_reach_the_estimator(separable):
    features, labels = separable
    config = TrainingConfig(regularisation=0.25, max_iter=321)
    estimator = train_classifier(features, labels, config)

    assert estimator.C == 0.25
    assert estimator.max_iter == 321
    assert estimator.class_weight == "balanced"


def test_rare_classes_are_not_simply_ignored():
    """What `class_weight="balanced"` buys.

    Answering with the majority class is a genuinely good strategy for accuracy
    and a useless one here.
    """
    features = csr_matrix(np.array([[1.0, 0.0]] * 20 + [[0.0, 1.0]] * 2))
    labels = ["common"] * 20 + ["rare"] * 2

    estimator = train_classifier(features, labels, TrainingConfig())

    assert "rare" in estimator.predict(csr_matrix(np.array([[0.0, 1.0]])))


def test_cross_validation_produces_a_full_result(sample_dataset, spec, taxonomy):
    result = cross_validate(sample_dataset, spec=spec, taxonomy=taxonomy, config=TrainingConfig())

    assert result.sample_count == len(sample_dataset)
    assert 0.0 <= result.macro_f1 <= 1.0
    assert len(result.per_class) == len(taxonomy.labels)


def test_training_writes_a_loadable_artifact(sample_dataset, spec, taxonomy, tmp_path):
    from code_ast_symbol_classifier.model import artifact as artifact_module

    artifact = train_final(sample_dataset, spec=spec, taxonomy=taxonomy, config=TrainingConfig())
    restored = artifact_module.read(
        artifact.write(tmp_path / "model.json"), expected_feature_version=spec.version
    )

    assert restored.vector_size == spec.vector_size
    assert set(restored.classes) <= set(taxonomy.labels)
