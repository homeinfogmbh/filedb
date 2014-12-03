"""
Abstract base classes for HOMEINFO's file database
"""
from .abc import FileDBModel
from .error import ChecksumMismatch, FilesizeMismatch
from homeinfo.util import MIMEUtil
from peewee import CharField, IntegerField
from os.path import join, basename
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
    _size = IntegerField(db_column='size')
    """The file's size in bytes"""

    def __init__(self, path=None, basedir='/tmp', suffix=None):
        """Initializes a file"""
        self.basename = uuid4() if path is None else basename(path)
        self.basedir = join('' if basedir is None else basedir,
                            '' if path is None else basedir(path))
        self.suffix = suffix

    @property
    def fileext(self):
        """Returns the appropriate file extension from the suffix"""
        if self.suffix is None:
            return ''
        elif self.suffix.startwith('.'):
            return self.suffix
        else:
            return '.'.join(['', self.suffix])

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
        return join(self.basedir, ''.join([self.filename, self.fileext]))

    @property
    def path(self):
        """An alias to filename"""
        return self.filename

    @property
    def data(self):
        """Returns the file's content"""
        with open(self.filename, 'rb') as f:
            return f.read()

    @property
    def consistent(self):
        """Checks for consistency"""
        data = self.data
        sha256sum = str(sha256(data).hexdigest())
        size = len(data)
        if sha256sum == self.sha256sum:
            if size == self.size:
                return True
        return False

    def read(self):
        """Reads the file's content safely"""
        data = self.data
        sha256sum = str(sha256(data).hexdigest())
        size = len(data)
        if sha256sum == self.sha256sum:
            if size == self.size:
                return data
            else:
                raise FilesizeMismatch(size, self.size)
        else:
            raise ChecksumMismatch(sha256sum, self.sha256sum)

    def remove(self,  recursive=False, delete_nullable=False):
        """Removes the file"""
        unlink(self.filename)
        return self.delete_instance(recursive, delete_nullable)

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
