"""Computing the numbers that have to be reported together.

Accuracy alone rewards the majority class: with one class at half the data, a
model that learned nothing scores 50% and reads as respectable. Macro-F1 weights
every class equally, so getting the common one right and the other nine wrong
does not pass.

Thresholds add a second problem. Once the model can abstain, "92% accurate" says
nothing without knowing how often it answered — it might be answering on 5% of
symbols.
"""

from __future__ import annotations

from sklearn.metrics import f1_score, precision_recall_fscore_support

from .confusion import confusion_matrix
from .results import Calibration, ClassMetrics, EvaluationResult
from .thresholds import Bucket, bucket_for


def evaluate(
    y_true: list[str],
    y_pred: list[str],
    confidences: list[float],
    *,
    labels: tuple[str, ...],
    accept: float,
    tentative: float,
    low_n: tuple[str, ...] = (),
) -> EvaluationResult:
    if not (len(y_true) == len(y_pred) == len(confidences)):
        raise ValueError("y_true, y_pred and confidences must be the same length")

    correct = [true == predicted for true, predicted in zip(y_true, y_pred, strict=True)]
    buckets = [bucket_for(value, accept=accept, tentative=tentative) for value in confidences]
    covered = [i for i, bucket in enumerate(buckets) if bucket is not Bucket.UNKNOWN]
    coverage = len(covered) / len(y_true) if y_true else 0.0

    return EvaluationResult(
        macro_f1=float(
            f1_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)
        ),
        accuracy=_ratio(sum(correct), len(correct)),
        per_class=_per_class(y_true, y_pred, labels, low_n),
        coverage=coverage,
        precision_at_covered=_ratio(sum(correct[i] for i in covered), len(covered)),
        abstention_rate=1.0 - coverage,
        calibration=_calibration(correct, buckets),
        sample_count=len(y_true),
        labels=labels,
        confusion=confusion_matrix(y_true, y_pred, labels),
    )


def _per_class(
    y_true: list[str],
    y_pred: list[str],
    labels: tuple[str, ...],
    low_n: tuple[str, ...],
) -> tuple[ClassMetrics, ...]:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=list(labels), zero_division=0
    )
    return tuple(
        ClassMetrics(
            label=label,
            precision=float(precision[position]),
            recall=float(recall[position]),
            f1=float(f1[position]),
            support=int(support[position]),
            low_n=label in low_n,
        )
        for position, label in enumerate(labels)
    )


def _calibration(correct: list[bool], buckets: list[Bucket]) -> Calibration:
    accept = [i for i, bucket in enumerate(buckets) if bucket is Bucket.ACCEPT]
    tentative = [i for i, bucket in enumerate(buckets) if bucket is Bucket.TENTATIVE]

    return Calibration(
        accept_precision=_optional_ratio(correct, accept),
        tentative_precision=_optional_ratio(correct, tentative),
        accept_count=len(accept),
        tentative_count=len(tentative),
    )


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _optional_ratio(correct: list[bool], indices: list[int]) -> float | None:
    if not indices:
        return None
    return sum(correct[i] for i in indices) / len(indices)
