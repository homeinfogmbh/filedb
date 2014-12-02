"""
Abstract base classes for HOMEINFO's file database
"""
from .abc import FileDBModel
from .error import ChecksumMismatch, FilesizeMismatch
from homeinfo.util import MIMEUtil
from peewee import CharField, IntegerField
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
    """The base directory of the file"""
    basename = CharField(255)
    """The file's basename"""
    suffix = CharField(8, null=True)
    """An optional file suffix"""
    mimetype = CharField(255)
    """The file's MIME type"""
    _sha256sum = CharField(69, db_column='sha256sum')
    """A SHA-256 checksum"""
    _size = IntegerField()
    """The file's size in bytes"""

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
        """Returns the file's SHA-256 sum"""
        return self._sha256sum

    @property
    def size(self):
        """Returns the file's size"""
        return self._size

    @property
    def filename(self):
        """The file's full name / path"""
        return join(self.basedir,
                    (''.join([self.filename, self._suffix])
                     if self._suffix.startswith('.')
                     else '.'.join([self.filename, self._suffix]))
                    if self.suffix else self.filename)

    @property
    def path(self):
        """An alias to filename"""
        return self.filename

    def _read(self):
        """Reads the respective file's content"""
        with open(self.filename, 'rb') as f:
            return f.read()

    def read(self):
        """Reads the file's content safely"""
        data = self._read()
        sha256sum = str(sha256(data).hexdigest())
        size = len(data)
        if sha256sum == self.sha256sum:
            if size == self.size:
                return data
            else:
                raise FilesizeMismatch(size, self.size)
        else:
            raise ChecksumMismatch(sha256sum, self.sha256sum)

    def remove(self):
        """Removes the file"""
        unlink(self.filename)
        self.delete_instance()

    def write(self, data, force_insert=False):
        """Writes data to the file"""
        with open(self.filename, 'wb') as f:
            f.write(data)
        self.suffix = MIMEUtil.getext(self.filename)
        self.mimetype = MIMEUtil.getmime(self.filename)
        self._sha256sum = str(sha256(data).hexdigest())
        self._size = len(data)
        self.save(force_insert=force_insert)

    def __str__(self):
        """Converts the file to a string"""
        return self.filename
