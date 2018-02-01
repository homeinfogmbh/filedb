"""Models for HOMEINFO's global file database."""

from base64 import b64encode
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from peewee import Model, CharField, IntegerField, DateTimeField, \
    PrimaryKeyField

from peeweeplus import MySQLDatabase
from fancylog import Logger
from mimeutil import mimetype

from filedb.config import CONFIG

__all__ = ['ChecksumMismatch', 'NoDataError', 'File']


LOGGER = Logger('filedb')
BASEDIR = Path(CONFIG['fs']['BASE_DIR'])
MODE = int(CONFIG['fs']['mode'], 8)


class ChecksumMismatch(Exception):
    """Indicates inconsistency between file checksums."""

    def __init__(self, expected_value, actual_value):
        """Sets expected and actual value."""
        super().__init__(expected_value, actual_value)
        self.expected_value = expected_value
        self.actual_value = actual_value

    def __str__(self):
        """Converts to a string."""
        return 'File checksums do not match.\nExpected {}, but got {}.'.format(
            self.expected_value, self.actual_value)


class NoDataError(ValueError):
    """Indicates that no data was provided while creating a new file."""

    def __init__(self):
        super().__init__('Refusing to create empty file.')


class FileDBModel(Model):
    """A basic model for the file database."""

    class Meta:
        database = MySQLDatabase(
            'filedb',
            host=CONFIG['db']['host'],
            user=CONFIG['db']['user'],
            passwd=CONFIG['db']['passwd'],
            closing=True)
        schema = database.database

    id = PrimaryKeyField()


class File(FileDBModel):
    """A file entry."""

    mimetype = CharField(255)
    sha256sum = CharField(64)
    size = IntegerField()   # File size in bytes.
    hardlinks = IntegerField()
    created = DateTimeField()
    last_access = DateTimeField(null=True, default=None)
    accessed = IntegerField(default=0)

    def __str__(self):
        """Converts the file to a string."""
        return str(self.sha256sum)

    @classmethod
    def add(cls, data, sha256sum=None):
        """Forcibly adds a file from bytes."""
        record = cls()
        record.mimetype = mimetype(data)
        record.sha256sum = sha256sum or sha256(data).hexdigest()
        record.created = datetime.now()
        record.size = len(data)
        record.hardlinks = 1
        record.write(data)
        record.save()
        return record

    @classmethod
    def from_bytes(cls, data):
        """Creates a unique file record from the provided bytes."""
        if not data:
            raise NoDataError()

        sha256sum = sha256(data).hexdigest()

        try:
            record = cls.get(cls.sha256sum == sha256sum)
        except cls.DoesNotExist:
            return cls.add(data, sha256sum=sha256sum)

        # Fix missing files on file system.
        if not record.exists:
            record.write(data)

        record.hardlinks += 1
        record.save()
        return record

    @classmethod
    def purge(cls, orphans):
        """Purge orphans from the filedb."""
        for orphan in orphans:
            try:
                record = cls.get(cls.id == orphan)
            except cls.DoesNotExist:
                LOGGER.warning('No such record: {}.'.format(orphan))
            else:
                # Forcibly remove record
                record.unlink(force=True)
                LOGGER.success('Unlinked: {}.'.format(record.id))

    @classmethod
    def update_hardlinks(cls, references):
        """Fixes the hard links to the given reference dictionary."""
        for ident, hardlinks in references.items():
            try:
                record = cls.get(cls.id == ident)
            except cls.DoesNotExist:
                LOGGER.warning('No such record: {}.'.format(ident))
            else:
                record.hardlinks = hardlinks
                record.save()
                LOGGER.success('Set hardlinks of #{.id} to {}'.format(
                    record, hardlinks))

    @property
    def path(self):
        """Returns the file's path."""
        return BASEDIR.joinpath(self.sha256sum)

    @property
    def data(self):
        """Reads the file's content safely."""
        data = self.read()
        checksum = sha256(data).hexdigest()

        if checksum == self.sha256sum:
            return data

        raise ChecksumMismatch(self.sha256sum, checksum)

    @property
    def base64(self):
        """Returns the file's data base64 encoded."""
        return b64encode(self.data)

    @property
    def exists(self):
        """Checks if the file exists on the system."""
        return self.path.is_file()

    @property
    def consistent(self):
        """Checks for consistency."""
        try:
            self.data
        except ChecksumMismatch:
            return False
        except FileNotFoundError:
            return False
        else:
            return True

    def touch(self):
        """Update access counters."""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

    def read(self):
        """Delegate reading to file handler."""
        self.touch()

        with self.path.open('rb') as file:
            return file.read()

    def write(self, data):
        """Writes data."""
        with self.path.open('wb') as file:
            file.write(data)

        self.path.chmod(MODE)

    def unlink(self, force=False):
        """Unlinks / removes the file."""
        self.hardlinks += -1

        if not self.hardlinks or force:
            try:
                self.path.unlink()
            except FileNotFoundError:
                LOGGER.error(
                    'Could not delete non-existing file: "{}".'.format(
                        self.path))
                return False
            except PermissionError:
                LOGGER.error(
                    'Could not delete file "{}" due to insufficient '
                    'permissions'.format(self.path))
                return False

            return self.delete_instance()

        self.save()
        return True

    def remove(self, force=False):
        """Alias to unlink."""
        return self.unlink(force=force)
