"""HTTP access to the filedb"""

from os.path import join
from datetime import datetime
from logging import basicConfig, getLogger

from requests import post, get, put, delete

from filedb.config import config

__all__ = ['FileError', 'FileClient']


basicConfig()
logger = getLogger(__name__)


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
        return config.www['BASE_URL']

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
        else:
            if result.status_code == 200:
                return True
            else:
                return False

    def _get_metadata(self, ident, query, debug=False):
        """Gets metadata"""
        params = self.params
        params['query'] = query
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

    def last_access(self, ident, debug=False, tf='%Y-%m-%dT%H:%M:%S'):
        """Gets the last access datetime of the file"""
        la = self._get_metadata(ident, 'last_access', debug=debug)

        if la == 'never':
            return None
        else:
            return datetime.strptime(la, tf)

    def created(self, ident, debug=False, tf='%Y-%m-%dT%H:%M:%S'):
        """Gets the datetime of the file's creation"""
        return datetime.strptime(
            self._get_metadata(ident, 'created', debug=debug), tf)


class FileProperty():
    """File property"""

    def __init__(self, file_manager, field, saving=False):
        self.file_manager = file_manager
        self.field = field
        self.saving = saving

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return self.file_manager.get(self.field)
        return self

    def __set__(self, instance, value):
        try:
            self.file_manager.delete(self.field)
        except FileError as e:
            logger.error(e)

        self.field = self.file_manager.add(value)

        if self.saving:
            instance.save()
