"""Models for HOMEINFO's global file database."""

from base64 import b64encode
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from peewee import Model, CharField, IntegerField, DoesNotExist,\
    DateTimeField, PrimaryKeyField, BooleanField

from peeweeplus import MySQLDatabase
from fancylog import Logger
from mimeutil import mimetype

from filedb.config import CONFIG

__all__ = ['ChecksumMismatch', 'File', 'Permission']


LOGGER = Logger('filedb')
BASEDIR = Path(CONFIG['fs']['BASE_DIR'])
MODE = int(CONFIG['fs']['mode'], 8)


class ChecksumMismatch(Exception):
    """Indicates inconsistency between file checksums."""

    def __init__(self, expected_value, actual_value):
        """Sets expected and actual value"""
        super().__init__(expected_value, actual_value)
        self._expected_value = expected_value
        self._actual_value = actual_value

    @property
    def expected_value(self):
        """Returns the expected value."""
        return self._expected_value

    @property
    def actual_value(self):
        """Returns the actual value."""
        return self._actual_value

    def __str__(self):
        """Converts to a string."""
        return '\n'.join([
            'File checksums do not match',
            ' '.join(['    expected:', str(self.expected_value)]),
            ' '.join(['    actual:  ', str(self.actual_value)])])


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

    @classmethod
    def add(cls, fileobj):
        """Add a new file uniquely."""
        try:
            # Assume file path first
            with open(fileobj, 'rb') as file:
                data = file.read()
        except FileNotFoundError:
            try:
                # Assume file handler
                data = fileobj.read()
            except AttributeError:
                # Finally assume bytes
                data = fileobj
        except (OSError, TypeError, ValueError):
            data = fileobj

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
                    with open(str(record.path), 'wb') as file:
                        file.write(data)

                record.hardlinks += 1
                record.save()
                return record
        else:
            raise ValueError('Refusing to create empty file')

    @classmethod
    def _add(cls, data, checksum, mime):
        """Forcibly adds a file."""
        record = cls()
        record.mimetype = mime
        record.sha256sum = checksum
        record.created = datetime.now()
        record.size = len(data)
        record.hardlinks = 1
        path = record.path

        with open(str(path), 'wb') as file:
            file.write(data)

        path.chmod(MODE)
        record.save()
        return record

    @classmethod
    def purge(cls, orphans):
        """Purge orphans from the filedb."""
        for orphan in orphans:
            try:
                record = cls.get(cls.id == orphan)
            except DoesNotExist:
                LOGGER.warning('No such record: {}'.format(orphan))
            else:
                # Forcibly remove record
                record.unlink(force=True)
                LOGGER.info('Unlinked: {}'.format(record.id))

    @classmethod
    def update_hardlinks(cls, references):
        """Fixes the hard links to the given reference dictionary."""
        for ident in references:
            try:
                record = cls.get(cls.id == ident)
            except DoesNotExist:
                LOGGER.warning('No such record: {}'.format(ident))
            else:
                record.hardlinks = references[ident]
                record.save()
                LOGGER.info(
                    'Set hard links of #{record.id} to '
                    '{record.hardlinks}'.format(record=record))

    @property
    def path(self):
        """Returns the file's path."""
        return BASEDIR.joinpath(self.sha256sum)

    def touch(self):
        """Update access counters."""
        self.accessed += 1
        self.last_access = datetime.now()
        self.save()

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

    def read(self, count=None):
        """Delegate reading to file handler."""
        self.touch()

        with open(str(self.path), 'rb') as file:
            return file.read(count)

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

    def __str__(self):
        """Converts the file to a string."""
        return str(self.sha256sum)


class Permission(FileDBModel):
    """Keys allowed to access the filedb."""

    key = CharField(36)
    perm_get = BooleanField(db_column='get')
    perm_post = BooleanField(db_column='post')
    perm_delete = BooleanField(db_column='delete')
    annotation = CharField(255)

    def __str__(self):
        """Returns a human readable representation."""
        return '{}: {}{}{} ({})'.format(
            self.key, 'g' if self.perm_get else '-',
            'p' if self.perm_post else '-', 'd' if self.perm_delete else '-',
            self.annotation)

    def to_dict(self):
        """Returns a JSON compliant dictionary."""
        return {
            'key': self.key,
            'get': self.perm_get,
            'post': self.perm_post,
            'delete': self.perm_delete,
            'annotation': self.annotation}
