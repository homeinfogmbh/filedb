"""Common exceptions."""


__all__ = ['AmbiguousIdentError', 'NoIdentError', 'FileError']


class AmbiguousIdentError(Exception):
    """Indicates ambiguous identifiers."""


class NoIdentError(Exception):
    """Indicates a lack of identifier."""


class FileError(Exception):
    """Indicates errors while accessing files."""

    def __init__(self, result):
        """Sets the request result."""
        super().__init__(result)
        self.result = result
