"""HTTP access to the filedb."""

from logging import WARNING, getLogger

from requests import post, delete as delete_

from filedb.config import CONFIG, PATH
from filedb.exceptions import FileError
from filedb.orm import File


__all__ = [
    'BASE_URL',
    'add',
    'get',
    'put',
    'delete',
    'exists',
    'sha256sum',
    'size',
    'hardlinks',
    'mimetype',
    'accessed',
    'last_access',
    'created'
]


_HOST = CONFIG['http']['host']
_PORT = CONFIG['http']['port']
BASE_URL = f'http://{_HOST}:{_PORT}{PATH}'
# Disable urllib3 verbose logging.
getLogger('requests').setLevel(WARNING)


def _get_url(path=''):
    """Joins the respective path to the base URL."""

    base_url = BASE_URL.rstrip('/')
    path = str(path).strip('/')
    return f'{base_url}/{path}'


def _file_by_id(ident):
    """Returns a file by its ID."""

    try:
        return File[ident]
    except File.DoesNotExist:
        raise FileError('No such file.')


def add(data):
    """Adds a file."""

    if not data:
        raise FileError('Cowardly refusing to add empty file.')

    response = post(_get_url(), data=data)

    if response.status_code == 200:
        return response.json()

    raise FileError(response.text)


def get(ident):
    """Gets a file."""

    return _file_by_id(ident).bytes


def put(ident):
    """Increases reference counter."""

    return _file_by_id(ident).touch()


def delete(ident):
    """Deletes a file."""

    response = delete_(_get_url(ident))
    return response.status_code == 200


def exists(ident):
    """Determines whether the respective file exists."""

    try:
        return File[ident]
    except File.DoesNotExist:
        return False


def sha256sum(ident):
    """Gets the SHA-256 checksum of the file."""

    return _file_by_id(ident).sha256sum


def size(ident):
    """Gets the file size in bytes."""

    return _file_by_id(ident).size


def hardlinks(ident):
    """Gets the file size in bytes."""

    return _file_by_id(ident).hardlinks


def mimetype(ident):
    """Gets the MIME type of the file."""

    return _file_by_id(ident).mimetype


def accessed(ident):
    """Gets the access count of the file."""

    return _file_by_id(ident).accessed


def last_access(ident):
    """Gets the last access datetime of the file."""

    return _file_by_id(ident).last_access


def created(ident):
    """Gets the datetime of the file's creation."""

    return _file_by_id(ident).created
