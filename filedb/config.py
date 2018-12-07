"""Configuration for HOMEINFO's global file database."""

from configparser import ConfigParser


__all__ = ['CONFIG', 'PATH']


CONFIG = ConfigParser(interpolation=None)
CONFIG.read('/usr/local/etc/filedb.conf')
PATH = CONFIG['http'].get('path', '')
