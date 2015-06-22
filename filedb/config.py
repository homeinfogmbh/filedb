"""Configuration for HOMEINFO's global file database"""

from homeinfo.lib.config import Configuration

__all__ = ['filedb_config']


class FileDBConfig(Configuration):
    """Main configuration for the file database"""

    @property
    def db(self):
        return self['db']

    @property
    def fs(self):
        return self['fs']

filedb_config = FileDBConfig('/usr/local/etc/filedb.conf')
