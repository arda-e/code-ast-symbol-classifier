"""Reading and writing the deployable model file.

The format is defined in `contracts/model-artifact.md`. `predict_proba` here is
the reference implementation of the inference side: it deliberately uses nothing
but the artifact's own numbers, so a future TypeScript port has something exact
to agree with.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from ..config import TrainingConfig
from ..errors import ArtifactError
from ..features.spec import FeatureSpec

ARTIFACT_VERSION = "1"


@dataclass(frozen=True)
class ModelArtifact:
    feature_version: str
    taxonomy_version: str
    labelset_id: str
    classes: tuple[str, ...]
    coef: np.ndarray
    intercept: np.ndarray
    numeric_fields: tuple[str, ...]
    buckets: int
    scaler_mean: tuple[float, ...] | None
    scaler_scale: tuple[float, ...] | None
    thresholds: dict[str, float]
    training: dict[str, object]
    created_at: str = ""

    @property
    def vector_size(self) -> int:
        return self.buckets + len(self.numeric_fields)

    def predict_proba(self, vector: np.ndarray) -> np.ndarray:
        """Score one already-built feature vector.

        Multiply, add, softmax. The exponential does two jobs: it makes every
        score positive, and it sharpens the gap, so a confident model reads as
        confident rather than merely ahead.
        """
        if vector.shape[-1] != self.vector_size:
            raise ArtifactError(
                f"vector has {vector.shape[-1]} features, artifact expects {self.vector_size}"
            )
        logits = self.coef @ vector + self.intercept
        shifted = np.exp(logits - np.max(logits))
        return shifted / shifted.sum()

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "artifactVersion": ARTIFACT_VERSION,
            "featureVersion": self.feature_version,
            "taxonomyVersion": self.taxonomy_version,
            "labelsetId": self.labelset_id,
            "createdAt": self.created_at or datetime.now(UTC).isoformat(),
            "buckets": self.buckets,
            "numericFields": list(self.numeric_fields),
            "classes": list(self.classes),
            "coef": self.coef.tolist(),
            "intercept": self.intercept.tolist(),
            "scaler": (
                None
                if self.scaler_mean is None
                else {"mean": list(self.scaler_mean), "scale": list(self.scaler_scale or ())}
            ),
            "thresholds": self.thresholds,
            "training": self.training,
        }
        return payload

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=2) + "\n", encoding="utf-8")
        return path


def from_estimator(
    estimator: LogisticRegression,
    *,
    spec: FeatureSpec,
    taxonomy_version: str,
    labelset_id: str,
    numeric_fields: tuple[str, ...],
    scaler_params: tuple[list[float], list[float]] | None,
    thresholds: dict[str, float],
    config: TrainingConfig,
    sample_count: int,
) -> ModelArtifact:
    return ModelArtifact(
        feature_version=spec.version,
        taxonomy_version=taxonomy_version,
        labelset_id=labelset_id,
        classes=tuple(str(c) for c in estimator.classes_),
        coef=np.asarray(estimator.coef_, dtype=float),
        intercept=np.asarray(estimator.intercept_, dtype=float),
        numeric_fields=numeric_fields,
        buckets=spec.hash.buckets,
        scaler_mean=None if scaler_params is None else tuple(scaler_params[0]),
        scaler_scale=None if scaler_params is None else tuple(scaler_params[1]),
        thresholds=dict(thresholds),
        training={
            "variant": config.variant,
            "C": config.regularisation,
            "classWeight": config.class_weight,
            "maxIter": config.max_iter,
            "seed": config.seed,
            "sampleCount": sample_count,
        },
    )


def read(path: Path, *, expected_feature_version: str | None = None) -> ModelArtifact:
    """Load an artifact, refusing a feature-version mismatch.

    Refusing is the correct behaviour rather than a strict one: a vector built by
    a different extractor version lines up column-for-column with the trained
    weights and produces confident nonsense.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))

    feature_version = payload["featureVersion"]
    if expected_feature_version is not None and feature_version != expected_feature_version:
        raise ArtifactError(
            f"artifact was trained on featureVersion {feature_version!r} but the current "
            f"feature spec is {expected_feature_version!r}; retrain rather than predict"
        )

    scaler = payload.get("scaler")
    return ModelArtifact(
        feature_version=feature_version,
        taxonomy_version=payload["taxonomyVersion"],
        labelset_id=payload.get("labelsetId", "unknown"),
        classes=tuple(payload["classes"]),
        coef=np.asarray(payload["coef"], dtype=float),
        intercept=np.asarray(payload["intercept"], dtype=float),
        numeric_fields=tuple(payload["numericFields"]),
        buckets=int(payload["buckets"]),
        scaler_mean=None if not scaler else tuple(scaler["mean"]),
        scaler_scale=None if not scaler else tuple(scaler["scale"]),
        thresholds=dict(payload.get("thresholds") or {}),
        training=dict(payload.get("training") or {}),
        created_at=payload.get("createdAt", ""),
    )
