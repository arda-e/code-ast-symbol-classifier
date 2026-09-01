"""The hash contract, alone in its own module.

This is the smallest piece of the project and the easiest to break silently. A
TypeScript port that gets any one of these knobs wrong produces a model that
still runs, still returns confident answers, and is quietly worse — so the
function lives by itself, pinned by `contracts/fixtures/hash-golden.json`.
"""

from __future__ import annotations

from dataclasses import dataclass

import mmh3


@dataclass(frozen=True)
class HashConfig:
    algorithm: str
    seed: int
    buckets: int
    signed: bool
    encoding: str
    occurrence: str


def hash_bucket(feature_string: str, config: HashConfig) -> int:
    """Map a feature string onto a fixed-size bucket index.

    Hashing is not used to give a word meaning — it maps an unbounded set of
    identifiers into a fixed feature space, so no vocabulary has to be built,
    stored, versioned and carried across two languages.

    `signed=False` is not a detail: mmh3 otherwise returns a signed int32, and
    `%` on a negative number behaves differently in Python and JavaScript. That
    one difference sends the same token to two different buckets.
    """
    encoded = feature_string.encode(config.encoding)
    return mmh3.hash(encoded, config.seed, signed=False) % config.buckets
