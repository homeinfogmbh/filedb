"""Abstract base classes for HOMEINFO's file database"""

from .config import filedb_config
from peewee import Model, MySQLDatabase

__all__ = ['FileDBModel']


class FileDBModel(Model):
    """
    A basic model for the file database
    """
    class Meta:
        database = MySQLDatabase(
            'filedb', host=filedb_config.db['host'],
            user=filedb_config.db['user'],
            passwd=filedb_config.db['passwd'])
