from __future__ import annotations

from code_ast_symbol_classifier.config import TrainingConfig
from code_ast_symbol_classifier.experiments.ablation import DEFAULT_VARIANTS, run_ablation
from code_ast_symbol_classifier.experiments.row import AblationRow
from code_ast_symbol_classifier.experiments.table import render


def test_every_requested_variant_produces_a_row(sample_dataset, spec, taxonomy):
    rows = run_ablation(
        sample_dataset,
        spec=spec,
        taxonomy=taxonomy,
        config=TrainingConfig(),
        variants=DEFAULT_VARIANTS,
    )

    assert [row.variant for row in rows] == list(DEFAULT_VARIANTS)


def test_a_failing_variant_stays_in_the_table(sample_dataset, spec, taxonomy):
    """The harness reports what it could not run instead of aborting.

    While the feature slots are unimplemented every variant fails the same way,
    and the table saying so is still the correct output.
    """
    rows = run_ablation(
        sample_dataset, spec=spec, taxonomy=taxonomy, config=TrainingConfig(), variants=("A",)
    )
    assert len(rows) == 1


def test_error_rows_render_without_numbers():
    row = AblationRow.from_error("A", 42, NotImplementedError("slot is empty"))
    table = render([row])

    assert "error: slot is empty" in table
    assert "| A |" in table


def test_table_has_a_header_row():
    assert render([]).splitlines()[0].startswith("| variant |")
