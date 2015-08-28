"""HTTP access to the filedb"""

from os.path import join
from requests import post, get, delete
from homeinfo.lib.misc import classproperty
from .config import filedb_config


class File():
    """Manages files via HTTP"""

    @classproperty
    @classmethod
    def base_url(cls):
        """Returns the base URL"""
        return filedb_config.www['BASE_URL']

    @classmethod
    def add(cls, data):
        """Adds a file"""
        return post(cls.base_url, data=data)

    @classmethod
    def get(cls, ident):
        """Gets a file"""
        return get(join(cls.base_url, str(ident)))

    @classmethod
    def delete(cls, ident):
        """Deletes a file"""
        return delete(join(cls.base_url, str(ident)))
