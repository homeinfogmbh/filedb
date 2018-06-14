"""Configuration for HOMEINFO's global file database."""

from configlib import INIParser

__all__ = ['CONFIG', 'PATH']


CONFIG = INIParser('/etc/filedb.conf', interpolation=None)
PATH = CONFIG['http'].get('path', '')

if not PATH.endswith('/'):
    PATH += '/'
