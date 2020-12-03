"""Common functions."""

from re import search
from typing import Tuple

from flask import request


__all__ = ['get_range']


def get_range() -> Tuple[int, int]:
    """Gets the requested stream range."""

    range = request.headers.get('Range')    # pylint: disable=W0622
    start, end = (0, None)

    if range:
        match = search(r'(\d+)-(\d*)', range)
        start, end = match.groups()
        start = int(start) if start else 0
        end = int(end) if end else None

    return (start, end)
