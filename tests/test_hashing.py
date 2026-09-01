"""The parity contract.

Every case in the golden fixture has to reproduce exactly. When a TypeScript
inference port is written, it reads the same file and must produce the same
numbers — that shared fixture is the only thing standing between a silent
mismatch and a model that quietly scores worse for reasons nobody can trace.
"""

from __future__ import annotations

import mmh3
import pytest

from code_ast_symbol_classifier.features.hashing import hash_bucket


def test_golden_cases_reproduce(spec, hash_golden):
    for case in hash_golden["cases"]:
        assert hash_bucket(case["input"], spec.hash) == case["bucket"], case["input"]


def test_golden_covers_every_namespace(spec, hash_golden):
    prefixes = {case["input"].split(":", 1)[0] for case in hash_golden["cases"]}
    assert set(spec.namespaces) <= prefixes


def test_golden_matches_current_hash_config(spec, hash_golden):
    """A regenerated fixture and a changed spec must move together."""
    assert hash_golden["hash"]["seed"] == spec.hash.seed
    assert hash_golden["hash"]["buckets"] == spec.hash.buckets
    assert hash_golden["featureVersion"] == spec.version


def test_buckets_stay_in_range(spec, hash_golden):
    assert all(0 <= case["bucket"] < spec.hash.buckets for case in hash_golden["cases"])


def test_unsigned_hashing_is_what_the_contract_means(spec):
    """Pins the trap rather than the happy path.

    mmh3 returns a signed int32 by default, and `%` on a negative differs between
    Python and JavaScript. A port that forgets this gets a different bucket for
    the same token, with no error anywhere.
    """
    signed_negative = next(
        value
        for value in (f"name:token{i}" for i in range(100))
        if mmh3.hash(value.encode("utf-8"), spec.hash.seed, signed=True) < 0
    )

    signed = mmh3.hash(signed_negative.encode("utf-8"), spec.hash.seed, signed=True)
    unsigned = mmh3.hash(signed_negative.encode("utf-8"), spec.hash.seed, signed=False)

    assert signed != unsigned
    assert hash_bucket(signed_negative, spec.hash) == unsigned % spec.hash.buckets


def test_non_ascii_input_hashes_as_utf8(spec):
    value = "name:sipariş"
    assert hash_bucket(value, spec.hash) == (
        mmh3.hash(value.encode("utf-8"), spec.hash.seed, signed=False) % spec.hash.buckets
    )


@pytest.mark.parametrize("value", ["name:place", "callee:save", "path:src"])
def test_hashing_is_stable_across_calls(spec, value):
    assert hash_bucket(value, spec.hash) == hash_bucket(value, spec.hash)
