"""HTTP access to the filedb."""

from contextlib import suppress
from datetime import datetime
from logging import WARNING, getLogger

from requests import post, get as get_, put as put_, delete as delete_

from filedb.config import CONFIG, PATH

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


BASE_URL = 'http://{}:{}{}'.format(
    CONFIG['http']['host'], CONFIG['http']['port'], PATH)
_TIME_FORMAT = CONFIG['data']['time_format']
# Disable urllib3 verbose logging.
getLogger("urllib3").setLevel(WARNING)


class FileError(Exception):
    """Indicates errors while accessing files."""

    def __init__(self, result):
        """Sets the request result."""
        super().__init__(result)
        self.result = result


def _get_url(path=''):
    """Joins the respective path to the base URL."""

    base_url = BASE_URL.rstrip('/')
    path = str(path).strip('/')
    return '/'.join((base_url, path))


def add(data):
    """Adds a file."""

    if data:
        result = post(_get_url(), data=data)

        if result.status_code == 200:
            return int(result.text)

        raise FileError(result.text)

    raise FileError('Refusing to add empty file.')


def get(ident, nocheck=False):
    """Gets a file."""

    params = {'nocheck': True} if nocheck else None
    result = get_(_get_url(ident), params=params)

    if result.status_code == 200:
        return result.content

    raise FileError(result)


def put(ident, nocheck=False):
    """Increases reference counter."""

    params = {'nocheck': True} if nocheck else None
    result = put_(_get_url(ident), params=params)

    if result.status_code == 200:
        return result.content

    raise FileError(result)


def delete(ident):
    """Deletes a file."""

    result = delete_(_get_url(ident))
    return result.status_code == 200


def get_metadata(ident, metadata, return_values=None):
    """Gets metadata."""

    result = get_(_get_url(ident), params={'metadata': metadata})

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
