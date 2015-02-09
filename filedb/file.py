"""Models for HOMEINFO's global file database"""

from os import unlink, chown, chmod
from hashlib import sha512
from base64 import b64encode
from datetime import datetime
from os.path import join
from peewee import CharField, IntegerField, DoesNotExist, DateTimeField
from homeinfo.lib import mimetype
from .abc import FileDBModel
from .config import fs
from pwd import getpwnam
from grp import getgrnam    # @UnresolvedImport

__date__ = '02.12.2014'
__author__ = 'Richard Neumann <r.neumann@homeinfo.de>'
__all__ = ['ChecksumMismatch', 'sha256sum', 'File']


class ChecksumMismatch(Exception):
    """Indicates inconsistency between file checksums"""
    def __init__(self, expected_value, actual_value):
        """Sets expected and actual value"""
        self._expected_value = expected_value
        self._actual_value = actual_value

    @property
    def expected_value(self):
        """Returns the expected value"""
        return self._expected_value

    @property
    def actual_value(self):
        """Returns the actual value"""
        return self._actual_value

    def __str__(self):
        """Converts to a string"""
        return '\n'.join(['File checksums do not match',
                          ' '.join(['    expected:',
                                    str(self.expected_value)]),
                          ' '.join(['    actual:  ',
                                    str(self.actual_value)])])


def sha512sum(data):
    """Creates a checksum string of the respective data"""
    return str(sha512(data).hexdigest())


class File(FileDBModel):
    """A file entry"""

    mimetype = CharField(255)
    """The file's MIME type"""
    sha512sum = CharField(128)
    """A SHA-512 checksum"""
    size = IntegerField()
    """The file's size in bytes"""
    hardlinks = IntegerField()
    """Amount of hardlinks on this file"""
    created = DateTimeField()
    """When was the file stored in the database"""
    last_access = DateTimeField()
    """When has the file been read the last time"""
    accessed = IntegerField()
    """How often was the file read"""

    @classmethod
    def add(cls, file_fh_data, mime=None):
        """Add a new file uniquely"""
        try:
            with open(file_fh_data, 'rb') as file:
                data = file.read()
        except FileNotFoundError:
            try:
                data = file_fh_data.read()
            except AttributeError:
                data = file_fh_data
        checksum = sha512sum(data)
        try:
            record = cls.get(cls.sha512sum == checksum)
        except DoesNotExist:
            return cls._add(data, mime=mime)
        else:
            record._hardlinks += 1
            record.save()
            return record

    @classmethod
    def _add(cls, data, checksum, mime=None):
        """Forcibly adds a file"""
        record = cls()
        if mime is None:
            record._mimetype = mimetype(data)
        else:
            record._mimetype = mime
        record.sha512sum = checksum
        record.size = len(data)
        record.hardlinks = 1
        path = record._path
        with open(path, 'wb') as f:
            f.write(data)
        chmod(path, int(fs.get('mode')))
        chown(path, getpwnam(fs.get('user')).pw_uid,
              getgrnam(fs.get('group')).gr_gid)
        record.save()
        return record

    @property
    def _path(self):
        """Returns the file's path"""
        return join(fs.get('BASE_DIR'), self.sha512sum)

    def _touch(self):
        """Update access counters"""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

    @property
    def data(self):
        """Reads the file's content safely"""
        data = self.read()
        checksum = sha512sum(data)
        if checksum == self.sha512sum:
            return data
        else:
            raise ChecksumMismatch(self.sha512sum, checksum)

    @property
    def b64data(self):
        """Returns the file's data base64 encoded"""
        return b64encode(self.data)

    @property
    def consistent(self):
        """Checks for consistency"""
        try:
            _ = self.data
        except ChecksumMismatch:
            return False
        else:
            return True

    def read(self, count=None):
        """Delegate reading to file handler"""
        self._touch()
        with open(self._path, 'rb') as f:
            return f.read(count)

    def unlink(self):
        """Unlinks / removes the file"""
        self._hardlinks += -1
        if not self.hardlinks:
            unlink(self.name)
            self.delete_instance()
        else:
            self.save()

    def remove(self):
        """Alias to unlink"""
        return self.unlink()

    def __str__(self):
        """Converts the file to a string"""
        return str(self.sha512sum)
