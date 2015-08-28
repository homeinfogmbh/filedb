"""Models for HOMEINFO's global file database"""

from os import unlink, chmod
from os.path import join, isfile
from hashlib import sha256
from base64 import b64encode
from datetime import datetime
from contextlib import suppress

from pwd import getpwnam
from grp import getgrnam    # @UnresolvedImport

from peewee import Model, CharField, IntegerField, DoesNotExist,\
    DateTimeField, PrimaryKeyField, ForeignKeyField, BooleanField

from homeinfo.lib.mime import mimetype
from homeinfo.lib.misc import classproperty
from homeinfo.peewee import MySQLDatabase

from .config import filedb_config

__all__ = ['ChecksumMismatch', 'sha256sum', 'File', 'Permission']


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
            passwd=filedb_config.db['passwd'],
            closing=True)
        schema = database.database

    id = PrimaryKeyField()


class File(FileDBModel):
    """A file entry"""

    mimetype = CharField(255)
    sha256sum = CharField(64)
    size = IntegerField()   # File size in bytes
    hardlinks = IntegerField()
    created = DateTimeField()
    last_access = DateTimeField(null=True, default=None)
    accessed = IntegerField(default=0)

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
    def add(cls, f):
        """Add a new file uniquely
        XXX: f can be either a path, file handler or bytes
        """
        name = None
        try:
            # Assume file path first
            with open(f, 'rb') as fh:
                data = fh.read()
            name = f
        except FileNotFoundError:
            try:
                # Assume file handler
                data = f.read()
            except AttributeError:
                # Finally assume bytes
                data = f
            else:
                with suppress(AttributeError):
                    name = f.name
        except (OSError, TypeError):
            data = f
        mime = mimetype(data)
        sha256sum = sha256(data).hexdigest()
        try:
            file_ = cls.get(cls.sha256sum == sha256sum)
        except DoesNotExist:
            file_ = cls._add(data, sha256sum, mime)
        else:
            if not file_.exists:
                # Fix data for missing files
                with open(file_.path, 'wb') as f:
                    f.write(data)
            file_.hardlinks += 1
            file_.save()
        if name is not None:
            try:
                filename = FileName.get(FileName.name == name)
            except DoesNotExist:
                filename = FileName()
                filename.name = name
                filename.file = file_
                filename.save()
        return file_

    @classmethod
    def _add(cls, data, checksum, mime):
        """Forcibly adds a file"""
        record = cls()
        record.mimetype = mime
        record.sha256sum = checksum
        record.created = datetime.now()
        record.size = len(data)
        record.hardlinks = 1
        path = record.path
        with open(path, 'wb') as f:
            f.write(data)
        chmod(path, cls.mode)
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
    def exists(self):
        """Checks if the file exists on the system"""
        return isfile(self.path)

    @property
    def consistent(self):
        """Checks for consistency"""
        try:
            _ = self.data
        except ChecksumMismatch:
            return False
        except FileNotFoundError:
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
            path = self.path
            result = self.delete_instance()
            try:
                unlink(path)
            except FileNotFoundError:
                print('filedb:', 'Could not delete file',
                      path, '-', 'Does not exist')
                return False
            except PermissionError:
                print('filedb:', 'Could not delete file',
                      path, '-', 'Insufficient permissions')
                return False
            else:
                return result
        else:
            return self.save()

    def remove(self):
        """Alias to unlink"""
        return self.unlink()

    def __str__(self):
        """Converts the file to a string"""
        return str(self.sha256sum)


class FileName(FileDBModel):
    """Mapping of file names"""

    name = CharField(255)
    file = ForeignKeyField(
        File, db_column='file',
        related_name='names',
        on_delete='CASCADE')


class Permission(FileDBModel):
    """Keys allowed to access the filedb"""

    key = CharField(36)      # UUID4
    perm_get = BooleanField()     # read
    perm_post = BooleanField()    # write
    perm_delete = BooleanField()  # delete
    annotation = CharField(255)
