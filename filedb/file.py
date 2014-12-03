"""
Abstract base classes for HOMEINFO's file database
"""
from .abc import FileDBModel
from .error import ChecksumMismatch, FilesizeMismatch
from homeinfo.util import MIMEUtil
from peewee import CharField, IntegerField
from os.path import join, basename, dirname
from os import unlink
from hashlib import sha256

__date__ = '02.12.2014'
__author__ = 'Richard Neumann <r.neumann@homeinfo.de>'
__all__ = ['File']


class File(FileDBModel):
    """
    A file entry
    """
    dirname = CharField(255)
    """The base directory of the file"""
    basename = CharField(255)
    """The file's base name"""
    mimetype = CharField(255)
    """The file's MIME type"""
    _sha256sum = CharField(69, db_column='sha256sum')
    """A SHA-256 checksum"""
    _size = IntegerField(db_column='size')
    """The file's size in bytes"""

    @classmethod
    def add(cls, path, force_insert=False):
        """Add a new File"""
        record = cls()
        record.basename = basename(path)
        record.dirname = dirname(path)
        record.mimetype = MIMEUtil.getmime(path)
        with open(path, 'rb') as file:
            data = file.read()
        record._sha256sum = str(sha256(data).hexdigest())
        record._size = len(data)
        record.save(force_insert=force_insert)

    @property
    def sha256sum(self):
        """Returns the file's SHA-256 sum"""
        return self._sha256sum

    @property
    def size(self):
        """Returns the file's size"""
        return self._size

    @property
    def name(self):
        """The file's full name / path"""
        return join(self.dirname, self.basename)

    @property
    def path(self):
        """An alias to self.name"""
        return self.name

    @property
    def data(self):
        """Returns the file's content"""
        with open(self.name, 'rb') as f:
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
        unlink(self.name)
        return self.delete_instance(recursive, delete_nullable)

    def __str__(self):
        """Converts the file to a string"""
        return self.name
