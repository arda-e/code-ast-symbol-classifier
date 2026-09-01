"""STAGE 3 — lay the numeric facts out in a fixed order.

    uv run pytest tests/spec/test_stage3_numeric.py

You are writing `numeric_vector` in `features/numeric.py`. It reads a record's
numeric facts out as a list, in the order the contract gives — no more.

WHY THESE ARE NOT HASHED. Stage 2 hashed identifiers because there are endlessly
many of them. Numeric facts are a closed set: there are exactly as many
side-effect kinds as the parser defines. Closed sets get reserved positions, so
`outDegree` always lands in slot 0 and always carries its own weight.

The alternative is worth picturing. Handed `calls: create, reserve, charge, save`
as text, a model would have to work out that commas separate things, count them,
and connect that count to the idea of a degree — all learned from a couple of
hundred examples with no feedback except the final label. Handed `outDegree = 4`,
the counting is already done.

WHY ORDER IS A CONTRACT. Swap two positions and `comparisonCount` gets
multiplied by `paramCount`'s weight. Nothing raises. The model just scores worse,
and the cause is nearly impossible to find later. The same list has to be read
identically by a future TypeScript port, which is why it lives in a file rather
than in code.

READ FIRST: `contracts/feature-spec.v1.json` -> `numeric`. There are 67 fields.

DONE WHEN: the five tests below pass.
"""

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
    """The failure this guards is silent."""
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
    """Most fields are absent for most symbols; that is normal, not an error."""
    record = SymbolRecord(id="a.ts#f", name="f", file_path="a.ts", kind="function")

    assert numeric_vector(record, spec.numeric_fields) == [0.0] * len(spec.numeric_fields)


def test_a_subset_of_fields_yields_a_shorter_block(spec):
    """How stage 4 drops a group without disturbing the rest."""
    record = SymbolRecord(
        id="a.ts#f", name="f", file_path="a.ts", kind="function", numeric={"inDegree": 4.0}
    )
    degrees = spec.fields_in_groups(("degree",))
    values = numeric_vector(record, degrees)

    assert len(values) == len(degrees)
    assert values[[f.name for f in degrees].index("inDegree")] == 4.0
