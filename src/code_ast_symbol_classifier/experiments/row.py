"""One line of the ablation table."""

from __future__ import annotations

from dataclasses import dataclass

from ..evaluation.results import EvaluationResult

MISSING = "—"


@dataclass(frozen=True)
class AblationRow:
    variant: str
    samples: int
    macro_f1: float | None = None
    coverage: float | None = None
    precision_at_covered: float | None = None
    error: str | None = None

    @staticmethod
    def from_result(variant: str, result: EvaluationResult) -> AblationRow:
        return AblationRow(
            variant=variant,
            samples=result.sample_count,
            macro_f1=result.macro_f1,
            coverage=result.coverage,
            precision_at_covered=result.precision_at_covered,
        )

    @staticmethod
    def from_error(variant: str, samples: int, error: Exception) -> AblationRow:
        return AblationRow(variant=variant, samples=samples, error=str(error))

    @property
    def cells(self) -> tuple[str, str, str, str, str]:
        if self.error is not None:
            return (self.variant, f"error: {self.error}", MISSING, MISSING, str(self.samples))
        return (
            self.variant,
            _format(self.macro_f1),
            _format(self.coverage),
            _format(self.precision_at_covered),
            str(self.samples),
        )


def _format(value: float | None) -> str:
    return MISSING if value is None else f"{value:.3f}"
