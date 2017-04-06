"""Configuration for HOMEINFO's global file database"""

from configparserplus import ConfigParserPlus

__all__ = ['config']


class FileDBConfig(ConfigParserPlus):
    """Main configuration for the file database"""

    @property
    def db(self):
        self.load()
        return self['db']

    @property
    def fs(self):
        self.load()
        return self['fs']

    @property
    def www(self):
        self.load()
        return self['www']


config = FileDBConfig('/etc/filedb.conf')
