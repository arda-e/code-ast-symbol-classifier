from __future__ import annotations

import pytest

from code_ast_symbol_classifier.evaluation.thresholds import Bucket, bucket_for

ACCEPT = 0.85
TENTATIVE = 0.65


def bucket(confidence: float) -> Bucket:
    return bucket_for(confidence, accept=ACCEPT, tentative=TENTATIVE)


@pytest.mark.parametrize(
    ("confidence", "expected"),
    [
        (1.0, Bucket.ACCEPT),
        (0.85, Bucket.ACCEPT),
        (0.8499, Bucket.TENTATIVE),
        (0.65, Bucket.TENTATIVE),
        (0.6499, Bucket.UNKNOWN),
        (0.0, Bucket.UNKNOWN),
    ],
)
def test_boundaries_are_inclusive_at_the_lower_edge(confidence, expected):
    assert bucket(confidence) == expected


def test_thresholds_come_from_the_taxonomy_contract(taxonomy):
    assert taxonomy.accept_threshold == ACCEPT
    assert taxonomy.tentative_threshold == TENTATIVE
