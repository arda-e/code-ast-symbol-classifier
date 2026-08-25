"""Turning a symbol into numbers.

Nothing in this package learns anything. Splitting identifiers, namespacing them,
hashing them into buckets and assembling the numeric block are all deterministic:
the same record always produces the same vector. This is where most of the work
lives, and it is feature engineering, not machine learning.
"""
