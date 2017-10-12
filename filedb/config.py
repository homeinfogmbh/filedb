"""Configuration for HOMEINFO's global file database."""

from configlib import INIParser

__all__ = ['CONFIG', 'TIME_FORMAT']


CONFIG = INIParser('/etc/filedb.conf')
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
