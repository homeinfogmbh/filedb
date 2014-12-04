"""
Abstract base classes for HOMEINFO's file database
"""
from .abc import FileDBModel
from homeinfo.util import MIMEUtil
from peewee import CharField, IntegerField
from os.path import join, basename, dirname
from os import unlink
from hashlib import sha256

__date__ = '02.12.2014'
__author__ = 'Richard Neumann <r.neumann@homeinfo.de>'
__all__ = ['ChecksumMismatch', 'File']


class ChecksumMismatch(Exception):
    """Indicates inconsistency between file checksums"""
    def __init__(self, actual_value, target_value):
        """Sets acual and target value"""
        self._actual_value = actual_value
        self._target_value = target_value

    @property
    def actual_value(self):
        """Returns the actual value"""
        return self._actual_value

    @property
    def target_value(self):
        """Returns the target value"""
        return self._target_value

    def __str__(self):
        """Converts to a string"""
        return '\n'.join(['File checksums do not match',
                          ' '.join(['    actual:', str(self.actual_value)]),
                          ' '.join(['    target:', str(self.target_value)])])


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
    def add(cls, path, mimetype=None, unique=True):
        """Add a new file uniquely"""
        if unique:
            with open(path, 'rb') as file:
                data = file.read()
            sha256sum = str(sha256(data).hexdigest())
            for record in cls.select().limit(1).where(cls.sha256sum
                                                      == sha256sum):
                record._hardlinks += 1
                record.save()
                return record
        return cls._add(path, mimetype=mimetype)

    @classmethod
    def _add(cls, path, mimetype=None):
        """Forcibly adds a file"""
        with open(path, 'rb') as file:
            data = file.read()
        sha256sum = str(sha256(data).hexdigest())
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
        try:
            self.read()
        except ChecksumMismatch:
            return False
        else:
            return True

    def read(self):
        """Reads the file's content safely"""
        data = self.data
        sha256sum = str(sha256(data).hexdigest())
        if sha256sum == self.sha256sum:
            return data
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
