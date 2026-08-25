"""Wiring: dataset in, measured result or model artifact out.

Nothing here decides anything about the model. It fits the scaler on the training
fold only, trains, predicts, and hands the numbers to `evaluation`. Kept apart
from the CLI so tests and the ablation runner exercise the same path.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import TrainingConfig
from .data.dataset import LabeledDataset
from .data.records import SymbolRecord
from .evaluation import folds as folds_module
from .evaluation.metrics import evaluate
from .evaluation.results import EvaluationResult
from .features.build import FeatureBuilder
from .features.spec import FeatureSpec
from .model import artifact as artifact_module
from .model.train import train_classifier
from .taxonomy import Taxonomy


@dataclass(frozen=True)
class FoldPredictions:
    predicted: list[str]
    confidences: list[float]


def cross_validate(
    dataset: LabeledDataset,
    *,
    spec: FeatureSpec,
    taxonomy: Taxonomy,
    config: TrainingConfig,
) -> EvaluationResult:
    """Stratified k-fold over the labelled set, pooling predictions across folds.

    Predictions from every fold are collected and scored once at the end rather
    than averaging five separate scores: with rare classes, a fold where a class
    never appears would otherwise contribute a meaningless zero to the average.
    """
    records = list(dataset.records)
    labels = list(dataset.labels)
    splits = folds_module.stratified_folds(labels, n_splits=config.folds, seed=config.seed)

    y_true: list[str] = []
    y_pred: list[str] = []
    confidences: list[float] = []

    for train_index, test_index in splits:
        fold = _run_fold(
            train_records=[records[i] for i in train_index],
            train_labels=[labels[i] for i in train_index],
            test_records=[records[i] for i in test_index],
            spec=spec,
            config=config,
        )
        y_true += [labels[i] for i in test_index]
        y_pred += fold.predicted
        confidences += fold.confidences

    return evaluate(
        y_true,
        y_pred,
        confidences,
        labels=taxonomy.labels,
        accept=taxonomy.accept_threshold,
        tentative=taxonomy.tentative_threshold,
        low_n=folds_module.low_n_classes(labels, config.folds),
    )


def train_final(
    dataset: LabeledDataset,
    *,
    spec: FeatureSpec,
    taxonomy: Taxonomy,
    config: TrainingConfig,
) -> artifact_module.ModelArtifact:
    """Fit on everything and freeze the result into a deployable artifact."""
    records = list(dataset.records)
    builder = FeatureBuilder(spec=spec, variant=config.variant).fit(records)
    estimator = train_classifier(builder.transform(records), list(dataset.labels), config)

    variant = spec.variant(config.variant)
    return artifact_module.from_estimator(
        estimator,
        spec=spec,
        taxonomy_version=taxonomy.version,
        labelset_id=dataset.labelset_id,
        numeric_fields=tuple(f.name for f in spec.fields_in_groups(variant.numeric_groups)),
        scaler_params=builder.scaler_params,
        thresholds={
            "accept": taxonomy.accept_threshold,
            "tentative": taxonomy.tentative_threshold,
        },
        config=config,
        sample_count=len(dataset),
    )


def _run_fold(
    *,
    train_records: list[SymbolRecord],
    train_labels: list[str],
    test_records: list[SymbolRecord],
    spec: FeatureSpec,
    config: TrainingConfig,
) -> FoldPredictions:
    """Fit on the training side only, then score the held-out side.

    The scaler is fitted here rather than once outside the loop on purpose:
    fitting it on all the data leaks the test fold into training and inflates
    every number downstream.
    """
    builder = FeatureBuilder(spec=spec, variant=config.variant).fit(train_records)
    estimator = train_classifier(builder.transform(train_records), train_labels, config)

    probabilities = estimator.predict_proba(builder.transform(test_records))
    classes = list(estimator.classes_)

    best = np.argmax(probabilities, axis=1)
    return FoldPredictions(
        predicted=[str(classes[i]) for i in best],
        confidences=[float(row[i]) for row, i in zip(probabilities, best, strict=True)],
    )
