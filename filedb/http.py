"""HTTP access to the filedb."""

from contextlib import suppress
from datetime import datetime
from os.path import join

from requests import post, get, put, delete

from filedb.config import CONFIG, TIME_FORMAT

__all__ = ['FileError', 'FileClient']


class FileError(Exception):
    """Indicates errors while accessing files."""

    def __init__(self, result):
        """Sets the request result."""
        super().__init__(result)
        self.result = result


class FileClient:
    """Manages files via HTTP."""

    def __init__(self, key):
        """Sets the API key."""
        self.key = key

    @property
    def params(self):
        """Returns common URL parameters."""
        return {'key': self.key}

    @property
    def base_url(self):
        """Returns the base URL."""
        return CONFIG['www']['BASE_URL']

    def add(self, data, debug=False):
        """Adds a file."""
        if data:
            params = self.params
            result = post(self.base_url, data=data, params=params)

            if debug:
                return result

            if result.status_code == 200:
                return int(result.text)

            raise FileError(result)

        raise FileError('Refusing to add empty file.')

    def get(self, ident, debug=False, nocheck=False):
        """Gets a file."""
        params = self.params

        if nocheck:
            params['nocheck'] = True

        result = get(join(self.base_url, str(ident)), params=params)

        if debug:
            return result

        if result.status_code == 200:
            return result.content

        raise FileError(result)

    def put(self, ident, debug=False, nocheck=False):
        """Increases reference counter."""
        params = self.params

        if nocheck:
            params['nocheck'] = True

        result = put(join(self.base_url, str(ident)), params=params)

        if debug:
            return result

        if result.status_code == 200:
            return result.content

        raise FileError(result)

    def delete(self, ident, debug=False):
        """Deletes a file."""
        params = self.params
        result = delete(join(self.base_url, str(ident)), params=params)

        if debug:
            return result

        return result.status_code == 200

    def _get_metadata(self, ident, metadata, debug=False, return_values=None):
        """Gets metadata."""
        params = self.params
        params['metadata'] = metadata
        result = get(join(self.base_url, str(ident)), params=params)

        if debug:
            return result

        if return_values is None:
            if result.status_code == 200:
                return result.text
        else:
            with suppress(KeyError):
                return return_values[result.status_code]

        raise FileError(result)

    def exists(self, ident, debug=False):
        """Determines whether the respective file exists."""
        return self._get_metadata(
            ident, 'exists', debug=debug,
            return_values={200: True, 404: False})

    def sha256sum(self, ident, debug=False):
        """Gets the SHA-256 checksum of the file."""
        return self._get_metadata(ident, 'sha256sum', debug=debug)

    def size(self, ident, debug=False):
        """Gets the file size in bytes."""
        return int(self._get_metadata(ident, 'size', debug=debug))

    def hardlinks(self, ident, debug=False):
        """Gets the file size in bytes."""
        return int(self._get_metadata(ident, 'hardlinks', debug=debug))

    def mimetype(self, ident, debug=False):
        """Gets the MIME type of the file."""
        return self._get_metadata(ident, 'mimetype', debug=debug)

    def accessed(self, ident, debug=False):
        """Gets the access count of the file."""
        return int(self._get_metadata(ident, 'accessed', debug=debug))

    def last_access(self, ident, debug=False, time_format=TIME_FORMAT):
        """Gets the last access datetime of the file."""
        last_access = self._get_metadata(ident, 'last_access', debug=debug)

        if last_access == 'never':
            return None

        return datetime.strptime(last_access, time_format)

    def created(self, ident, debug=False, time_format=TIME_FORMAT):
        """Gets the datetime of the file's creation."""
        return datetime.strptime(
            self._get_metadata(ident, 'created', debug=debug), time_format)
