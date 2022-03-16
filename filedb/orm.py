"""Models for HOMEINFO's global file database."""

from __future__ import annotations
from datetime import datetime
from hashlib import sha256
from typing import Iterable, Iterator, Union

from flask import Response
from peewee import IntegrityError
from peewee import BigIntegerField
from peewee import BlobField
from peewee import CharField
from peewee import DateTimeField
from peewee import Field
from peewee import FixedCharField
from peewee import IntegerField

from peeweeplus import JSONModel, MySQLDatabaseProxy
from mimeutil import mimetype, mimetype_to_ext

from filedb.functions import get_range


__all__ = ['META_FIELDS', 'File']


DATABASE = MySQLDatabaseProxy('filedb')
SHA256 = type(sha256())


class FileDBModel(JSONModel):
    """A basic model for the file database."""

    class Meta:
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
    def by_sha256sum(cls, sha256sum: Union[SHA256, str]) -> File:
        """Returns a file by its SHA-256 sum."""
        if isinstance(sha256sum, SHA256):
            return cls.by_sha256sum(sha256sum.hexdigest())

        return cls.select().where(cls.sha256sum == sha256sum).get()

    @classmethod
    def _from_bytes(
            cls,
            bytes_: bytes,
            sha256sum: SHA256, *,
            save: bool
    ) -> File:
        """Creates a new file."""
        file = cls()
        file.bytes = bytes_
        file.mimetype = mimetype(bytes_)
        file.sha256sum = sha256sum.hexdigest()
        file.size = len(bytes_)
        return file.save_unique() if save else file

    @classmethod
    def from_bytes(cls, bytes_: bytes, *, save: bool = False) -> File:
        """Creates a file from the given bytes."""
        try:
            return cls.by_sha256sum(sha256sum := sha256(bytes_))
        except cls.DoesNotExist:
            return cls._from_bytes(bytes_, sha256sum, save=save)

    @classmethod
    def from_stream(
            cls,
            stream: Iterator[bytes],
            *,
            save: bool = False
    ) -> File:
        """Creates a file from the respective stream."""
        return cls.from_bytes(b''.join(stream), save=save)

    @classmethod
    def meta_fields(cls) -> Iterable[Field]:
        """Returns an iterable of metadata fields."""
        return (
            cls.id, cls.mimetype, cls.sha256sum, cls.size, cls.created,
            cls.last_access, cls.accessed
        )

    @property
    def suffix(self) -> str:
        """Returns the file suffix."""
        return mimetype_to_ext(self.mimetype)

    @property
    def filename(self) -> str:
        """Returns a unique file name from the SHA-256 hash and suffix."""
        return self.sha256sum + self.suffix

    def save_unique(self):
        """Saves the file or returns an equivalent
        record by its SHA-256 sum.
        """
        try:
            self.save()
        except IntegrityError:
            return type(self).by_sha256sum(self.sha256sum)

        return self

    def touch(self):
        """Update access counters."""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

    def stream(self) -> Response:
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
            direct_passthrough=True
        )
        content_range = f'bytes {start}-{end}/{self.size}'
        response.headers.add('Content-Range', content_range)
        return response


META_FIELDS = File.meta_fields()
