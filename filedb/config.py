"""Configuration for HOMEINFO's global file database"""

from configparserplus import ConfigParserPlus

__all__ = ['config']


config = ConfigParserPlus('/etc/filedb.conf')
