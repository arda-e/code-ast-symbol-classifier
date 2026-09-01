from __future__ import annotations

import json

import pytest

from code_ast_symbol_classifier.errors import FeatureSpecError
from code_ast_symbol_classifier.features.spec import load_feature_spec


def test_vector_size_is_buckets_plus_numeric(spec):
    assert spec.vector_size == spec.hash.buckets + len(spec.numeric_fields)


def test_numeric_field_names_are_unique(spec):
    assert len(set(spec.numeric_names)) == len(spec.numeric_names)


def test_degree_fields_are_the_graph_global_ones(spec):
    """Guards the split the ablation depends on.

    Only degrees need the whole graph. If a file-local counter is ever marked
    post-graph, the B-local / B-global comparison stops answering whether
    classification can run incrementally.
    """
    global_fields = {field.name for field in spec.numeric_fields if field.is_graph_global}
    degree_fields = {field.name for field in spec.numeric_fields if field.group == "degree"}
    assert global_fields == degree_fields


def test_variants_partition_the_numeric_groups(spec):
    local = set(spec.variant("B-local").numeric_groups)
    graph_global = set(spec.variant("B-global").numeric_groups)
    everything = set(spec.variant("C").numeric_groups)

    assert not local & graph_global
    assert local | graph_global == everything


def test_variant_a_is_lexical_only(spec):
    variant = spec.variant("A")
    assert variant.use_lexical
    assert variant.numeric_groups == ()


def test_unknown_variant_is_rejected(spec):
    with pytest.raises(FeatureSpecError, match="unknown ablation variant"):
        spec.variant("Z")


def test_unsupported_hash_algorithm_is_rejected(tmp_path):
    raw = {
        "featureVersion": "test",
        "hash": {
            "algorithm": "murmur3_x64_128",
            "seed": 0,
            "buckets": 16,
            "signed": False,
            "encoding": "utf-8",
            "occurrence": "binary",
        },
        "lexical": {"namespaces": [{"prefix": "name"}]},
        "numeric": {"fields": []},
        "ablationVariants": {},
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(FeatureSpecError, match="unsupported hash algorithm"):
        load_feature_spec(path)
