"""HTTP access to the filedb"""

from os.path import join
from datetime import datetime

from requests import post, get, put, delete

from filedb.config import CONFIG, TIME_FORMAT

__all__ = ['FileError', 'FileClient']


class FileError(Exception):
    """Indicates errors while accessing files"""

    def __init__(self, result):
        """Sets the request result"""
        super().__init__(result)
        self.result = result


class FileClient():
    """Manages files via HTTP"""

    def __init__(self, key):
        """Sets the API key"""
        self.key = key

    @property
    def params(self):
        """Returns common URL parameters"""
        return {'key': self.key}

    @property
    def base_url(self):
        """Returns the base URL"""
        return CONFIG['www']['BASE_URL']

    def add(self, data, debug=False):
        """Adds a file"""
        if data:
            params = self.params
            result = post(self.base_url, data=data, params=params)

            if debug:
                return result
            else:
                if result.status_code == 200:
                    return int(result.text)
                else:
                    raise FileError(result)
        else:
            raise FileError('Refusing to add empty file')

    def get(self, ident, debug=False, nocheck=False):
        """Gets a file"""
        params = self.params

        if nocheck:
            params['nocheck'] = True

        result = get(join(self.base_url, str(ident)), params=params)

        if debug:
            return result
        else:
            if result.status_code == 200:
                return result.content
            else:
                raise FileError(result)

    def put(self, ident, debug=False, nocheck=False):
        """Increases reference counter"""
        params = self.params

        if nocheck:
            params['nocheck'] = True

        result = put(join(self.base_url, str(ident)), params=params)

        if debug:
            return result
        else:
            if result.status_code == 200:
                return result.content
            else:
                raise FileError(result)

    def delete(self, ident, debug=False):
        """Deletes a file"""
        params = self.params
        result = delete(join(self.base_url, str(ident)), params=params)

        if debug:
            return result

        return result.status_code == 200

    def _get_metadata(self, ident, metadata, debug=False):
        """Gets metadata"""
        params = self.params
        params['metadata'] = metadata
        result = get(join(self.base_url, str(ident)), params=params)

        if debug:
            return result
        else:
            if result.status_code == 200:
                return result.text
            else:
                raise FileError(result)

    def sha256sum(self, ident, debug=False):
        """Gets the SHA-256 checksum of the file"""
        return self._get_metadata(ident, 'sha256sum', debug=debug)

    def size(self, ident, debug=False):
        """Gets the file size in bytes"""
        return int(self._get_metadata(ident, 'size', debug=debug))

    def hardlinks(self, ident, debug=False):
        """Gets the file size in bytes"""
        return int(self._get_metadata(ident, 'hardlinks', debug=debug))

    def mimetype(self, ident, debug=False):
        """Gets the MIME type of the file"""
        return self._get_metadata(ident, 'mimetype', debug=debug)

    def accessed(self, ident, debug=False):
        """Gets the access count of the file"""
        return int(self._get_metadata(ident, 'accessed', debug=debug))

    def last_access(self, ident, debug=False, time_format=TIME_FORMAT):
        """Gets the last access datetime of the file"""
        last_access = self._get_metadata(ident, 'last_access', debug=debug)

        if last_access == 'never':
            return None

        return datetime.strptime(last_access, time_format)

    def created(self, ident, debug=False, time_format=TIME_FORMAT):
        """Gets the datetime of the file's creation"""
        return datetime.strptime(
            self._get_metadata(ident, 'created', debug=debug), time_format)
