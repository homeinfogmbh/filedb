"""HTTP access to the filedb."""

from contextlib import suppress
from datetime import datetime
from os.path import join

from requests import post, get as get_, put as put_, delete as delete_

from filedb.config import CONFIG

__all__ = [
    'BASE_URL',
    'FileError',
    'add',
    'get',
    'put',
    'delete',
    'get_metadata',
    'exists',
    'sha256sum',
    'size',
    'hardlinks',
    'mimetype',
    'accessed',
    'last_access',
    'created']


BASE_URL = 'http://{}:{}/'.format(
    CONFIG['http']['host'], CONFIG['http']['port'])
_TIME_FORMAT = CONFIG['data']['time_format']


class FileError(Exception):
    """Indicates errors while accessing files."""

    def __init__(self, result):
        """Sets the request result."""
        super().__init__(result)
        self.result = result


def add(data):
    """Adds a file."""

    if data:
        result = post(BASE_URL, data=data)

        if result.status_code == 200:
            return int(result.text)

        raise FileError(result.text)

    raise FileError('Refusing to add empty file.')


def get(ident, nocheck=False):
    """Gets a file."""

    params = {'nocheck': True} if nocheck else None
    result = get_(join(BASE_URL, str(ident)), params=params)

    if result.status_code == 200:
        return result.content

    raise FileError(result)


def put(ident, nocheck=False):
    """Increases reference counter."""

    params = {'nocheck': True} if nocheck else None
    result = put_(join(BASE_URL, str(ident)), params=params)

    if result.status_code == 200:
        return result.content

    raise FileError(result)


def delete(ident):
    """Deletes a file."""

    result = delete_(join(BASE_URL, str(ident)))
    return result.status_code == 200


def get_metadata(ident, metadata, return_values=None):
    """Gets metadata."""

    result = get_(join(BASE_URL, str(ident)), params={'metadata': metadata})

    if return_values:
        with suppress(KeyError):
            return return_values[result.status_code]
    elif result.status_code == 200:
        return result.text

    raise FileError(result)


def exists(ident):
    """Determines whether the respective file exists."""

    return get_metadata(
        ident, 'exists',
        return_values={200: True, 404: False})


def sha256sum(ident):
    """Gets the SHA-256 checksum of the file."""

    return get_metadata(ident, 'sha256sum')


def size(ident):
    """Gets the file size in bytes."""

    return int(get_metadata(ident, 'size'))


def hardlinks(ident):
    """Gets the file size in bytes."""

    return int(get_metadata(ident, 'hardlinks'))


def mimetype(ident):
    """Gets the MIME type of the file."""

    return get_metadata(ident, 'mimetype')


def accessed(ident):
    """Gets the access count of the file."""

    return int(get_metadata(ident, 'accessed'))


def last_access(ident, time_format=_TIME_FORMAT):
    """Gets the last access datetime of the file."""

    last_access_ = get_metadata(ident, 'last_access')

    if last_access_ == 'never':
        return None

    return datetime.strptime(last_access_, time_format)


def created(ident, time_format=_TIME_FORMAT):
    """Gets the datetime of the file's creation."""

    return datetime.strptime(
        get_metadata(ident, 'created'), time_format)
