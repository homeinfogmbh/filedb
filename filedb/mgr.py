"""General file DB record and data management."""

from filedb.exceptions import AmbiguousIdentError, NoIdentError
from filedb.orm import File


__all__ = ['get_file', 'purge', 'untrack']


def get_file(ident: int = None, checksum: str = None) -> File:
    """Gets a file by either identifier or checksum."""

    if ident is not None and checksum is not None:
        raise AmbiguousIdentError()

    if ident is not None:
        return File[ident]

    if checksum is not None:
        return File.by_sha256sum(checksum)

    raise NoIdentError()


def purge(ident: int = None, checksum: str = None):
    """Purges a file from the database and file system."""

    file = get_file(ident=ident, checksum=checksum)
    file.unlink(force=True)


def untrack(ident: int = None, checksum: str = None):
    """Removes a file from the database only."""

    file = get_file(ident=ident, checksum=checksum)
    file.delete_instance()
