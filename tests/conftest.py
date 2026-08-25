from __future__ import annotations

import json
from pathlib import Path

import pytest

from code_ast_symbol_classifier.config import FIXTURES_DIR, GOLDEN_DIR
from code_ast_symbol_classifier.data.loader import join, load_labelset, load_symbols
from code_ast_symbol_classifier.features.spec import load_feature_spec
from code_ast_symbol_classifier.taxonomy import load_taxonomy


@pytest.fixture(scope="session")
def spec():
    return load_feature_spec()


@pytest.fixture(scope="session")
def taxonomy():
    return load_taxonomy()


@pytest.fixture(scope="session")
def hash_golden() -> dict:
    return json.loads((GOLDEN_DIR / "hash-golden.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def vector_golden() -> dict:
    return json.loads((GOLDEN_DIR / "vector-golden.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def sample_symbols_path() -> Path:
    return FIXTURES_DIR / "symbols.sample.jsonl"


@pytest.fixture(scope="session")
def sample_dataset(taxonomy, sample_symbols_path):
    return join(
        load_symbols(sample_symbols_path),
        load_labelset(FIXTURES_DIR / "labels.sample.json"),
        taxonomy,
    )
