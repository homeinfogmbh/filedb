"""Models for HOMEINFO's global file database."""

from datetime import datetime
from functools import partial
from hashlib import sha256
from tempfile import NamedTemporaryFile

from flask import Response
from peewee import BigIntegerField
from peewee import BlobField
from peewee import CharField
from peewee import DateTimeField
from peewee import FixedCharField
from peewee import IntegerField

from peeweeplus import JSONModel, MySQLDatabase
from mimeutil import mimetype, mimetype_to_ext

from filedb.config import CONFIG, CHUNK_SIZE
from filedb.functions import get_range


__all__ = ['META_FIELDS', 'File']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])


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
    created = DateTimeField(default=datetime.now)
    last_access = DateTimeField(null=True, default=None)
    accessed = IntegerField(default=0)

    def __str__(self):
        """Converts the file to a string."""
        return str(self.sha256sum)

    @classmethod
    def get_fast(cls, *args, **kwargs):
        """Returns a single file with a fast query."""
        sparse_file = cls.select(cls.id).where(*args, **kwargs).get()
        return cls[sparse_file.id]

    @classmethod
    def by_sha256sum(cls, sha256sum):
        """Returns a file by its SHA-256 sum."""
        return cls.get_fast(cls.sha256sum == sha256sum)

    @classmethod
    def from_bytes(cls, bytes_, *, save=False):
        """Creates a file from the given bytes."""
        sha256sum = sha256(bytes_).hexdigest()

        try:
            return cls.by_sha256sum(sha256sum)
        except cls.DoesNotExist:
            file = cls()
            file.bytes = bytes_
            file.mimetype = mimetype(bytes_)
            file.sha256sum = sha256sum
            file.size = len(bytes_)

            if save:
                file.save()

            return file

    @classmethod
    def _from_temporary_file(cls, temp, sha256sum, mime_type, chunk_size):
        """Creates the file from a temporary file."""
        file = cls()
        file.sha256sum = sha256sum
        file.bytes = b''
        file.size = 0

        for chunk in iter(partial(temp.read, chunk_size), b''):
            file.bytes += chunk
            file.size += len(chunk)

        file.mimetype = mime_type
        return file

    @classmethod
    def from_stream(cls, stream, *, chunk_size=CHUNK_SIZE, save=False):
        """Creates a file from the respective stream."""
        sha256sum = sha256()

        with NamedTemporaryFile('w+b') as tmp:
            for chunk in stream:
                tmp.write(chunk)
                sha256sum.update(chunk)

            sha256sum = sha256sum.hexdigest()

            try:
                return cls.by_sha256sum(sha256sum)
            except cls.DoesNotExist:
                tmp.flush()
                tmp.seek(0)
                file = cls._from_temporary_file(
                    tmp, sha256sum, mimetype(tmp.name), chunk_size)

                if save:
                    file.save()

                return file

    @property
    def suffix(self):
        """Returns the file suffix."""
        return mimetype_to_ext(self.mimetype)

    @property
    def filename(self):
        """Returns a unique file name from the SHA-256 hash and suffix."""
        return self.sha256sum + self.suffix

    def touch(self):
        """Update access counters."""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

    def stream(self):
        """Generic WSGI function to stream a file."""
        start, end = get_range()

        if start >= self.size:
            start = 0

        if end:
            chunk = self.bytes[start:end]
        else:
            chunk = self.bytes[start:]
            end = self.size - 1

        response = Response(
            chunk, 206, mimetype=self.mimetype, content_type=self.mimetype,
            direct_passthrough=True)
        content_range = f'bytes {start}-{end}/{self.size}'
        response.headers.add('Content-Range', content_range)
        return response


META_FIELDS = (
    File.mimetype, File.sha256sum, File.size, File.created, File.last_access,
    File.accessed
)
