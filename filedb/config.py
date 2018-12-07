"""Configuration for HOMEINFO's global file database."""

from configlib import loadcfg


__all__ = ['CONFIG', 'PATH']


CONFIG = loadcfg('filedb.conf')
PATH = CONFIG['http'].get('path', '')
