"""General file DB record and data management"""

from filedb.orm import File

__all__ = [
    'NoIdentError',
    'AmbiguousIdentError',
    'get_file',
    'purge',
    'untrack']


class NoIdentError(Exception):
    """Indicates a lack of identifier."""

    pass


class AmbiguousIdentError(Exception):
    """Indicates ambiguous identifiers."""

    pass


def get_file(ident=None, checksum=None):
    """Gets a file by either identifier or checksum."""
    if ident is None and checksum is None:
        raise NoIdentError()
    elif ident is not None:
        return File.get(File.id == ident)
    elif checksum is not None:
        return File.get(File.sha256sum == checksum)
    else:
        raise AmbiguousIdentError()


def purge(ident=None, checksum=None):
    """Purges a file from the database and server."""

    file = get_file(ident=ident, checksum=checksum)
    file.path.unlink()
    file.delete_record()


def untrack(ident=None, checksum=None):
    """Removes a file from the database only."""

    file = get_file(ident=ident, checksum=checksum)
    file.delete_record()
