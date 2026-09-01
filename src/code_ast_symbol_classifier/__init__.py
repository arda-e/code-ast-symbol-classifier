"""Architectural intent classification for code symbols.

The pipeline is deliberately small: hashed lexical features plus a fixed-order
numeric block from the graph and AST, fed to a logistic regression. Everything
before the classifier is deterministic feature engineering, not learning.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
