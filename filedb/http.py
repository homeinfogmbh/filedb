"""HTTP access to the filedb"""

from os.path import join

from requests import post, get, delete

from .config import filedb_config

__all__ = ['FileError', 'File']


class FileError(Exception):
    """Indicates errors while accessing files"""

    pass


class File():
    """Manages files via HTTP"""

    def __init__(self, key):
        """Sets the API key"""
        self._key = key

    @property
    def key(self):
        """Returns the API key"""
        return self._key

    @property
    def params(self):
        """Returns common URL parameters"""
        return {'key': self.key}

    @property
    def base_url(self):
        """Returns the base URL"""
        return filedb_config.www['BASE_URL']

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

    def mimetype(self, ident, debug=False):
        """Gets the MIME type of the file"""
        params = self.params
        params['query'] = 'mimetype'
        result = get(join(self.base_url, str(ident)), params=params)

        if debug:
            return result
        else:
            if result.status_code == 200:
                return result.text
            else:
                raise FileError(result)

    def sha256sum(self, ident, debug=False):
        """Gets the MIME type of the file"""
        params = self.params
        params['query'] = 'sha256sum'
        result = get(join(self.base_url, str(ident)), params=params)

        if debug:
            return result
        else:
            if result.status_code == 200:
                return result.text
            else:
                raise FileError(result)

    def delete(self, ident, debug=False):
        """Deletes a file"""
        params = self.params
        result = delete(join(self.base_url, str(ident)), params=params)

        if debug:
            return result
        else:
            if result.status_code == 200:
                return True
            else:
                return False
