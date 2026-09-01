"""Every error this package raises, in one hierarchy.

Callers that only want to distinguish "our problem" from "someone else's" catch
`ClassifierError`; the specific types exist so a CLI or a test can say which
contract was broken.
"""

from __future__ import annotations


class ClassifierError(Exception):
    """Base for every error raised by this package."""


class TaxonomyError(ClassifierError, ValueError):
    """The taxonomy file is malformed, or a label is not part of it."""


class SchemaError(ClassifierError, ValueError):
    """An input record or label set does not match its contract."""


class FeatureSpecError(ClassifierError, ValueError):
    """The feature spec is malformed, or a record disagrees with it."""


class ArtifactError(ClassifierError, ValueError):
    """A model artifact is malformed, or was trained against other contracts."""
