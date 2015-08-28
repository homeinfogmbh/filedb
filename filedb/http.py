"""HTTP access to the filedb"""

from os.path import join
from requests import post, get, delete
from homeinfo.lib.misc import classproperty
from .config import filedb_config

__all__ = ['FileError', 'File']


class FileError(Exception):
    """Indicates errors while accessing files"""
    pass


class File():
    """Manages files via HTTP"""

    @classproperty
    @classmethod
    def base_url(cls):
        """Returns the base URL"""
        return filedb_config.www['BASE_URL']

    @classmethod
    def add(cls, data, debug=False):
        """Adds a file"""
        result = post(cls.base_url, data=data)
        if debug:
            return result
        else:
            if result.status_code == 200:
                return int(result.text)
            else:
                raise FileError(result)

    @classmethod
    def get(cls, ident, debug=False):
        """Gets a file"""
        result = get(join(cls.base_url, str(ident)))
        if debug:
            return result
        else:
            if result.status_code == 200:
                return result.content
            else:
                raise FileError(result)

    @classmethod
    def delete(cls, ident, debug=False):
        """Deletes a file"""
        result = delete(join(cls.base_url, str(ident)))
        if debug:
            return result
        else:
            if result.status_code == 200:
                return True
            else:
                return False
