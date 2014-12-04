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
    _hardlinks = IntegerField(db_column='hardlinks')
    """Amount of hardlinks on this file"""

    @classmethod
    def add(cls, path, mimetype=None):
        """Add a new File"""
        with open(path, 'rb') as file:
            data = file.read()
        sha256sum = str(sha256(data).hexdigest())
        for record in cls.select().limit(1).where(cls.sha256sum
                                                  == sha256sum):
            record._hardlinks += 1
            break
        else:
            record = cls()
            record.basename = basename(path)
            record.dirname = dirname(path)
            if mimetype is None:
                record.mimetype = MIMEUtil.getmime(path)
            else:
                record.mimetype = mimetype
            record._sha256sum = sha256sum
            record._size = len(data)
            record._hardlinks = 1
        record.save()
        return record

    @property
    def sha256sum(self):
        """Returns the file's SHA-256 sum"""
        return self._sha256sum

    @property
    def size(self):
        """Returns the file's size"""
        return self._size

    @property
    def hardlinks(self):
        """Returns the amount of hardlinks"""
        return self._hardlinks

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

    def remove(self):
        """Removes the file"""
        self._hardlinks += -1
        if not self.hardlinks:
            self._remove()
        else:
            self.save()

    def _remove(self):
        """Actually removes the file"""
        unlink(self.name)
        return self.delete_instance()

    def __str__(self):
        """Converts the file to a string"""
        return self.name
