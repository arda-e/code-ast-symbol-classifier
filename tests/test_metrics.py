"""Hand-computed expectations.

Every number below was worked out on paper first. A metrics module tested against
its own output tests nothing.

    y_true      a    a    b    b
    y_pred      a    b    b    b
    confidence  0.9  0.7  0.5  0.95

    class a: predicted once, correct  -> precision 1.0,   recall 0.5, F1 0.667
    class b: predicted 3x, 2 correct  -> precision 0.667, recall 1.0, F1 0.8
"""

from __future__ import annotations

import pytest

from code_ast_symbol_classifier.evaluation.metrics import evaluate

LABELS = ("a", "b")
Y_TRUE = ["a", "a", "b", "b"]
Y_PRED = ["a", "b", "b", "b"]
CONFIDENCES = [0.9, 0.7, 0.5, 0.95]


@pytest.fixture
def result():
    return evaluate(
        Y_TRUE, Y_PRED, CONFIDENCES, labels=LABELS, accept=0.85, tentative=0.65, low_n=("b",)
    )


def test_macro_f1_weights_classes_equally(result):
    assert result.macro_f1 == pytest.approx((0.6666667 + 0.8) / 2, abs=1e-6)


def test_accuracy(result):
    assert result.accuracy == pytest.approx(0.75)


def test_per_class_precision_and_recall(result):
    by_label = {metrics.label: metrics for metrics in result.per_class}

    assert by_label["a"].precision == pytest.approx(1.0)
    assert by_label["a"].recall == pytest.approx(0.5)
    assert by_label["b"].precision == pytest.approx(2 / 3)
    assert by_label["b"].recall == pytest.approx(1.0)


def test_support_counts_true_labels(result):
    assert {m.label: m.support for m in result.per_class} == {"a": 2, "b": 2}


def test_low_n_marking_is_carried_through(result):
    assert {m.label: m.low_n for m in result.per_class} == {"a": False, "b": True}


def test_coverage_excludes_the_unknown_bucket(result):
    assert result.coverage == pytest.approx(0.75)
    assert result.abstention_rate == pytest.approx(0.25)


def test_precision_at_covered_only_counts_answered_predictions(result):
    assert result.precision_at_covered == pytest.approx(2 / 3)


def test_calibration_compares_the_two_buckets(result):
    calibration = result.calibration

    assert (calibration.accept_count, calibration.tentative_count) == (2, 1)
    assert calibration.accept_precision == pytest.approx(1.0)
    assert calibration.tentative_precision == pytest.approx(0.0)
    assert calibration.separates is True


def test_calibration_is_undecidable_with_an_empty_bucket():
    result = evaluate(["a"], ["a"], [0.99], labels=LABELS, accept=0.85, tentative=0.65)

    assert result.calibration.tentative_precision is None
    assert result.calibration.separates is None


def test_a_majority_class_model_scores_badly_on_macro_f1():
    """The reason accuracy alone is not reported.

    Answering "a" for everything is right 80% of the time here, and macro-F1
    still shows it for what it is.
    """
    y_true = ["a"] * 8 + ["b"] * 2
    y_pred = ["a"] * 10

    result = evaluate(y_true, y_pred, [0.9] * 10, labels=LABELS, accept=0.85, tentative=0.65)

    assert result.accuracy == pytest.approx(0.8)
    assert result.macro_f1 < 0.5


def test_mismatched_input_lengths_are_rejected():
    with pytest.raises(ValueError, match="same length"):
        evaluate(["a"], ["a", "b"], [0.9], labels=LABELS, accept=0.85, tentative=0.65)


def test_confusion_matrix_counts_pairs(result):
    a, b = 0, 1
    assert result.confusion[a][a] == 1
    assert result.confusion[a][b] == 1
    assert result.confusion[b][b] == 2
