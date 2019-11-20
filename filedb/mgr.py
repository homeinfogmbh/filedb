"""General file DB record and data management."""

from filedb.exceptions import AmbiguousIdentError, NoIdentError
from filedb.orm import File


__all__ = ['get_file', 'purge', 'untrack']


def get_file(ident=None, checksum=None):
    """Gets a file by either identifier or checksum."""

    if ident is None and checksum is None:
        raise NoIdentError()

    if ident is not None:
        return File.get(File.id == ident)

    if checksum is not None:
        return File.get(File.sha256sum == checksum)

    raise AmbiguousIdentError()


def purge(ident=None, checksum=None):
    """Purges a file from the database and server."""

    file = get_file(ident=ident, checksum=checksum)
    file.remove()


def untrack(ident=None, checksum=None):
    """Removes a file from the database only."""

    file = get_file(ident=ident, checksum=checksum)
    file.delete_instance()
