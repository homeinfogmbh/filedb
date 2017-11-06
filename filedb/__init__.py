"""HOMEINFO's file database"""

from filedb.client import FileError, add, get, delete
from filedb.extra import FileProperty

__all__ = ['FileError', 'add', 'get', 'delete', 'FileProperty']
