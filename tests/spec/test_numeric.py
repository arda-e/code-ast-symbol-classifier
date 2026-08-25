"""Specification for features/numeric.py — expected to fail until it is written."""

from __future__ import annotations

import pytest

from code_ast_symbol_classifier.data.records import SymbolRecord
from code_ast_symbol_classifier.features.numeric import numeric_vector

pytestmark = pytest.mark.spec


def test_golden_symbol_produces_the_expected_block(spec, vector_golden):
    record = SymbolRecord.from_json(vector_golden["record"])

    assert numeric_vector(record, spec.numeric_fields) == pytest.approx(
        vector_golden["expectedNumericValues"]
    )


def test_block_length_matches_the_contract(spec, vector_golden):
    record = SymbolRecord.from_json(vector_golden["record"])

    assert len(numeric_vector(record, spec.numeric_fields)) == len(spec.numeric_fields)


def test_values_follow_contract_order_not_record_order(spec):
    """The failure mode this guards is silent.

    A shifted order multiplies `comparisonCount` by `paramCount`'s weight,
    raises nothing, and costs accuracy nobody can trace back.
    """
    record = SymbolRecord(
        id="a.ts#f",
        name="f",
        file_path="a.ts",
        kind="function",
        numeric={"paramCount": 7.0, "outDegree": 3.0},
    )
    values = numeric_vector(record, spec.numeric_fields)
    position = {field.name: i for i, field in enumerate(spec.numeric_fields)}

    assert values[position["outDegree"]] == 3.0
    assert values[position["paramCount"]] == 7.0


def test_absent_fields_become_zero(spec):
    record = SymbolRecord(id="a.ts#f", name="f", file_path="a.ts", kind="function")

    assert numeric_vector(record, spec.numeric_fields) == [0.0] * len(spec.numeric_fields)


def test_a_subset_of_fields_yields_a_shorter_block(spec):
    """How the ablation variants drop a group without disturbing the rest."""
    record = SymbolRecord(
        id="a.ts#f", name="f", file_path="a.ts", kind="function", numeric={"inDegree": 4.0}
    )
    degrees = spec.fields_in_groups(("degree",))
    values = numeric_vector(record, degrees)

    assert len(values) == len(degrees)
    assert values[[f.name for f in degrees].index("inDegree")] == 4.0
