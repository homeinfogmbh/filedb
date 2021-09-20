"""Configuration for HOMEINFO's global file database."""

from configlib import loadcfg


__all__ = ['CONFIG']


CONFIG = loadcfg('filedb.conf')
