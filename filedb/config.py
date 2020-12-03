"""Configuration for HOMEINFO's global file database."""

from configlib import loadcfg


__all__ = ['CONFIG', 'CHUNK_SIZE']


CONFIG = loadcfg('filedb.conf')
CHUNK_SIZE = CONFIG.getint('data', 'chunk_size')
