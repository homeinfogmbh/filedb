"""Common functions."""

from re import search
from typing import Optional

from flask import request


__all__ = ['get_range']


def get_range() -> tuple[int, Optional[int]]:
    """Gets the requested stream range."""

    if not (range_ := request.headers.get('Range')):
        return (0, None)

    match = search(r'(\d+)-(\d*)', range_)
    start, end = match.groups()
    start = int(start) if start else 0
    end = int(end) if end else None
    return (start, end)
