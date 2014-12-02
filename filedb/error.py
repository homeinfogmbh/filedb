"""
Abstract base classes for HOMEINFO's file database
"""
__date__ = '02.12.2014'
__author__ = 'Richard Neumann <r.neumann@homeinfo.de>'
__all__ = ['ChecksumMismatch', 'FilesizeMismatch']


class MismatchError(Exception):
    """Indicates inconsistency between actual and target values"""
    def __init__(self, actual_value, target_value):
        """Sets acual and target value"""
        self._actual_value = actual_value
        self._target_value = target_value

    @property
    def actual_value(self):
        """Returns the actual value"""
        return self._actual_value

    @property
    def target_value(self):
        """Returns the target value"""
        return self._target_value

    def __str__(self):
        """Converts to a string"""
        return '\n'.join(['File checksums do not match',
                          ' '.join(['    actual:', str(self.actual_value)]),
                          ' '.join(['    target:', str(self.target_value)])])


class ChecksumMismatch(MismatchError):
    """Indicates inconsistency between file checksums"""
    pass


class FilesizeMismatch(MismatchError):
    """Indicates inconsistency between file checksums"""
    pass
