"""The fixed-order numeric block.  [UNIMPLEMENTED SLOT]

Some facts are already numbers and must not be hashed. Degrees, flags, counters,
side-effect and mutation tallies each get a reserved position, because hashing is
only for things that are unbounded — identifiers.

Giving the model `outDegree = 4` directly, rather than leaving it to infer the
count from a comma-separated list of callee names, is the whole argument for this
block: the counting work is already done, in its own position, with its own
weight.

The order of `spec.numeric_fields` is the contract. A shifted order multiplies
`comparisonCount` by `paramCount`'s weight, raises nothing, and costs accuracy
that is very hard to trace back.
"""

from __future__ import annotations

from ..data.records import SymbolRecord
from .spec import NumericField


def numeric_vector(record: SymbolRecord, fields: tuple[NumericField, ...]) -> list[float]:
    """Read the record's numeric facts out in exactly `fields` order.

    A field the record does not carry is 0.0 — absence and zero are the same
    thing for every field in the current spec, except `entrypointDistance`,
    whose "unreachable" value is -1 (see the spec's field description).
    """
    raise NotImplementedError("see contracts/feature-spec.v1.json -> numeric.fields")
