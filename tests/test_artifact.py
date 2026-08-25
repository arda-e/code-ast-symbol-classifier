from __future__ import annotations

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression

from code_ast_symbol_classifier.config import TrainingConfig
from code_ast_symbol_classifier.errors import ArtifactError
from code_ast_symbol_classifier.model import artifact as artifact_module
from code_ast_symbol_classifier.model.artifact import ModelArtifact


def tiny_artifact() -> ModelArtifact:
    return ModelArtifact(
        feature_version="v1",
        taxonomy_version="v1",
        labelset_id="test",
        classes=("a", "b"),
        coef=np.array([[1.0, 0.0], [0.0, 1.0]]),
        intercept=np.array([0.0, 0.0]),
        numeric_fields=("outDegree",),
        buckets=1,
        scaler_mean=(0.0,),
        scaler_scale=(1.0,),
        thresholds={"accept": 0.85, "tentative": 0.65},
        training={},
    )


def test_vector_size_is_buckets_plus_numeric_fields():
    assert tiny_artifact().vector_size == 2


def test_predict_proba_is_a_softmax_over_the_logits():
    probabilities = tiny_artifact().predict_proba(np.array([1.0, 0.0]))

    assert probabilities.sum() == pytest.approx(1.0)
    assert probabilities[0] == pytest.approx(np.exp(1) / (np.exp(1) + 1))


def test_predict_proba_rejects_a_wrongly_sized_vector():
    with pytest.raises(ArtifactError, match="expects 2"):
        tiny_artifact().predict_proba(np.array([1.0, 0.0, 3.0]))


def test_roundtrip_preserves_every_field(tmp_path):
    original = tiny_artifact()
    restored = artifact_module.read(original.write(tmp_path / "model.json"))

    assert restored.classes == original.classes
    assert restored.numeric_fields == original.numeric_fields
    assert restored.taxonomy_version == original.taxonomy_version
    assert restored.thresholds == original.thresholds
    assert np.allclose(restored.coef, original.coef)
    assert np.allclose(restored.intercept, original.intercept)


def test_reading_refuses_a_feature_version_mismatch(tmp_path):
    """A shifted vector layout produces confident nonsense, not an error.

    Refusing is the only place this can be caught.
    """
    path = tiny_artifact().write(tmp_path / "model.json")

    with pytest.raises(ArtifactError, match="retrain rather than predict"):
        artifact_module.read(path, expected_feature_version="v2")


def test_from_estimator_records_the_training_settings(spec):
    estimator = LogisticRegression(max_iter=200).fit(
        np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.9], [0.9, 0.1]]), ["a", "b", "a", "b"]
    )
    config = TrainingConfig(variant="C", regularisation=0.5, seed=7)

    artifact = artifact_module.from_estimator(
        estimator,
        spec=spec,
        taxonomy_version="v1",
        labelset_id="test",
        numeric_fields=("outDegree",),
        scaler_params=([0.0], [1.0]),
        thresholds={"accept": 0.85, "tentative": 0.65},
        config=config,
        sample_count=4,
    )

    assert artifact.feature_version == spec.version
    assert artifact.training["C"] == 0.5
    assert artifact.training["seed"] == 7
    assert artifact.training["sampleCount"] == 4
    assert artifact.classes == ("a", "b")
