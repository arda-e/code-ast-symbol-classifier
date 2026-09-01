"""The report must not be able to quietly omit a required number."""

from __future__ import annotations

import pytest

from code_ast_symbol_classifier.evaluation.latency import LatencyStats
from code_ast_symbol_classifier.evaluation.metrics import evaluate
from code_ast_symbol_classifier.evaluation.report import render

REQUIRED_ROWS = (
    "macro-F1",
    "coverage",
    "precision@covered",
    "abstention rate",
    "calibration",
    "model size",
)


@pytest.fixture
def result():
    return evaluate(
        ["a", "a", "b", "b"],
        ["a", "b", "b", "b"],
        [0.9, 0.7, 0.5, 0.95],
        labels=("a", "b"),
        accept=0.85,
        tentative=0.65,
        low_n=("b",),
    )


@pytest.mark.parametrize("row", REQUIRED_ROWS)
def test_every_required_row_is_present(result, row):
    assert row in render(result, title="test")


def test_unmeasured_items_say_so_rather_than_disappearing(result):
    report = render(result, title="test")

    assert "latency: not measured" in report
    assert "model size: not measured" in report


def test_low_n_classes_are_marked_in_the_table(result):
    assert "low-N" in render(result, title="test")


def test_measured_latency_replaces_the_placeholder(result):
    latency = LatencyStats(p50_ms=0.1, p95_ms=0.2, p99_ms=0.3, cold_start_ms=5.0, samples=100)
    report = render(result, title="test", latency=latency, model_size_bytes=2048)

    assert "not measured" not in report
    assert "cold start" in report
    assert "2.0 KB" in report


def test_a_useless_threshold_is_called_out(result):
    """Reported plainly, because it decides whether the policy means anything."""
    report = render(result, title="test")
    assert "the threshold separates" in report


def test_latency_measurement_reports_percentiles():
    stats = LatencyStats.measure(lambda _: sum(range(50)), n=30, warmup=2)

    assert stats.samples == 30
    assert stats.p50_ms <= stats.p95_ms <= stats.p99_ms
    assert stats.cold_start_ms >= 0
