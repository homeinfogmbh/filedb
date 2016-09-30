"""Web service for REST-based access"""

from peewee import DoesNotExist

from homeinfo.lib.wsgi import OK, Error, InternalServerError, handler, \
    RequestHandler, WsgiApp

from filedb.orm import File, ChecksumMismatch, Permission

__all__ = ['FileDBController']


class InvalidIdentifier(Exception):
    """Indicates an invalid file identifier"""

    pass


class NoIdentifier(Exception):
    """Indicates a missing identifier"""

    pass


class NotAuthenticated(Exception):
    """Indicates missing authentication"""

    pass


class FileDBRequestHandler(RequestHandler):
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
                raise InvalidIdentifier()
            else:
                return ident
        else:
            raise NoIdentifier()

    def _authenticate(self):
        """Authenticate an access"""
        try:
            key = self.query_dict['key']
        except KeyError:
            raise NotAuthenticated()
        else:
            try:
                return Permission.get(Permission.key == key)
            except DoesNotExist:
                raise NotAuthenticated()

    def get(self):
        """Gets a file by its ID"""
        qd = self.query_dict

        try:
            auth = self._authenticate()
        except NotAuthenticated:
            return Error('Not authenticated', status=400)
        else:
            if auth.perm_get:
                try:
                    ident = self._ident
                except InvalidIdentifier:
                    return Error('Invalid identifier', status=400)
                except NoIdentifier:
                    return Error('No identifier', status=400)
                else:
                    try:
                        f = File.get(File.id == ident)
                    except DoesNotExist:
                        return Error('No such file', status=400)
                    else:
                        query = qd.get('query')

                        if query is None:
                            try:
                                if qd.get('nocheck'):
                                    # Skip SHA-256 checksum check
                                    data = f.read()
                                else:
                                    data = f.data
                            except FileNotFoundError:
                                return Error('File not found', status=500)
                            except PermissionError:
                                return Error('Cannot read file', status=500)
                            except ChecksumMismatch:
                                return Error('Corrupted file', status=500)
                            else:
                                return OK(data, content_type=f.mimetype,
                                          charset=None)
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
                            tf = qd.get('time_format') or '%Y-%m-%dT%H:%M:%S'

                            if query == 'last_access':
                                last_access = f.last_access

                                if last_access is not None:
                                    return OK(last_access.strftime(tf))
                                else:
                                    return OK('never')
                            elif query == 'created':
                                created = f.created
                                return OK(created.strftime(tf))
                            else:
                                return Error('Invalid mode', status=400)
            else:
                return Error('Not authorized', status=400)

    def post(self):
        """Stores a (new) file"""
        try:
            auth = self._authenticate()
        except NotAuthenticated:
            return Error('Not authenticated', status=400)
        else:
            if auth.perm_post:
                try:
                    record = File.add(self.file.read())
                except Exception as exception:
                    return InternalServerError(str(exception))
                else:
                    return OK(str(record.id))
            else:
                return Error('Not authorized', status=400)

    def delete(self):
        """Deletes a file"""
        try:
            auth = self._authenticate()
        except NotAuthenticated:
            return Error('Not authenticated', status=400)
        else:
            if auth.perm_delete:
                try:
                    ident = self._ident
                except InvalidIdentifier:
                    return Error('Invalid identifier', status=400)
                except NoIdentifier:
                    return Error('No identifier', status=400)
                else:
                    try:
                        f = File.get(File.id == ident)
                    except DoesNotExist:
                        return Error('No such file', status=400)
                    else:
                        result = f.unlink()
                        return OK(str(result))
            else:
                return Error('Not authorized', status=400)


@handler(FileDBRequestHandler)
class FileDBController(WsgiApp):
    """WSGI controller for filedb access"""

    pass
