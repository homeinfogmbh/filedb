"""File streaming."""

from functools import partial
from hashlib import sha256
from io import BytesIO
from mimetypes import guess_extension

from magic import from_buffer   # pylint: disable=E0401

from mimeutil import FileMetaData


__all__ = ['NamedFileStream']


class NamedFileStream:
    """Represents a named file stream."""

    def __init__(self, stream_func=None, stem=None, # pylint: disable=R0913
                 mimetype=None, size=None, sha256sum=None, suffix=None, *,
                 chunk_size=4096):
        """Sets name, streaming function callback,
        MIME type, size and streaming chunk size.
        """
        self.stream_func = stream_func
        self._stem = stem
        self._mimetype = mimetype
        self._size = size
        self._sha256sum = sha256sum
        self._suffix = suffix
        self.chunk_size = chunk_size

    def __iter__(self):
        """Streams the file's bytes."""
        for chunk in self.stream():
            yield chunk

    @classmethod
    def from_bytes(cls, bytes_, *, chunk_size=4096):
        """Creates the file stream from bytes."""
        def stream_func(chunk_size=chunk_size):
            file = BytesIO(bytes_)
            yield from iter(partial(file.read, chunk_size), b'')

        sha256sum, mimetype, suffix = FileMetaData.from_bytes(bytes_)
        return cls(stream_func, mimetype=mimetype, size=len(bytes_),
                   sha256sum=sha256sum, suffix=suffix, chunk_size=chunk_size)

    @classmethod
    def from_file_model(cls, file, *, chunk_size=4096):
        """Creates the file stream from a file ORM model."""
        return cls(file.stream, mimetype=file.mimetype, size=file.size,
                   sha256sum=file.sha256sum, chunk_size=chunk_size)

    @classmethod
    def from_path(cls, path, *, chunk_size=4096):
        """Creates the file stream from a pathlib.Path."""
        def stream_func(chunk_size=chunk_size):
            """Stream func for the path."""
            with path.open('rb') as file:
                yield from iter(partial(file.read, chunk_size), b'')

        return cls(stream_func, stem=path.stem, suffix=path.suffix,
                   chunk_size=chunk_size)

    @property
    def stem(self):
        """Returns the file stem."""
        if self._stem is None:
            return self.sha256sum

        return self._stem

    @property
    def mimetype(self):
        """Returns the MIME type."""
        if self._mimetype is None:
            for chunk in self.stream_func(chunk_size=1024):
                return from_buffer(chunk, mime=True)

        return self._mimetype

    @property
    def size(self):
        """Returns the file's size."""
        if self._size is None:
            size = 0

            for chunk in self:
                size += len(chunk)

            return size

        return self._size

    @property
    def sha256sum(self):
        """Returns the file's SHA-256 sum."""
        if self._sha256sum is None:
            sha256sum = sha256()

            for chunk in self:
                sha256sum.update(chunk)

            return sha256sum.hexdigest()

        return self._sha256sum

    @property
    def suffix(self):
        """Returns the file suffix aka. file extension."""
        if self._suffix is None:
            return guess_extension(self.mimetype)

        return self._suffix

    @property
    def name(self):
        """Returns the file name."""
        return self.stem + self.suffix

    def stream(self, chunk_size=None):
        """Streams the bytes."""
        chunk_size = self.chunk_size if chunk_size is None else chunk_size

        for chunk in self.stream_func(chunk_size=chunk_size):
            yield chunk
