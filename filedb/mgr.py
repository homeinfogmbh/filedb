"""General file DB record and data management"""

from os import unlink

from filedb.db import File


class NoIdentError():
    """Indicates a lack of identifier"""
    pass


class AmbiguousIdentError():
    """Indicates ambiguous identifiers"""
    pass


class FileManager():
    """File management utility"""

    def __init__(self, interactive=False):
        """Sets the interactive flag"""
        self.interactive = interactive

    def _get_file(self, ident=None, checksum=None):
        """Gets a file by either identifier or checksum"""
        if ident is None and checksum is None:
            raise NoIdentError()
        elif ident is not None:
            f = File.get(File.id == ident)
        elif checksum is not None:
            f = File.get(File.sha256sum == checksum)
        else:
            raise AmbiguousIdentError()

        return f

    def purge(self, ident=None, checksum=None):
        """Purges a file from the database and server"""
        f = self._get_file(ident=ident, checksum=checksum)
        unlink(f.path)
        f.delete_record()

    def untrack(self, ident=None, checksum=None):
        """Removes a file from the database only"""
        f = self._get_file(ident=ident, checksum=checksum)
        f.delete_record()
