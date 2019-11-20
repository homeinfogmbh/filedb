"""File streaming."""

from re import search

from flask import request, Response

from wsgilib import Error


__all__ = ['FileStream', 'stream']


MIN_CHUNK_SIZE = 4096
DEFAULT_CHUNK_SIZE = MIN_CHUNK_SIZE * 1024
MAX_CHUNK_SIZE = DEFAULT_CHUNK_SIZE * 1024
ALLOWED_CHUNK_SIZES = range(MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)


def get_range():
    """Gets the requested range."""

    range = request.headers.get('Range')    # pylint: disable=W0622
    start, end = (0, None)

    if range:
        match = search(r'(\d+)-(\d*)', range)
        start, end = match.groups()
        start = int(start) if start else 0
        end = int(end) if end else None

    return (start, end)


def stream(file):
    """Generic WSGI function to stream a file."""

    start, end = get_range()
    chunk, start, length = file.get_chunk(start, end)
    response = Response(
        chunk, 206, mimetype=file.mimetype, content_type=file.mimetype,
        direct_passthrough=True)
    end = start + length - 1
    response.headers.add('Content-Range', f'bytes {start}-{end}/{file.size}')
    return response


def get_chunk_size():
    """Gets the chunk size from the request args."""

    try:
        chunk_size = request.args['chunk_size']
    except KeyError:
        return DEFAULT_CHUNK_SIZE

    try:
        chunk_size = int(chunk_size)
    except ValueError:
        raise Error('Chunk size is not an integer.')

    if chunk_size in ALLOWED_CHUNK_SIZES:
        return chunk_size

    raise Error('Chunk size out of bounds.')


class FileStream(Response):     # pylint: disable=R0901
    """A stream response."""

    def __init__(self, file, chunk_size=4096):
        """Sets the file, chunk size and status code."""
        super().__init__(
            file.stream(chunk_size), status=206, mimetype=file.mimetype,
            content_type=file.mimetype, direct_passthrough=True)
        self.headers.add('Content-Length', file.size)

    @classmethod
    def from_request_args(cls, file):
        """Gets the chunk size from the request args."""
        return cls(file, chunk_size=get_chunk_size())
