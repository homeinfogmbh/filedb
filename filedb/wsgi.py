"""Web service for REST-based access."""

from functools import partial

from flask import request, Flask

from wsgilib import JSON

from filedb.config import PATH, CHUNK_SIZE
from filedb.orm import File
from filedb.streaming import stream


__all__ = ['APPLICATION']


APPLICATION = Flask('filedb')


def _path(node):
    """Returns a joint path."""

    path = PATH.rstrip('/')
    node = node.lstrip('/')
    return f'{path}/{node}'


def get_data(file):
    """Returns actual file data."""

    try:
        if not request.args.get('nocheck', False) and not file.consistent:
            return ('Corrupted file.', 500)

        return stream(file)
    except FileNotFoundError:
        return ('File not found.', 500)
    except PermissionError:
        return ('Permission error.', 500)


def get_file(ident):
    """Returns a file by the respective identifier."""

    if len(ident) == 64:    # Probably a SHA-256 sum.
        return File.get(File.sha256sum == ident)

    return File.get(File.id == ident)


@APPLICATION.route(_path('/<ident>'), methods=['GET'])
def get_bytes(ident):
    """Gets the respective file."""

    try:
        file = get_file(ident)
    except File.DoesNotExist:
        return ('No such file.', 404)

    return get_data(file)


@APPLICATION.route(_path('/meta/<ident>'), methods=['GET'])
def get_metadata(ident):
    """Gets the respective file."""

    try:
        file = get_file(ident)
    except File.DoesNotExist:
        return ('No such file.', 404)

    return JSON(file.to_json())


@APPLICATION.route(_path('/<ident>'), methods=['DELETE'])
def delete_file(ident):
    """Deletes trhe respective file."""

    try:
        file = get_file(ident)
    except File.DoesNotExist:
        return ('No such file.', 400)

    return str(file.unlink())


@APPLICATION.route(_path('/<ident>'), methods=['PUT'])
def touch_file(ident):
    """Increases the reference counter."""

    try:
        file = get_file(ident)
    except File.DoesNotExist:
        return ('No such file.', 404)

    file.hardlinks += 1
    file.save()
    return 'Hardlinks increased.'


@APPLICATION.route(_path('/'), methods=['POST'])
def add_file():
    """Adds a new file."""

    upload_stream = iter(partial(request.stream.read, CHUNK_SIZE), b'')

    try:
        record = File.from_stream(upload_stream)
    except Exception as error:  # pylint: disable=W0703
        return (str(error), 500)

    record.save()
    return JSON(record.to_json())
