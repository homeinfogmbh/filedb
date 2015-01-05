"""
Abstract base classes for HOMEINFO's file database
"""
from .abc import FileDBModel
from homeinfo.util import MIMEUtil
from peewee import CharField, IntegerField
from os.path import basename, dirname
from os import unlink
from hashlib import sha256
from base64 import b64encode

__date__ = '02.12.2014'
__author__ = 'Richard Neumann <r.neumann@homeinfo.de>'
__all__ = ['ChecksumMismatch', 'sha256sum', 'File']


class ChecksumMismatch(Exception):
    """Indicates inconsistency between file checksums"""
    def __init__(self, target_value, actual_value):
        """Sets target and actual value"""
        self._target_value = target_value
        self._actual_value = actual_value

    @property
    def target_value(self):
        """Returns the target value"""
        return self._target_value

    @property
    def actual_value(self):
        """Returns the actual value"""
        return self._actual_value

    def __str__(self):
        """Converts to a string"""
        return '\n'.join(['File checksums do not match',
                          ' '.join(['    target:', str(self.target_value)]),
                          ' '.join(['    actual:', str(self.actual_value)])])


def sha256sum(data):
    """Creates a checksum string of the respective data"""
    return str(sha256(data).hexdigest())


class File(FileDBModel):
    """
    A file entry
    """
    _name = CharField(255, db_column='name')
    """The file's full path"""
    _mimetype = CharField(255, db_column='mimetype')
    """The file's MIME type"""
    _sha256sum = CharField(69, db_column='sha256sum')
    """A SHA-256 checksum"""
    _size = IntegerField(db_column='size')
    """The file's size in bytes"""
    _hardlinks = IntegerField(db_column='hardlinks')
    """Amount of hardlinks on this file"""

    @classmethod
    def add(cls, name, mimetype=None, unique=True):
        """Add a new file uniquely"""
        if unique:
            with open(name, 'rb') as file:
                cs = sha256sum(file.read())
            for record in cls.select().limit(1).where(cls.sha256sum == cs):
                record._hardlinks += 1
                record.save()
                return record
            else:
                return cls._add(name, mimetype=mimetype)
        else:
            return cls._add(name, mimetype=mimetype)

    @classmethod
    def _add(cls, name, mimetype=None):
        """Forcibly adds a file"""
        with open(name, 'rb') as file:
            data = file.read()
        sha256sum = str(sha256(data).hexdigest())
        record = cls()
        record._name = name
        if mimetype is None:
            record._mimetype = MIMEUtil.getmime(name)
        else:
            record._mimetype = mimetype
        record._sha256sum = sha256sum
        record._size = len(data)
        record._hardlinks = 1
        record.save()
        return record

    @property
    def name(self):
        """Returns the file's name"""
        return self._name

    @property
    def mimetype(self):
        """Returns the file's MIME type"""
        return self._mimetype

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
    def path(self):
        """An alias to self.name"""
        return self.name

    @property
    def basename(self):
        """Returns the file's basename"""
        return basename(self.name)

    @property
    def dirname(self):
        """Returns the file's dirname"""
        return dirname(self.name)

    @property
    def data(self):
        """Returns the file's content"""
        with open(self.name, 'rb') as f:
            return f.read()

    @property
    def b64data(self):
        """Returns the file's data base64 encoded"""
        return b64encode(self.data)

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
        cs = sha256sum(data)
        if cs == self.sha256sum:
            return data
        else:
            raise ChecksumMismatch(cs, self.sha256sum)

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
