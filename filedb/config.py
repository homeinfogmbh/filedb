"""Configuration for HOMEINFO's global file database."""

from configlib import loadcfg


__all__ = ['CONFIG', 'PATH', 'CHUNK_SIZE']


CONFIG = loadcfg('filedb.conf')
PATH = CONFIG['http'].get('path', '')
CHUNK_SIZE = int(CONFIG['data']['chunk_size'])
