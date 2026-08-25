from __future__ import annotations

import pytest

from code_ast_symbol_classifier.data.records import SymbolRecord, parse_jsonl
from code_ast_symbol_classifier.errors import SchemaError

VALID = '{"id":"a.ts#f","name":"f","filePath":"a.ts","kind":"function"}'


def test_parses_a_minimal_record():
    record = parse_jsonl(VALID, source="test")[0]
    assert record.id == "a.ts#f"
    assert record.callees == ()
    assert record.numeric == {}


def test_blank_lines_are_skipped():
    assert len(parse_jsonl(f"\n{VALID}\n\n{VALID}\n", source="test")) == 2


def test_invalid_json_names_the_line():
    with pytest.raises(SchemaError, match="test:2"):
        parse_jsonl(f"{VALID}\nnot json\n", source="test")


@pytest.mark.parametrize("missing", ["id", "name", "filePath", "kind"])
def test_missing_required_field_is_rejected(missing):
    payload = {"id": "a.ts#f", "name": "f", "filePath": "a.ts", "kind": "function"}
    del payload[missing]

    with pytest.raises(SchemaError, match=missing):
        SymbolRecord.from_json(payload)


def test_non_numeric_value_in_numeric_block_is_rejected():
    payload = {
        "id": "a.ts#f",
        "name": "f",
        "filePath": "a.ts",
        "kind": "function",
        "numeric": {"outDegree": "four"},
    }
    with pytest.raises(SchemaError, match="non-numeric"):
        SymbolRecord.from_json(payload)


def test_numeric_block_must_be_an_object():
    payload = {
        "id": "a.ts#f",
        "name": "f",
        "filePath": "a.ts",
        "kind": "function",
        "numeric": [1, 2, 3],
    }
    with pytest.raises(SchemaError, match="must be an object"):
        SymbolRecord.from_json(payload)
