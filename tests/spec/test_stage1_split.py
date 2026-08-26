"""STAGE 1 — split an identifier into words.

    uv run pytest tests/spec/test_stage1_split.py

You are writing `split_identifier` in `features/lexical.py`. It takes one
identifier and returns lowercase words:

    placeOrder  ->  ["place", "order"]

That is the whole stage. It is first because everything else is built on it, and
because it needs no machine learning at all — it is string handling.

WHY IT MATTERS. Left whole, `placeOrder` becomes its own isolated feature. It
would share nothing with `placeBid`, `cancelOrder` or `orderTotal`, so the model
could only ever recognise names it had already seen, and would learn nothing it
could apply to a name it had not. Splitting is what makes generalisation
possible.

READ FIRST: `contracts/feature-spec.v1.json` -> `lexical.tokenization`.

DONE WHEN: the nine tests below pass. Then move to stage 2.
"""

from __future__ import annotations

import pytest

from code_ast_symbol_classifier.features.lexical import split_identifier

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
    """Consistent casing keeps `Order` and `order` in the same bucket."""
    assert all(token.islower() for token in split_identifier("HTTPServerFactory"))
