"""Models for HOMEINFO's global file database"""

from os import unlink, chmod
from os.path import join, isfile
from hashlib import sha256
from base64 import b64encode
from datetime import datetime

from peewee import Model, CharField, IntegerField, DoesNotExist,\
    DateTimeField, PrimaryKeyField, BooleanField

from peeweeplus import MySQLDatabase
from fancylog import Logger
from mimeutil import mimetype
from homeinfo.misc import classproperty

from filedb.config import config

__all__ = ['ChecksumMismatch', 'File', 'Permission']


logger = Logger('filedb')


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
            host=config['db']['host'],
            user=config['db']['user'],
            passwd=config['db']['passwd'],
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
        return int(config['fs']['mode'], 8)

    @classmethod
    def add(cls, f):
        """Add a new file uniquely
        XXX: f can be either a path, file handler or bytes
        """
        try:
            # Assume file path first
            with open(f, 'rb') as fh:
                data = fh.read()
        except FileNotFoundError:
            try:
                # Assume file handler
                data = f.read()
            except AttributeError:
                # Finally assume bytes
                data = f
        except (OSError, TypeError, ValueError):
            data = f

        if data:
            mime = mimetype(data)
            sha256sum = sha256(data).hexdigest()

            try:
                record = cls.get(cls.sha256sum == sha256sum)
            except DoesNotExist:
                return cls._add(data, sha256sum, mime)
            else:
                if not record.exists:
                    # Fix missing files on file system
                    with open(record.path, 'wb') as f:
                        f.write(data)

                record.hardlinks += 1
                record.save()
                return record
        else:
            raise ValueError('Refusing to create empty file')

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

    @classmethod
    def purge(cls, orphans):
        """Purge orphans from the filedb"""
        for orphan in orphans:
            try:
                record = cls.get(cls.id == orphan)
            except DoesNotExist:
                logger.warning('No such record: {}'.format(orphan))
            else:
                # Forcibly remove record
                record.unlink(force=True)
                logger.info('Unlinked: {}'.format(record.id))

    @classmethod
    def update_hardlinks(cls, references):
        """Fixes the hard links to the given reference dictionary"""
        for ident in references:
            try:
                record = cls.get(cls.id == ident)
            except DoesNotExist:
                logger.warning('No such record: {}'.format(ident))
            else:
                record.hardlinks = references[ident]
                record.save()
                logger.info(
                    'Set hard links of #{record.id} to '
                    '{record.hardlinks}'.format(record=record))

    @property
    def path(self):
        """Returns the file's path"""
        return join(config['fs']['BASE_DIR'], self.sha256sum)

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
            self.data
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

    def unlink(self, force=False):
        """Unlinks / removes the file"""
        self.hardlinks += -1

        if not self.hardlinks or force:
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
            self.save()
            return True

    def remove(self):
        """Alias to unlink"""
        return self.unlink()

    def __str__(self):
        """Converts the file to a string"""
        return str(self.sha256sum)


class Permission(FileDBModel):
    """Keys allowed to access the filedb"""

    key = CharField(36)
    get_ = BooleanField(db_column='get')
    post = BooleanField()
    delete = BooleanField()
    annotation = CharField(255)

    def __str__(self):
        """Returns a human readable representation"""
        return '{key}: {get}{post}{delete} ({annotation})'.format(
            key=self.key,
            get='g' if self.get_ else '-',
            post='p' if self.post else '-',
            delete='d' if self.delete else '-',
            annotation=self.annotation)
