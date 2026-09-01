"""Regenerate the golden fixtures from the feature spec.

The fixtures are derived from the CONTRACT, never from the feature code — that is
what makes them a test rather than a snapshot of current behaviour. The expected
lexical features below are written out by hand from the spec's tokenisation rules;
only the bucket arithmetic is computed.

Run after any change to the hash config or the numeric field list, and commit the
result alongside the new featureVersion:

    uv run python scripts/generate_golden.py
"""

from __future__ import annotations

import json
from pathlib import Path

from code_ast_symbol_classifier.config import GOLDEN_DIR
from code_ast_symbol_classifier.features.hashing import hash_bucket
from code_ast_symbol_classifier.features.spec import load_feature_spec

# Chosen to cover every namespace plus the cases most likely to diverge between
# two implementations: digits, a single character, a long string, a non-ASCII
# identifier (UTF-8 encoding), and a string whose signed hash is negative.
HASH_INPUTS = [
    "name:place",
    "name:order",
    "name:validate",
    "name:is",
    "name:x",
    "name:handler2",
    "owner:order",
    "owner:service",
    "owner:controller",
    "path:src",
    "path:orders",
    "path:service",
    "callee:order",
    "callee:factory",
    "callee:create",
    "callee:inventory",
    "callee:reserve",
    "callee:payment",
    "callee:charge",
    "callee:repository",
    "callee:save",
    "callee:validate",
    "accepts:create",
    "accepts:order",
    "accepts:dto",
    "returns:order",
    "returns:boolean",
    "returns:void",
    "name:sipariş",
    "name:ödeme",
    "name:averyveryverylongidentifiertokenthatkeepsgoingandgoing",
]

GOLDEN_RECORD = {
    "id": "src/orders/order.service.ts#OrderService.placeOrder",
    "name": "placeOrder",
    "owner": "OrderService",
    "filePath": "src/orders/order.service.ts",
    "kind": "method",
    "callees": [
        "this.orderFactory.create",
        "this.inventory.reserve",
        "this.payment.charge",
        "this.repository.save",
    ],
    "paramTypes": ["CreateOrderDto"],
    "returnType": "Promise<Order>",
    "numeric": {
        "outDegree": 4,
        "inDegree": 3,
        "distinctCallees": 4,
        "distinctCallers": 3,
        "entrypointDistance": 1,
        "isAsync": 1,
        "isExported": 1,
        "isMethod": 1,
        "paramCount": 1,
        "statementCount": 5,
        "lineCount": 7,
        "awaitCount": 4,
        "returnCount": 1,
        "sideEffect_database_write": 1,
    },
    "extractorVersion": "v1",
}

EXPECTED_LEXICAL = [
    "name:place",
    "name:order",
    "owner:order",
    "owner:service",
    "path:src",
    "path:orders",
    "path:order",
    "path:service",
    "callee:order",
    "callee:factory",
    "callee:create",
    "callee:inventory",
    "callee:reserve",
    "callee:payment",
    "callee:charge",
    "callee:repository",
    "callee:save",
    "accepts:create",
    "accepts:order",
    "accepts:dto",
    "returns:order",
]


def main() -> None:
    spec = load_feature_spec()
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    hash_golden = {
        "featureVersion": spec.version,
        "hash": {
            "algorithm": spec.hash.algorithm,
            "seed": spec.hash.seed,
            "buckets": spec.hash.buckets,
            "signed": spec.hash.signed,
            "encoding": spec.hash.encoding,
        },
        "note": (
            "input string -> expected bucket index. Both the Python trainer and any "
            "TypeScript inference port must reproduce every row exactly. A mismatch "
            "raises nothing at runtime; it only makes the model quietly worse."
        ),
        "cases": [
            {"input": value, "bucket": hash_bucket(value, spec.hash)} for value in HASH_INPUTS
        ],
    }
    _write(GOLDEN_DIR / "hash-golden.json", hash_golden)

    numeric_values = [
        float(GOLDEN_RECORD["numeric"].get(field.name, 0.0)) for field in spec.numeric_fields
    ]
    vector_golden = {
        "featureVersion": spec.version,
        "note": (
            "One symbol, fully worked out. `expectedLexicalFeatures` comes from the "
            "spec's tokenisation rules by hand; `expectedBuckets` is their hash. "
            "`expectedNumericValues` is the numeric block in contract order, unscaled."
        ),
        "record": GOLDEN_RECORD,
        "expectedLexicalFeatures": EXPECTED_LEXICAL,
        "expectedBuckets": sorted({hash_bucket(f, spec.hash) for f in EXPECTED_LEXICAL}),
        "numericFieldOrder": list(spec.numeric_names),
        "expectedNumericValues": numeric_values,
    }
    _write(GOLDEN_DIR / "vector-golden.json", vector_golden)


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(path.parents[2])}")


if __name__ == "__main__":
    main()
