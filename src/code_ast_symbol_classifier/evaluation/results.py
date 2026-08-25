"""The shapes a measurement comes back in."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ClassMetrics:
    label: str
    precision: float
    recall: float
    f1: float
    support: int
    low_n: bool


@dataclass(frozen=True)
class Calibration:
    """Whether the confidence score means anything.

    A softmax output of 0.94 looks like a probability but is not guaranteed to
    behave like one. The check that matters is blunt: are predictions in the
    accept bucket actually more often right than those in the tentative bucket?
    If not, the threshold separates nothing and no product behaviour should rest
    on it.
    """

    accept_precision: float | None
    tentative_precision: float | None
    accept_count: int
    tentative_count: int

    @property
    def separates(self) -> bool | None:
        """True, False, or None when a bucket was too empty to tell."""
        if self.accept_precision is None or self.tentative_precision is None:
            return None
        return self.accept_precision > self.tentative_precision


@dataclass(frozen=True)
class EvaluationResult:
    macro_f1: float
    accuracy: float
    per_class: tuple[ClassMetrics, ...]
    coverage: float
    precision_at_covered: float
    abstention_rate: float
    calibration: Calibration
    sample_count: int
    labels: tuple[str, ...]
    confusion: np.ndarray
