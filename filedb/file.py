"""Models for HOMEINFO's global file database"""

from os import unlink, chown, chmod
from os.path import join
from hashlib import sha512
from base64 import b64encode
from datetime import datetime

from pwd import getpwnam
from grp import getgrnam    # @UnresolvedImport

from peewee import Model, MySQLDatabase, CharField, IntegerField,\
    DoesNotExist, DateTimeField, BooleanField, PrimaryKeyField, create

from homeinfo.lib.mime import mimetype

from .config import filedb_config

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
        return '\n'.join([
            'File checksums do not match',
            ' '.join(['    expected:', str(self.expected_value)]),
            ' '.join(['    actual:  ', str(self.actual_value)])])


class FileDBModel(Model):
    """
    A basic model for the file database
    """
    class Meta:
        database = MySQLDatabase(
            'filedb',
            host=filedb_config.db['host'],
            user=filedb_config.db['user'],
            passwd=filedb_config.db['passwd'])

    id = PrimaryKeyField()


@create
class File(FileDBModel):
    """A file entry"""

    mimetype = CharField(255)
    sha512sum = CharField(128)
    size = IntegerField()   # File size in bytes
    hardlinks = IntegerField()
    created = DateTimeField()
    last_access = DateTimeField()
    accessed = IntegerField()
    public = BooleanField

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
        checksum = sha512(data).hexdigest()
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
        chmod(path, int(filedb_config.fs['mode']))
        chown(path, getpwnam(filedb_config.fs['user']).pw_uid,
              getgrnam(filedb_config.fs['group']).gr_gid)
        record.save()
        return record

    @property
    def _path(self):
        """Returns the file's path"""
        return join(filedb_config.fs['BASE_DIR'], self.sha512sum)

    def touch(self):
        """Update access counters"""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

    @property
    def data(self):
        """Reads the file's content safely"""
        data = self.read()
        checksum = sha512(data).hexdigest()
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
        self.touch()
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
