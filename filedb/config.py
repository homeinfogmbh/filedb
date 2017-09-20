"""Configuration for HOMEINFO's global file database"""

from configlib import INIParser

__all__ = ['config']


config = INIParser('/etc/filedb.conf')
