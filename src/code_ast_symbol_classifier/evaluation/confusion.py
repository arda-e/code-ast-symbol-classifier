"""Confusion matrix, built and rendered.

Kept separate from the metrics because it answers a different question: the
numbers say how good, this says which pairs the model keeps mixing up — and the
taxonomy already predicts where that will happen (validator against policy,
orchestrator against domain_logic).
"""

from __future__ import annotations

import numpy as np


def confusion_matrix(y_true: list[str], y_pred: list[str], labels: tuple[str, ...]) -> np.ndarray:
    index = {label: position for position, label in enumerate(labels)}
    matrix = np.zeros((len(labels), len(labels)), dtype=int)

    for true_label, predicted in zip(y_true, y_pred, strict=True):
        if true_label in index and predicted in index:
            matrix[index[true_label]][index[predicted]] += 1
    return matrix


def render(matrix: np.ndarray, labels: tuple[str, ...]) -> str:
    width = max((len(label) for label in labels), default=4)
    header = " " * (width + 2) + " ".join(f"{position:>4}" for position in range(len(labels)))
    rows = [
        f"{label:<{width}} |" + " ".join(f"{count:>4}" for count in row)
        for label, row in zip(labels, matrix, strict=True)
    ]
    legend = [f"{position:>4} = {label}" for position, label in enumerate(labels)]
    return "\n".join([header, *rows, "", *legend])
