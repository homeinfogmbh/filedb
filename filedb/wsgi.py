"""Web service for REST-based access"""

from peewee import DoesNotExist

from homeinfo.lib.wsgi import OK, Error, Binary, InternalServerError, \
    RequestHandler

from filedb.orm import File, ChecksumMismatch, Permission

__all__ = ['FileDB']


class FileDB(RequestHandler):
    """Handles requests for the FileDBController"""

    @property
    def _ident(self):
        """Returns the appropriate file identifier"""
        path = self.path

        if len(path) == 2:
            ident_str = self.path[-1]

            try:
                ident = int(ident_str)
            except (TypeError, ValueError):
                raise Error('Invalid identifier', status=400) from None
            else:
                return ident
        else:
            raise Error('No identifier', status=400) from None

    def _authenticate(self):
        """Authenticate an access"""
        try:
            key = self.query['key']
        except KeyError:
            raise Error('Not authenticated', status=401) from None
        else:
            try:
                return Permission.get(Permission.key == key)
            except DoesNotExist:
                raise Error('Not authorized', status=403) from None

    def get(self):
        """Gets a file by its ID"""
        if self._authenticate().perm_get:
            try:
                f = File.get(File.id == self._ident)
            except DoesNotExist:
                raise Error('No such file', status=400) from None
            else:
                query = self.query.get('query')

                if query is None:
                    try:
                        if self.query.get('nocheck'):
                            # Skip SHA-256 checksum check
                            data = f.read()
                        else:
                            data = f.data
                    except FileNotFoundError:
                        raise Error('File not found', status=500) from None
                    except PermissionError:
                        raise Error('Cannot read file', status=500) from None
                    except ChecksumMismatch:
                        raise Error('Corrupted file', status=500) from None
                    else:
                        return Binary(data)
                elif query in ['checksum', 'sha256sum']:
                    return OK(f.sha256sum)
                elif query == 'size':
                    return OK(str(f.size))
                elif query in ['links', 'hardlinks']:
                    return OK(str(f.hardlinks))
                elif query in ['type', 'mimetype']:
                    return OK(f.mimetype)
                elif query in ['accesses', 'accessed']:
                    return OK(str(f.accessed))
                else:  # times
                    tf = self.query.get('time_format', '%Y-%m-%dT%H:%M:%S')

                    if query == 'last_access':
                        if f.last_access is not None:
                            return OK(f.last_access.strftime(tf))
                        else:
                            return OK('never')
                    elif query == 'created':
                        return OK(f.created.strftime(tf))
                    else:
                        raise Error('Invalid mode', status=400) from None
        else:
            raise Error('Not authorized', status=403) from None

    def post(self):
        """Stores a (new) file"""
        if self._authenticate().perm_post:
            try:
                record = File.add(self.data)
            except Exception as e:
                return InternalServerError(str(e))
            else:
                return OK(str(record.id))
        else:
            raise Error('Not authorized', status=403) from None

    def delete(self):
        """Deletes a file"""
        if self._authenticate().perm_delete:
            try:
                f = File.get(File.id == self._ident)
            except DoesNotExist:
                raise Error('No such file', status=400) from None
            else:
                return OK(str(f.unlink()))
        else:
            raise Error('Not authorized', status=400) from None
