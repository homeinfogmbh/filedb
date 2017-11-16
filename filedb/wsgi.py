"""Web service for REST-based access."""

from peewee import DoesNotExist

from wsgilib import OK, Error, Binary, InternalServerError, RestHandler, \
    Router, Route

from filedb.config import TIME_FORMAT
from filedb.orm import ChecksumMismatch, NoDataError, File

__all__ = ['ROUTER']


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


class FileDB(RestHandler):
    """Handles requests for the FileDBController."""

    @property
    def ident(self):
        """Returns the appropriate file identifier."""
        print(self.vars)
        return self.vars['id']

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

    def post(self):
        """Stores a (new) file."""
        try:
            record = File.from_bytes(self.data.bytes)
        except NoDataError:
            raise Error('No data provided.') from None
        except Exception as error:
            raise InternalServerError(str(error)) from None
        else:
            return OK(str(record.id))

    def put(self):
        """Increases the reference counter."""
        try:
            file = File.get(File.id == self.ident)
        except DoesNotExist:
            raise Error('No such file.', status=404) from None
        else:
            file.hardlinks += 1
            file.save()
            return OK()

    def delete(self):
        """Deletes a file."""
        try:
            file = File.get(File.id == self.ident)
        except DoesNotExist:
            raise Error('No such file.', status=400) from None
        else:
            return OK(str(file.unlink()))


ROUTER = Router(
    (Route('/filedb/[id:int]'), FileDB)
)
