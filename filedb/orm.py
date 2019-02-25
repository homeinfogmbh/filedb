"""Models for HOMEINFO's global file database."""

from contextlib import suppress
from datetime import datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryFile

from peewee import BigIntegerField
from peewee import CharField
from peewee import DateTimeField
from peewee import FixedCharField
from peewee import IntegerField
from peewee import Model

from peeweeplus import MySQLDatabase
from mimeutil import mimetype, FileMetaData

from filedb.config import CONFIG, CHUNK_SIZE


__all__ = ['File']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])
BASEDIR = Path(CONFIG['fs']['BASE_DIR'])
MODE = int(CONFIG['fs']['mode'], 8)


class FileDBModel(Model):
    """A basic model for the file database."""

    class Meta:     # pylint: disable=R0903
        """Database and schema configuration."""
        database = DATABASE
        schema = database.database


class File(FileDBModel):
    """A file entry."""

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
    def add(cls, bytes_, metadata=None):
        """Forcibly adds a file from bytes."""

        if metadata is None:
            metadata = FileMetaData.from_bytes(bytes_)

        try:
            record = cls.get(cls.sha256sum == metadata.sha256sum)
        except cls.DoesNotExist:
            record = cls()
            record.sha256sum, record.mimetype, _ = metadata
            record.size = len(bytes_)
            record.bytes = bytes_
            record.save()
        else:
            record.hardlinks += 1
            record.save()

        return record

    @classmethod
    def from_stream(cls, stream):
        """Creates a file from the respective stream."""
        sha256sum = sha256()

        with TemporaryFile('w+b') as tmp:
            for chunk in stream:
                tmp.write(chunk)
                sha256sum.update(chunk)

            sha256sum = sha256sum.hexdigest()

            try:
                return cls.get(cls.sha256sum == sha256sum)
            except cls.DoesNotExist:
                tmp.flush()
                tmp.seek(0)
                return cls._from_temporary_file(tmp, sha256sum)

    @classmethod
    def _from_temporary_file(cls, temp, sha256sum, chunk_size=CHUNK_SIZE):
        """Creates the file from a temporary file."""
        record = cls()
        record.sha256sum = sha256sum
        path = BASEDIR.joinpath(sha256sum)
        size = 0

        with path.open('wb') as file:
            for chunk in iter(partial(temp.read, chunk_size), b''):
                size += len(chunk)
                file.write(chunk)

        record.size = size
        record.mimetype = mimetype(str(path))
        record.save()
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

    @property
    def path(self):
        """Returns the file's path."""
        return BASEDIR.joinpath(self.sha256sum)

    @property
    def exists(self):
        """Checks if the file exists on the system."""
        return self.path.is_file()

    @property
    def consistent(self):
        """Checks for consistency."""
        sha256sum = sha256()

        for chunk in self.stream():
            sha256sum.update(chunk)

        return sha256sum.hexdigest() == self.sha256sum

    @property
    def bytes(self):
        """Returns the bytes of the respective file."""
        with self.path.open('rb') as file:
            return file.read()

    @bytes.setter
    def bytes(self, bytes_):
        """Returns the bytes of the respective file."""
        with self.path.open('wb') as file:
            return file.write(bytes_)

    def touch(self):
        """Update access counters."""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

    def unlink(self, force=False):
        """Unlinks / removes the file."""
        self.hardlinks += -1

        if not self.hardlinks or force:
            with suppress(FileNotFoundError):
                try:
                    self.path.unlink()
                except PermissionError:
                    return False

            return self.delete_instance()

        self.save()
        return True

    def remove(self, force=False):
        """Alias to unlink."""
        return self.unlink(force=force)

    def stream(self, chunk_size=CHUNK_SIZE):
        """Yields chunks of the specified size."""
        with self.path.open('rb') as file:
            for chunk in iter(partial(file.read, chunk_size), b''):
                yield chunk

        self.touch()
