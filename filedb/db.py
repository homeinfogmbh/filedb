"""Models for HOMEINFO's global file database"""

from os import unlink, chown, chmod
from os.path import join
from hashlib import sha256
from base64 import b64encode
from datetime import datetime

from pwd import getpwnam
from grp import getgrnam    # @UnresolvedImport

from peewee import Model, MySQLDatabase, CharField, IntegerField,\
    DoesNotExist, DateTimeField, BooleanField, PrimaryKeyField, create

from homeinfo.lib.mime import mimetype
from homeinfo.lib.misc import classproperty

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
    """A basic model for the file database"""
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
    sha256sum = CharField(64)
    size = IntegerField()   # File size in bytes
    hardlinks = IntegerField()
    created = DateTimeField(null=True, default=None)
    last_access = DateTimeField(null=True, default=None)
    accessed = IntegerField(default=0)
    public = BooleanField(default=False)

    @classproperty
    @classmethod
    def mode(self):
        """Returns the default file mode"""
        return int(filedb_config.fs['mode'], 8)

    @classproperty
    @classmethod
    def user(self):
        """Returns the default file user"""
        return getpwnam(filedb_config.fs['user']).pw_uid

    @classproperty
    @classmethod
    def group(self):
        """Returns the default file user"""
        return getgrnam(filedb_config.fs['group']).gr_gid

    @classmethod
    def add(cls, f, mime=None):
        """Add a new file uniquely
        XXX: f can be either a path, file handler or bytes
        """
        try:
            # Assume file path first
            with open(f, 'rb') as file:
                data = file.read()
        except FileNotFoundError:
            try:
                # Assume file handler
                data = f.read()
            except AttributeError:
                # Finally assume bytes
                data = f
        sha256sum = sha256(data).hexdigest()
        try:
            record = cls.get(cls.sha256sum == sha256sum)
        except DoesNotExist:
            return cls._add(data, sha256sum, mime=mime)
        else:
            record.hardlinks += 1
            record.save()
            return record

    @classmethod
    def _add(cls, data, checksum, mime=None):
        """Forcibly adds a file"""
        record = cls()
        if mime is None:
            record.mimetype = mimetype(data)
        else:
            record.mimetype = mime
        record.sha256sum = checksum
        record.size = len(data)
        record.hardlinks = 1
        path = record.path
        with open(path, 'wb') as f:
            f.write(data)
        chmod(path, cls.mode)
        chown(path, cls.user, cls.group)
        record.save()
        return record

    @property
    def path(self):
        """Returns the file's path"""
        return join(filedb_config.fs['BASE_DIR'], self.sha256sum)

    def touch(self):
        """Update access counters"""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

    @property
    def data(self):
        """Reads the file's content safely"""
        data = self.read()
        checksum = sha256(data).hexdigest()
        if checksum == self.sha256sum:
            return data
        else:
            raise ChecksumMismatch(self.sha256sum, checksum)

    @property
    def base64(self):
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
        with open(self.path, 'rb') as f:
            return f.read(count)

    def unlink(self):
        """Unlinks / removes the file"""
        self.hardlinks += -1
        if not self.hardlinks:
            unlink(self.path)
            self.delete_instance()
        else:
            self.save()

    def remove(self):
        """Alias to unlink"""
        return self.unlink()

    def __str__(self):
        """Converts the file to a string"""
        return str(self.sha256sum)
