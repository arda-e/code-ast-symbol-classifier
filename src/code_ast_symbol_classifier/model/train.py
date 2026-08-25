"""Fitting the classifier.  [UNIMPLEMENTED SLOT]

This is the only part of the pipeline that learns anything, and it is three
lines. Everything before it — splitting, namespacing, hashing, counting, scaling
— is deterministic data preparation.

Two settings carry most of the weight:

* **`C`** constrains the weights. With a few hundred examples against 4096+
  features, an unconstrained model can find a private feature for every example,
  score perfectly in training, and collapse on an unseen symbol.
* **`class_weight="balanced"`** stops the model from discovering that always
  answering with the most common class is a decent strategy. It is a genuinely
  good strategy for accuracy, and a useless one for us.

Both come from `TrainingConfig` and are recorded in the artifact, so a reported
number can be traced back to the settings that produced it.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression

from ..config import TrainingConfig


def train_classifier(
    features: csr_matrix,
    labels: list[str] | np.ndarray,
    config: TrainingConfig,
) -> LogisticRegression:
    """Fit a multinomial logistic regression and return the fitted estimator."""
    raise NotImplementedError("see contracts/model-artifact.md -> training")
