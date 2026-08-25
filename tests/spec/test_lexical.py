"""Specification for features/lexical.py — expected to fail until it is written.

Marked `spec` so CI can stay blocking on everything else. Run just these with:

    uv run pytest -m spec
"""

from __future__ import annotations

import pytest

from code_ast_symbol_classifier.data.records import SymbolRecord
from code_ast_symbol_classifier.features.lexical import lexical_features, split_identifier

pytestmark = pytest.mark.spec


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("placeOrder", ["place", "order"]),
        ("CreateOrderDto", ["create", "order", "dto"]),
        ("isEligibleForDiscount", ["is", "eligible", "for", "discount"]),
        ("read_env_settings", ["read", "env", "settings"]),
        ("order-service", ["order", "service"]),
        ("order.service", ["order", "service"]),
        ("chunk", ["chunk"]),
        ("", []),
    ],
)
def test_split_identifier(identifier, expected):
    assert split_identifier(identifier) == expected


def test_split_lowercases_every_token():
    assert all(token.islower() for token in split_identifier("HTTPServerFactory"))


def test_golden_symbol_produces_the_expected_features(spec, vector_golden):
    """The whole contract for this module, in one case."""
    record = SymbolRecord.from_json(vector_golden["record"])

    assert sorted(lexical_features(record, spec)) == sorted(
        vector_golden["expectedLexicalFeatures"]
    )


def test_every_feature_string_is_namespaced(spec, vector_golden):
    record = SymbolRecord.from_json(vector_golden["record"])

    for feature in lexical_features(record, spec):
        prefix, _, token = feature.partition(":")
        assert prefix in spec.namespaces
        assert token


def test_callee_receiver_is_kept_but_this_is_dropped(spec):
    """`repository.save` separates classes; `save` alone appears everywhere."""
    record = SymbolRecord(
        id="a.ts#f",
        name="f",
        file_path="a.ts",
        kind="method",
        callees=("this.repository.save",),
    )
    features = lexical_features(record, spec)

    assert "callee:repository" in features
    assert "callee:save" in features
    assert "callee:this" not in features


def test_the_same_word_from_two_sources_stays_distinguishable(spec):
    """Why the namespace prefix exists at all.

    A symbol named `validate` and a symbol that calls something named `validate`
    point at different classes. Without the prefix both collapse into one bucket
    and the difference becomes unlearnable.
    """
    named = SymbolRecord(id="a#1", name="validate", file_path="a.ts", kind="function")
    calling = SymbolRecord(
        id="a#2", name="run", file_path="a.ts", kind="function", callees=("validate",)
    )

    assert "name:validate" in lexical_features(named, spec)
    assert "name:validate" not in lexical_features(calling, spec)
    assert "callee:validate" in lexical_features(calling, spec)


def test_file_name_contributes_path_tokens(spec):
    """`*.service.ts`-style suffixes are among the strongest naming signals."""
    record = SymbolRecord(
        id="src/orders/order.service.ts#f",
        name="f",
        file_path="src/orders/order.service.ts",
        kind="method",
    )
    features = lexical_features(record, spec)

    assert "path:service" in features
    assert "path:ts" not in features


def test_return_type_generics_are_unwrapped(spec):
    record = SymbolRecord(
        id="a.ts#f", name="f", file_path="a.ts", kind="function", return_type="Promise<Order>"
    )
    features = lexical_features(record, spec)

    assert "returns:order" in features
    assert "returns:promise" not in features
