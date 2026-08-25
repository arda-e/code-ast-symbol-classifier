"""Identifier tokens, namespaced and hashed.  [UNIMPLEMENTED SLOT]

What this has to do, per `contracts/feature-spec.v1.json` -> `lexical`:

    placeOrder                      -> ["place", "order"]
    isEligibleForDiscount           -> ["is", "eligible", "for", "discount"]
    this.orderFactory.create        -> ["order", "factory", "create"]

then prefix each token with the namespace it came from, producing strings like
`name:place`, `owner:service`, `callee:repository`, `returns:order`.

Two decisions are already made and are not yours to change:

* **Splitting is mandatory.** Left whole, `placeOrder` shares no signal with
  `placeBid` or `cancelOrder`, and the model can only recognise names it has
  already seen.
* **The namespace prefix carries meaning.** `name:validate` (this symbol
  validates) and `callee:validate` (this symbol calls something that validates)
  point at different classes. Without the prefix both land in one bucket and the
  difference becomes unlearnable.

For callees, take the whole expression including the receiver. `save` appears
everywhere; `repository.save` does not — the receiver is often the stronger
signal.

`tests/test_vector_layout.py` holds the golden fixture this must reproduce.
"""

from __future__ import annotations

from ..data.records import SymbolRecord
from .spec import FeatureSpec


def split_identifier(identifier: str) -> list[str]:
    """Split camelCase, PascalCase, snake_case, kebab-case and dotted paths.

    Returns lowercase tokens, in source order, with empty tokens dropped.
    """
    raise NotImplementedError("see contracts/feature-spec.v1.json -> lexical.tokenization")


def lexical_features(record: SymbolRecord, spec: FeatureSpec) -> list[str]:
    """Produce the namespaced feature strings for one symbol.

    Order does not matter — these become set membership in a bucket vector — but
    the strings themselves must match the contract exactly, because they are
    hashed and a single character changes the bucket.
    """
    raise NotImplementedError("see contracts/feature-spec.v1.json -> lexical.namespaces")
