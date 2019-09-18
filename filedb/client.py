"""HTTP access to the filedb."""

from logging import WARNING, getLogger

from requests import post, get as get_, put as put_, delete as delete_

from timelib import strpdatetime

from filedb.config import CONFIG, PATH
from filedb.exceptions import FileError


__all__ = [
    'BASE_URL',
    'add',
    'get',
    'stream',
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


def add(data, *, raw=False):
    """Adds a file."""

    if not data:
        raise FileError('Cowardly refusing to add empty file.')

    result = post(_get_url(), data=data)

    if result.status_code == 200:
        return result.json() if raw else result.json()['id']

    raise FileError(result.text)


def get(ident, nocheck=False):
    """Gets a file."""

    params = {'nocheck': True} if nocheck else None
    result = get_(_get_url(ident), params=params)

    if result.status_code == 200:
        return result.content

    raise FileError(result)


def stream(ident, nocheck=False, chunk_size=4096, decode_unicode=False):
    """Yields byte blocks of the respective file."""

    params = {'nocheck': True} if nocheck else None
    result = get_(_get_url(ident), params=params)

    if result.status_code == 200:
        for chunk in result.iter_content(
                chunk_size=chunk_size, decode_unicode=decode_unicode):
            yield chunk
    else:
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


def get_metadata(ident, *, checkexists=False):
    """Gets metadata."""

    result = get_(_get_url(f'/meta/{ident}'))

    if checkexists:
        if result.status_code == 200:
            return True

        if result.status_code == 404:
            return False
    elif result.status_code == 200:
        return result.json()

    raise FileError(result)


def exists(ident):
    """Determines whether the respective file exists."""

    return get_metadata(ident, checkexists=True)


def sha256sum(ident):
    """Gets the SHA-256 checksum of the file."""

    return get_metadata(ident)['sha256sum']


def size(ident):
    """Gets the file size in bytes."""

    return get_metadata(ident)['size']


def hardlinks(ident):
    """Gets the file size in bytes."""

    return get_metadata(ident)['hardlinks']


def mimetype(ident):
    """Gets the MIME type of the file."""

    return get_metadata(ident)['mimetype']


def accessed(ident):
    """Gets the access count of the file."""

    return get_metadata(ident)['accessed']


def last_access(ident):
    """Gets the last access datetime of the file."""

    return strpdatetime(get_metadata(ident).get('last_access'))


def created(ident):
    """Gets the datetime of the file's creation."""

    return strpdatetime(get_metadata(ident)['created'])
