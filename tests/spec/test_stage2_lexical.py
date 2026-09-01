"""STAGE 2 — label each word with where it came from.

    uv run pytest tests/spec/test_stage2_lexical.py

You are writing `lexical_features` in `features/lexical.py`. It takes a whole
symbol and returns strings that carry both a word and its source:

    name:place       the symbol's own name contains "place"
    callee:save      the symbol calls something containing "save"
    path:service     it lives in a file whose name contains "service"

WHY THE PREFIX MATTERS. This is the one idea in the stage, and it is easy to
skip past. Consider two symbols:

    a function NAMED validate         -> probably a validator
    a function that CALLS validate    -> does not validate; it delegates

Same word, opposite conclusions. Drop the prefix and both become the feature
`validate`; the model sees one signal where there were two and can never learn
the difference. The prefix keeps them apart.

Same reasoning for keeping the receiver in a call: `save` appears in every
codebase and separates nothing, while `repository.save` says a great deal.

READ FIRST: `contracts/feature-spec.v1.json` -> `lexical.namespaces`, and
`contracts/fixtures/vector-golden.json`, which contains one symbol worked out
completely — the 21 strings your function has to produce for it.

DONE WHEN: the six tests below pass. `make explain` then shows real output for
the first time.
"""

from __future__ import annotations

import pytest

from code_ast_symbol_classifier.data.records import SymbolRecord
from code_ast_symbol_classifier.features.lexical import lexical_features

pytestmark = pytest.mark.spec


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


def test_the_same_word_from_two_sources_stays_distinguishable(spec):
    """Why the namespace prefix exists at all."""
    named = SymbolRecord(id="a#1", name="validate", file_path="a.ts", kind="function")
    calling = SymbolRecord(
        id="a#2", name="run", file_path="a.ts", kind="function", callees=("validate",)
    )

    assert "name:validate" in lexical_features(named, spec)
    assert "name:validate" not in lexical_features(calling, spec)
    assert "callee:validate" in lexical_features(calling, spec)


def test_callee_receiver_is_kept_but_this_is_dropped(spec):
    """`repository.save` separates classes; `save` alone appears everywhere.

    `this` is dropped because it sits on nearly every method call, so it splits
    nothing while taking up a bucket.
    """
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


def test_file_name_contributes_path_tokens(spec):
    """`*.service.ts`-style suffixes are among the strongest signals a TS repo gives."""
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
    """`Promise` is how the code is written, not what it returns."""
    record = SymbolRecord(
        id="a.ts#f", name="f", file_path="a.ts", kind="function", return_type="Promise<Order>"
    )
    features = lexical_features(record, spec)

    assert "returns:order" in features
    assert "returns:promise" not in features
