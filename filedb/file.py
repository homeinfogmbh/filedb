"""
Abstract base classes for HOMEINFO's file database
"""
from .abc import FileDBModel
from homeinfo.util import MIMEUtil
from peewee import CharField
from os.path import join
from os import unlink
from hashlib import sha256
from uuid import uuid4

__date__ = '02.12.2014'
__author__ = 'Richard Neumann <r.neumann@homeinfo.de>'
__all__ = ['File']


class File(FileDBModel):
    """
    A file entry
    """
    basedir = CharField(255)
    filename = CharField(255)
    suffix = CharField(8, null=True)
    mimetype = CharField(255)
    _sha256sum = CharField(69, db_column='sha256sum')

    def __init__(self, filename=None, basedir='/srv/files', suffix=None):
        """Initializes a file"""
        self.filename = uuid4() if filename is None else filename
        self.basedir = basedir
        self.suffix = suffix

    @property
    def _suffix(self):
        """Returns an enforced string version of the suffix"""
        return '' if self.suffix is None else self.suffix

    @property
    def sha256sum(self):
        """Returns the SHA-256 sum"""
        return self._sha256sum

    @property
    def path(self):
        """Returns the full file path"""
        return join(self.basedir,
                    (''.join([self.filename, self._suffix])
                     if self._suffix.startswith('.')
                     else '.'.join([self.filename, self._suffix]))
                    if self.suffix else self.filename)

    def read(self):
        """Read the respective file's content"""
        with open(self.path, 'rb') as f:
            return f.read()

    def remove(self):
        """Removes the file"""
        unlink(self.path)
        self.delete_instance()

    def write(self, data, force_insert=False):
        """Writes data to the file"""
        with open(self.path, 'wb') as f:
            f.write(data)
        self.suffix = MIMEUtil.getext(self.path)
        self.mimetype = MIMEUtil.getmime(self.path)
        self._sha256sum = str(sha256(data).hexdigest())
        self.save(force_insert=force_insert)
