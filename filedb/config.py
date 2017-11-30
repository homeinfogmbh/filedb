"""Configuration for HOMEINFO's global file database."""

from configlib import INIParser

__all__ = ['CONFIG']


CONFIG = INIParser('/etc/filedb.conf', interpolation=None)
