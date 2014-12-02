"""
Abstract base classes for HOMEINFO's file database
"""
from .config import db
from peewee import Model, MySQLDatabase

__date__ = '02.12.2014'
__author__ = 'Richard Neumann <r.neumannr@homeinfo.de>'
__all__ = ['FileDBModel']


class FileDBModel(Model):
    """
    A basic model for the file database
    """
    class Meta:
        database = MySQLDatabase('filedb', host=db.get('host'),
                                 user=db.get('user'),
                                 passwd=db.get('passwd'))
