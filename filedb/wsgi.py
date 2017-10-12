"""Web service for REST-based access."""

from peewee import DoesNotExist

from wsgilib import OK, Error, Binary, InternalServerError, ResourceHandler

from filedb.config import TIME_FORMAT
from filedb.orm import File, ChecksumMismatch, Permission

__all__ = ['FileDB']


METADATA = {
    'sha256sum': lambda file: file.sha256sum,
    'size': lambda file: str(file.size),
    'hardlinks': lambda file: str(file.hardlinks),
    'mimetype': lambda file: file.mimetype,
    'accessed': lambda file: str(file.accessed),
    'last_access': (
        lambda file: 'never' if file.last_access is None
        else file.last_access.strftime(TIME_FORMAT)),
    'created': lambda file: file.created.strftime(TIME_FORMAT)}


def get_metadata(file, metadata):
    """Returns file meta data."""

    try:
        function = METADATA[metadata]
    except KeyError:
        raise Error('Unknown metadata.', status=400) from None
    else:
        return OK(function(file))


class FileDB(ResourceHandler):
    """Handles requests for the FileDBController."""

    @property
    def ident(self):
        """Returns the appropriate file identifier."""
        try:
            return int(self.resource)
        except ValueError:
            raise Error('Invalid identifier.', status=400) from None
        except TypeError:
            raise Error('Missing identifier.', status=400) from None

    @property
    def perm(self):
        """Authenticate an access."""
        try:
            key = self.query['key']
        except KeyError:
            raise Error('Not authenticated.', status=401) from None
        else:
            try:
                return Permission.get(Permission.key == key)
            except DoesNotExist:
                raise Error('Not authorized.', status=403) from None

    @property
    def file(self):
        """Returns the respective file."""
        try:
            return File.get(File.id == self.ident)
        except DoesNotExist:
            raise Error('No such file', status=404) from None

    def _get_data(self):
        """Returns actual file data."""
        try:
            if self.query.get('nocheck'):
                data = self.file.read()
            else:
                data = self.file.data
        except FileNotFoundError:
            raise Error('File not found.', status=500) from None
        except PermissionError:
            raise Error('Cannot read file.', status=500) from None
        except ChecksumMismatch:
            raise Error('Corrupted file.', status=500) from None
        else:
            return Binary(data)

    def get(self):
        """Gets a file by its ID."""
        if self.perm.perm_get:
            metadata = self.query.get('metadata')

            if metadata is None:
                return self._get_data()

            if metadata == 'exists':
                try:
                    File.get(File.id == self.ident)
                except DoesNotExist:
                    return Error(str(False), status=404)
                else:
                    return OK(str(True))

            return get_metadata(self.file, metadata)

        raise Error('Not authorized.', status=403) from None

    def post(self):
        """Stores a (new) file."""
        if self.perm.perm_post:
            try:
                record = File.add(self.data.bytes)
            except Exception as error:
                raise InternalServerError(str(error)) from None
            else:
                return OK(str(record.id))

        raise Error('Not authorized.', status=403) from None

    def put(self):
        """Increases the reference counter."""
        if self.perm.perm_post:  # Use POST permissions for now
            try:
                file = File.get(File.id == self.ident)
            except DoesNotExist:
                raise Error('No such file.', status=404) from None
            else:
                file.hardlinks += 1
                file.save()
                return OK()

        raise Error('Not authorized.', status=403) from None

    def delete(self):
        """Deletes a file."""
        if self.perm.perm_delete:
            try:
                file = File.get(File.id == self.ident)
            except DoesNotExist:
                raise Error('No such file.', status=400) from None
            else:
                return OK(str(file.unlink()))

        raise Error('Not authorized.', status=400) from None
