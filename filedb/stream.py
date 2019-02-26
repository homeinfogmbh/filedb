"""File streaming."""

from functools import partial
from gc import collect
from hashlib import sha256
from mimetypes import guess_extension
from pathlib import Path
from tempfile import TemporaryFile

from magic import from_buffer   # pylint: disable=E0401

from mimeutil import FileMetaData

from filedb.config import CHUNK_SIZE


__all__ = ['stream_bytes', 'stream_path', 'NamedFileStream']


def stream_bytes(bytes_, chunk_size=CHUNK_SIZE):
    """Streams bytes."""

    with TemporaryFile(mode='w+b') as tmp:
        tmp.write(bytes_)
        tmp.flush()
        tmp.seek(0)
        bytes_ = None   # Remove name from bytes.
        collect()       # Garbage collect bytes.

        for chunk in iter(partial(tmp.read, chunk_size), b''):
            yield chunk


def stream_path(path, chunk_size=CHUNK_SIZE):
    """Stream func for the path."""

    with path.open('rb') as file:
        for chunk in iter(partial(file.read, chunk_size), b''):
            yield chunk


class NamedFileStream:  # pylint: disable=R0902
    """Represents a named file stream."""

    __slots__ = ('stream_func', '_name', '_stem', '_suffix', '_mimetype',
                 '_size', '_sha256sum', 'chunk_size')

    def __init__(self, stream_func=None, name=None, # pylint: disable=R0913
                 stem=None, suffix=None, mimetype=None, size=None,
                 sha256sum=None, *, chunk_size=CHUNK_SIZE):
        """Sets name, streaming function callback,
        MIME type, size and streaming chunk size.
        """
        self.stream_func = stream_func
        self._name = name
        self._stem = stem
        self._suffix = suffix
        self._mimetype = mimetype
        self._size = size
        self._sha256sum = sha256sum
        self.chunk_size = chunk_size

    def __iter__(self):
        """Streams the file's bytes."""
        for chunk in self.stream():
            yield chunk

    def __str__(self):
        """Returns a string representation."""
        classname = type(self).__name__
        attributes = ', '.join(self._slot_strings)
        return '{}({})'.format(classname, attributes)

    @classmethod
    def from_bytes(cls, bytes_, name=None, *, chunk_size=CHUNK_SIZE):
        """Creates the file stream from bytes."""
        sha256sum, mimetype, suffix = FileMetaData.from_bytes(bytes_)
        return cls(partial(stream_bytes, bytes_), name=name,
                   mimetype=mimetype, size=len(bytes_), sha256sum=sha256sum,
                   suffix=suffix, chunk_size=chunk_size)

    @classmethod
    def from_orm(cls, file, name=None, *, chunk_size=CHUNK_SIZE):
        """Creates the file stream from a file ORM model."""
        return cls(partial(stream_path, file.path), name=name,
                   mimetype=file.mimetype, size=file.size,
                   sha256sum=file.sha256sum, chunk_size=chunk_size)

    @classmethod
    def from_path(cls, path, *, chunk_size=CHUNK_SIZE):
        """Creates the file stream from a pathlib.Path."""
        return cls(partial(stream_path, path), stem=path.stem,
                   suffix=path.suffix, chunk_size=chunk_size)

    @property
    def _slot_values(self):
        """Yields slot name / sloot value pairs."""
        for slot in type(self).__slots__:
            yield (slot, getattr(self, slot))

    @property
    def _slot_strings(self):
        """Yields 'slot=<value>' strings."""
        for slot, value in self._slot_values:
            yield '{}={}'.format(slot, value)

    @property
    def name(self):
        """Returns the name."""
        if self._name is None:
            self._name = self.stem + self.suffix

        return self._name

    @property
    def stem(self):
        """Returns the file stem."""
        if self._stem is None:
            if self._name is None:
                self._stem = self.sha256sum
            else:
                self._stem = Path(self._name).stem

        return self._stem

    @property
    def suffix(self):
        """Returns the file suffix aka. file extension."""
        if self._suffix is None:
            if self._name is None:
                self._suffix = guess_extension(self.mimetype)
            else:
                self._suffix = Path(self._name).suffix

        return self._suffix

    @property
    def mimetype(self):
        """Returns the MIME type."""
        if self._mimetype is None:
            for chunk in self.stream_func(chunk_size=CHUNK_SIZE):
                self._mimetype = from_buffer(chunk, mime=True)
                break

        return self._mimetype

    @property
    def size(self):
        """Returns the file's size."""
        if self._size is None:
            self._size = 0

            for chunk in self:
                self._size += len(chunk)

        return self._size

    @property
    def sha256sum(self):
        """Returns the file's SHA-256 sum."""
        if self._sha256sum is None:
            sha256sum = sha256()

            for chunk in self:
                sha256sum.update(chunk)

            self._sha256sum = sha256sum.hexdigest()

        return self._sha256sum

    def stream(self, chunk_size=None):
        """Streams the bytes."""
        chunk_size = self.chunk_size if chunk_size is None else chunk_size

        for chunk in self.stream_func(chunk_size=chunk_size):
            yield chunk
