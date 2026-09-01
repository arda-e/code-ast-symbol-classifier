"""The input record.

A symbol arrives as a row of names plus a bag of numeric facts. The model never
sees source code — not the body, not the comments, not the variable names inside
it. Callee names are the one thing taken from the body, and they arrive here
already reduced to names.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..errors import SchemaError

REQUIRED_FIELDS = ("id", "name", "filePath", "kind")


@dataclass(frozen=True)
class SymbolRecord:
    """One symbol, as the extractor emits it.

    `numeric` is an open mapping rather than fixed attributes: the numeric block
    is defined by the feature spec, so a record carrying a field the current spec
    does not know about is a version mismatch to report, not a parse error here.
    """

    id: str
    name: str
    file_path: str
    kind: str
    owner: str | None = None
    callees: tuple[str, ...] = ()
    param_types: tuple[str, ...] = ()
    return_type: str | None = None
    numeric: dict[str, float] = field(default_factory=dict)
    extractor_version: str = "unknown"

    @staticmethod
    def from_json(payload: dict[str, Any], *, source: str = "<memory>") -> SymbolRecord:
        for required in REQUIRED_FIELDS:
            if not payload.get(required):
                raise SchemaError(f"{source}: record is missing required field {required!r}")

        return SymbolRecord(
            id=payload["id"],
            name=payload["name"],
            file_path=payload["filePath"],
            kind=payload["kind"],
            owner=payload.get("owner"),
            callees=tuple(payload.get("callees") or ()),
            param_types=tuple(payload.get("paramTypes") or ()),
            return_type=payload.get("returnType"),
            numeric=_read_numeric(payload.get("numeric") or {}, source=source),
            extractor_version=payload.get("extractorVersion", "unknown"),
        )


def parse_jsonl(text: str, *, source: str) -> list[SymbolRecord]:
    records: list[SymbolRecord] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        location = f"{source}:{line_number}"
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"{location}: invalid JSON ({exc.msg})") from exc
        records.append(SymbolRecord.from_json(payload, source=location))
    return records


def _read_numeric(payload: object, *, source: str) -> dict[str, float]:
    if not isinstance(payload, dict):
        raise SchemaError(f"{source}: 'numeric' must be an object, got {type(payload).__name__}")
    try:
        return {key: float(value) for key, value in payload.items()}
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"{source}: 'numeric' holds a non-numeric value ({exc})") from exc
