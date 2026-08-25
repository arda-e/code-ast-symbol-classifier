"""Cross-validation splits that keep the class balance.

Holding out a fixed slice wastes labels that are expensive to produce, and makes
the reported number depend on which slice you happened to cut. Five folds use
every example for testing exactly once and for training four times.

The stratification is the part that has bitten this project before: an earlier
spike capped per-class training examples and let the overflow fall into the test
set, which left the test set 75% one class. Any accuracy it reported was
indistinguishable from always answering with the majority class.
"""

from __future__ import annotations

import warnings
from collections import Counter

import numpy as np
from sklearn.model_selection import StratifiedKFold


def class_counts(labels: list[str]) -> dict[str, int]:
    return dict(Counter(labels))


def low_n_classes(labels: list[str], n_splits: int) -> tuple[str, ...]:
    """Classes too rare to spread across the folds.

    Their per-class F1 is noise. Reported without a marker they sit in the table
    at the same visual weight as everything else and pull decisions the wrong way.
    """
    counts = class_counts(labels)
    return tuple(sorted(label for label, count in counts.items() if count < n_splits))


def stratified_folds(
    labels: list[str],
    *,
    n_splits: int = 5,
    seed: int = 42,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return (train_index, test_index) pairs preserving class proportions.

    sklearn warns about under-populated classes; the warning is suppressed here
    because `low_n_classes` reports the same fact in the results table, where it
    is actually read.
    """
    if len(labels) < n_splits:
        raise ValueError(f"cannot build {n_splits} folds from {len(labels)} labelled examples")

    y = np.asarray(labels)
    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return [(train, test) for train, test in splitter.split(np.zeros(len(y)), y)]
