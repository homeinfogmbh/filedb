"""File streaming."""

from re import search

from flask import request, Response


__all__ = ['stream']


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
