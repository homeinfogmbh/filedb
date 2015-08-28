"""Configuration for HOMEINFO's global file database"""

from homeinfo.lib.config import Configuration

__all__ = ['filedb_config']


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

filedb_config = FileDBConfig('/etc/filedb.conf')
