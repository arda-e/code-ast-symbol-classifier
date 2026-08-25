"""Rendering a result so nothing required can go missing.

Every item on the checklist gets a line. An unmeasured one prints as
"not measured" rather than being left out — a missing row reads as a number
nobody needed rather than one nobody took.
"""

from __future__ import annotations

from . import confusion as confusion_module
from .latency import LatencyStats
from .results import Calibration, EvaluationResult


def render(
    result: EvaluationResult,
    *,
    title: str,
    latency: LatencyStats | None = None,
    model_size_bytes: int | None = None,
    context: dict[str, object] | None = None,
) -> str:
    sections = [
        f"# {title}",
        _context(context),
        _headline(result),
        _per_class_table(result),
        _thresholded(result),
        _cost(latency, model_size_bytes),
        _confusion(result),
    ]
    return "\n\n".join(section for section in sections if section) + "\n"


def _context(context: dict[str, object] | None) -> str:
    if not context:
        return ""
    return "\n".join(f"- **{key}**: {value}" for key, value in context.items())


def _headline(result: EvaluationResult) -> str:
    return "\n".join(
        [
            "## Headline",
            "",
            f"- macro-F1: **{result.macro_f1:.3f}**",
            f"- accuracy: {result.accuracy:.3f}  _(never reported without macro-F1 beside it)_",
            f"- samples: {result.sample_count}",
        ]
    )


def _per_class_table(result: EvaluationResult) -> str:
    rows = [
        f"| {metrics.label} | {metrics.precision:.3f} | {metrics.recall:.3f} | "
        f"{metrics.f1:.3f} | {metrics.support} | {'low-N' if metrics.low_n else ''} |"
        for metrics in result.per_class
    ]
    return "\n".join(
        [
            "## Per class",
            "",
            "| class | precision | recall | F1 | support | |",
            "|---|---:|---:|---:|---:|---|",
            *rows,
        ]
    )


def _thresholded(result: EvaluationResult) -> str:
    calibration = result.calibration
    return "\n".join(
        [
            "## Thresholded behaviour",
            "",
            f"- coverage: {result.coverage:.3f}",
            f"- precision@covered: {result.precision_at_covered:.3f}",
            f"- abstention rate: {result.abstention_rate:.3f}",
            f"- accept bucket: n={calibration.accept_count}, "
            f"precision={_optional(calibration.accept_precision)}",
            f"- tentative bucket: n={calibration.tentative_count}, "
            f"precision={_optional(calibration.tentative_precision)}",
            f"- calibration: {_calibration_verdict(calibration)}",
        ]
    )


def _cost(latency: LatencyStats | None, model_size_bytes: int | None) -> str:
    lines = ["## Cost", ""]
    if latency is None:
        lines.append("- latency: not measured")
    else:
        lines += [
            f"- p50 / p95 / p99: {latency.p50_ms:.3f} / {latency.p95_ms:.3f} / "
            f"{latency.p99_ms:.3f} ms  _(n={latency.samples})_",
            f"- cold start: {latency.cold_start_ms:.3f} ms",
        ]

    lines.append(
        "- model size: not measured"
        if model_size_bytes is None
        else f"- model size: {model_size_bytes / 1024:.1f} KB"
    )
    return "\n".join(lines)


def _confusion(result: EvaluationResult) -> str:
    rendered = confusion_module.render(result.confusion, result.labels)
    return "\n".join(["## Confusion", "", "```", rendered, "```"])


def _calibration_verdict(calibration: Calibration) -> str:
    separates = calibration.separates
    if separates is None:
        return "not enough predictions in one of the buckets to tell"
    if separates:
        return "accept is more precise than tentative — the threshold separates"
    return "**accept is not more precise than tentative — the threshold separates nothing**"


def _optional(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"
