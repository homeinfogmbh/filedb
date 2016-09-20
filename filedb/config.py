"""Configuration for HOMEINFO's global file database"""

from homeinfo.lib.config import Configuration

__all__ = ['config']


class FileDBConfig(Configuration):
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
