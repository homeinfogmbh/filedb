"""Common exceptions."""


__all__ = ['AmbiguousIdentError', 'NoIdentError']


class AmbiguousIdentError(Exception):
    """Indicates ambiguous identifiers."""


class NoIdentError(Exception):
    """Indicates a lack of identifier."""
