"""Which signal is actually doing the work.

Run the same classifier on different slices of the feature set and read the gaps:

    A         names only        — could the answer just be word matching?
    B-local   file-local facts  — counters, flags, effects, mutations
    B-global  graph-global      — degrees, which need the whole codebase
    C         everything

B is split for a reason beyond curiosity. Graph-global features make
classification non-incremental: a symbol nobody edited can change class because
some other file started calling it. If the global block contributes little, that
whole complication can be dropped.

The B rows also answer a blunter question — rename every symbol to f1, f2, f3,
and what is left? Which is the same as asking whether the model survives a
codebase with different naming habits.
"""

from __future__ import annotations

import dataclasses

from ..config import TrainingConfig
from ..data.dataset import LabeledDataset
from ..features.spec import FeatureSpec
from ..pipeline import cross_validate
from ..taxonomy import Taxonomy
from .row import AblationRow

DEFAULT_VARIANTS = ("A", "B-local", "B-global", "C")


def run_ablation(
    dataset: LabeledDataset,
    *,
    spec: FeatureSpec,
    taxonomy: Taxonomy,
    config: TrainingConfig,
    variants: tuple[str, ...] = DEFAULT_VARIANTS,
) -> list[AblationRow]:
    """Cross-validate each variant, keeping failures in the table.

    A variant that raises becomes a row rather than aborting the run: while the
    feature slots are unimplemented every row fails identically, and that is
    still the right output — it shows the harness works and what is missing.
    """
    rows: list[AblationRow] = []

    for variant in variants:
        variant_config = dataclasses.replace(config, variant=variant)
        try:
            result = cross_validate(dataset, spec=spec, taxonomy=taxonomy, config=variant_config)
        except NotImplementedError as exc:
            rows.append(AblationRow.from_error(variant, len(dataset), exc))
        else:
            rows.append(AblationRow.from_result(variant, result))

    return rows
