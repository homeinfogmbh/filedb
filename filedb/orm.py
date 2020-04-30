"""Models for HOMEINFO's global file database."""

from datetime import datetime
from functools import partial
from hashlib import sha256
from tempfile import NamedTemporaryFile

from peewee import OperationalError
from peewee import BigIntegerField
from peewee import BlobField
from peewee import CharField
from peewee import DateTimeField
from peewee import FixedCharField
from peewee import IntegerField

from peeweeplus import JSONModel, MySQLDatabase
from mimeutil import mimetype

from filedb.config import CONFIG, CHUNK_SIZE


__all__ = ['File']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])
MODE = int(CONFIG['fs']['mode'], 8)


class FileDBModel(JSONModel):
    """A basic model for the file database."""

    class Meta:     # pylint: disable=R0903
        """Database and schema configuration."""
        database = DATABASE
        schema = database.database


class File(FileDBModel):
    """A file entry."""

    bytes = BlobField()
    mimetype = CharField(255)
    sha256sum = FixedCharField(64)
    size = BigIntegerField()   # File size in bytes.
    hardlinks = IntegerField(default=1)
    created = DateTimeField(default=datetime.now)
    last_access = DateTimeField(null=True, default=None)
    accessed = IntegerField(default=0)

    def __str__(self):
        """Converts the file to a string."""
        return str(self.sha256sum)

    @classmethod
    def _from_temporary_file(cls, temp, sha256sum, mime_type, chunk_size):
        """Creates the file from a temporary file."""
        record = cls()
        record.sha256sum = sha256sum
        record.bytes = b''
        record.size = 0

        for chunk in iter(partial(temp.read, chunk_size), b''):
            record.bytes += chunk
            record.size += len(chunk)

        record.mimetype = mime_type
        return record

    @classmethod
    def from_stream(cls, stream, chunk_size=CHUNK_SIZE):
        """Creates a file from the respective stream."""
        sha256sum = sha256()

        with NamedTemporaryFile('w+b') as tmp:
            for chunk in stream:
                tmp.write(chunk)
                sha256sum.update(chunk)

            sha256sum = sha256sum.hexdigest()

            try:
                record = cls.get(cls.sha256sum == sha256sum)
            except cls.DoesNotExist:
                tmp.flush()
                tmp.seek(0)
                return cls._from_temporary_file(
                    tmp, sha256sum, mimetype(tmp.name), chunk_size)

            record.hardlinks += 1
            return record

    @classmethod
    def purge(cls, orphans):
        """Purge orphans from the filedb."""
        for orphan in orphans:
            try:
                record = cls.get(cls.id == orphan)
            except cls.DoesNotExist:
                continue

            record.unlink(force=True)

    @classmethod
    def update_hardlinks(cls, references):
        """Fixes the hard links to the given reference dictionary."""
        for ident, hardlinks in references.items():
            try:
                record = cls.get(cls.id == ident)
            except cls.DoesNotExist:
                continue

            record.hardlinks = hardlinks
            record.save()

    def load_from_fs(self):
        """Import file from file system."""
        if self.bytes:
            return True

        path = f'/srv/filedb/{self.sha256sum}'

        try:
            with open(path, 'rb') as file:
                self.bytes = file.read()
        except FileNotFoundError:
            print('No such file:', path, flush=True)
        except PermissionError:
            print('Permission error reading:', path, flush=True)

        try:
            return self.save()
        except OperationalError:
            print('Operational error. File:', self.id, 'id:', self.id,
                  flush=True)
            raise

    def touch(self):
        """Update access counters."""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

    def unlink(self, force=False):
        """Unlinks / removes the file."""
        self.hardlinks += -1

        if not self.hardlinks or force:
            return self.delete_instance()

        self.save()
        return True

    remove = unlink

    def get_chunk(self, start=None, end=None):
        """Returns the respective chunk."""
        if start >= self.size:
            start = 0

        if end:
            chunk = self.bytes[start:end]
            length = end - start + 1
        else:
            chunk = self.bytes[start:]
            length = self.size - start

        return (chunk, start, length)
