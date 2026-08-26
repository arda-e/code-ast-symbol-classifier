"""STAGE 5 — the part that actually learns.

    uv run pytest tests/spec/test_stage5_train.py

You are writing `train_classifier` in `model/train.py`. It is three lines.

That is not a joke about scope — it is the point of the whole design. Stages 1
to 4 were deterministic: split, prefix, hash, count, scale. Same input, same
output, rules written by a person. None of it learned anything. Only this stage
does, and what it learns is a table:

    name:validate      raises the score for validator      +2.8
    callee:save        raises the score for orchestrator   +0.7
    comparisonCount    raises the score for domain_logic   +0.9

Nobody wrote that table. It comes out of the labelled examples. That is the
entire difference between this and a pile of if-statements: with rules, a person
decides which signal matters and how much; here the data decides.

TWO SETTINGS CARRY THE WEIGHT.

`C` constrains how large the weights may grow. With a couple of hundred examples
against 4163 features, there are far more knobs than evidence — an unconstrained
model can memorise one private feature per example, score perfectly on what it
has seen, and fall apart on the next symbol. Smaller `C` forces a simpler answer.

`class_weight="balanced"` stops the model taking the easy way out. If one class
is a third of the data, always answering with it is genuinely good for accuracy
and useless to us. Balancing makes a mistake on a rare class cost more.

READ FIRST: `contracts/model-artifact.md`, and `config.py` for where these
settings come from.

DONE WHEN: all six pass. At that point `make evaluate` produces a real report
and `make ablate` a real table — the harness has been waiting for exactly this.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from code_ast_symbol_classifier.config import TrainingConfig
from code_ast_symbol_classifier.model import artifact as artifact_module
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
    """The smallest possible sanity check: two obviously different groups."""
    features, labels = separable
    estimator = train_classifier(features, labels, TrainingConfig())

    assert list(estimator.predict(features)) == labels


def test_config_settings_reach_the_estimator(separable):
    """A reported number is worthless if the settings behind it are unknown."""
    features, labels = separable
    config = TrainingConfig(regularisation=0.25, max_iter=321)
    estimator = train_classifier(features, labels, config)

    assert estimator.C == 0.25
    assert estimator.max_iter == 321
    assert estimator.class_weight == "balanced"


def test_rare_classes_are_not_simply_ignored():
    """What `class_weight="balanced"` buys."""
    features = csr_matrix(np.array([[1.0, 0.0]] * 20 + [[0.0, 1.0]] * 2))
    labels = ["common"] * 20 + ["rare"] * 2

    estimator = train_classifier(features, labels, TrainingConfig())

    assert "rare" in estimator.predict(csr_matrix(np.array([[0.0, 1.0]])))


def test_cross_validation_produces_a_full_result(sample_dataset, spec, taxonomy):
    """Everything downstream was already built and tested; this connects it."""
    result = cross_validate(sample_dataset, spec=spec, taxonomy=taxonomy, config=TrainingConfig())

    assert result.sample_count == len(sample_dataset)
    assert 0.0 <= result.macro_f1 <= 1.0
    assert len(result.per_class) == len(taxonomy.labels)


def test_training_writes_a_loadable_artifact(sample_dataset, spec, taxonomy, tmp_path):
    """The deployable end of the project: a JSON file, no runtime attached."""
    artifact = train_final(sample_dataset, spec=spec, taxonomy=taxonomy, config=TrainingConfig())
    restored = artifact_module.read(
        artifact.write(tmp_path / "model.json"), expected_feature_version=spec.version
    )

    assert restored.vector_size == spec.vector_size
    assert set(restored.classes) <= set(taxonomy.labels)
