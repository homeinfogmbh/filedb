"""Web service for REST-based access"""

from peewee import DoesNotExist

from wsgilib import OK, Error, Binary, InternalServerError, ResourceHandler

from filedb.orm import File, ChecksumMismatch, Permission

__all__ = ['FileDB']


class FileDB(ResourceHandler):
    """Handles requests for the FileDBController"""

    @property
    def _ident(self):
        """Returns the appropriate file identifier"""
        try:
            return int(self.resource)
        except ValueError:
            raise Error('Invalid identifier.', status=400) from None
        except TypeError:
            raise Error('Missing identifier.', status=400) from None

    @property
    def _perm(self):
        """Authenticate an access"""
        try:
            key = self.query['key']
        except KeyError:
            raise Error('Not authenticated.', status=401) from None
        else:
            try:
                return Permission.get(Permission.key == key)
            except DoesNotExist:
                raise Error('Not authorized.', status=403) from None

    def get(self):
        """Gets a file by its ID"""
        if self._perm.get_:
            try:
                f = File.get(File.id == self._ident)
            except DoesNotExist:
                raise Error('No such file', status=404) from None
            else:
                metadata = self.query.get('metadata')
                time_format = self.query.get(
                    'time_format', '%Y-%m-%dT%H:%M:%S')

                if metadata is None:
                    try:
                        if self.query.get('nocheck'):
                            # Skip SHA-256 checksum check
                            data = f.read()
                        else:
                            data = f.data
                    except FileNotFoundError:
                        raise Error('File not found.', status=500) from None
                    except PermissionError:
                        raise Error('Cannot read file.', status=500) from None
                    except ChecksumMismatch:
                        raise Error('Corrupted file.', status=500) from None
                    else:
                        return Binary(data)
                elif metadata == 'sha256sum':
                    return OK(f.sha256sum)
                elif metadata == 'size':
                    return OK(str(f.size))
                elif metadata == 'hardlinks':
                    return OK(str(f.hardlinks))
                elif metadata == 'mimetype':
                    return OK(f.mimetype)
                elif metadata == 'accessed':
                    return OK(str(f.accessed))
                elif metadata == 'last_access':
                    if f.last_access is not None:
                        return OK(f.last_access.strftime(time_format))
                    else:
                        return OK('never')
                elif metadata == 'created':
                    return OK(f.created.strftime(time_format))
                else:
                    raise Error('Unknown metadata.', status=400) from None
        else:
            raise Error('Not authorized.', status=403) from None

    def post(self):
        """Stores a (new) file"""
        if self._perm.post:
            try:
                record = File.add(self.data)
            except Exception as e:
                raise InternalServerError(str(e)) from None
            else:
                return OK(str(record.id))
        else:
            raise Error('Not authorized.', status=403) from None

    def put(self):
        """Increases the reference counter"""
        if self._perm.post:  # Use POST permissions for now
            try:
                f = File.get(File.id == self._ident)
            except DoesNotExist:
                raise Error('No such file.', status=404) from None
            else:
                f.hardlinks += 1
                f.save()
                return OK()
        else:
            raise Error('Not authorized.', status=403) from None

    def delete(self):
        """Deletes a file"""
        if self._perm.delete:
            try:
                f = File.get(File.id == self._ident)
            except DoesNotExist:
                raise Error('No such file.', status=400) from None
            else:
                return OK(str(f.unlink()))
        else:
            raise Error('Not authorized.', status=400) from None
