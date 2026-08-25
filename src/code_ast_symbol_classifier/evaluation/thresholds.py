"""Turning a confidence into a decision.

Three buckets: take the answer, flag it for a human, or throw it away. Leaving a
symbol unlabelled is cheaper than labelling it wrongly — a wrong architectural
role propagates into every query that trusts the graph.
"""

from __future__ import annotations

from enum import StrEnum


class Bucket(StrEnum):
    ACCEPT = "accept"
    TENTATIVE = "tentative"
    UNKNOWN = "unknown"


def bucket_for(confidence: float, *, accept: float, tentative: float) -> Bucket:
    """Classify a confidence into its bucket. Boundaries are inclusive."""
    if confidence >= accept:
        return Bucket.ACCEPT
    if confidence >= tentative:
        return Bucket.TENTATIVE
    return Bucket.UNKNOWN
