"""Web service for REST-based access."""

from functools import partial

from flask import request, Flask, Response

from wsgilib import JSON

from filedb.orm import File
from filedb.config import CONFIG, PATH, CHUNK_SIZE


__all__ = ['APPLICATION']


APPLICATION = Flask('filedb')
METADATA = {
    'sha256sum': lambda file: file.sha256sum,
    'size': lambda file: str(file.size),
    'hardlinks': lambda file: str(file.hardlinks),
    'mimetype': lambda file: file.mimetype,
    'accessed': lambda file: str(file.accessed),
    'last_access': (
        lambda file: 'never' if file.last_access is None
        else file.last_access.strftime(CONFIG['data']['time_format'])),
    'created': lambda file: file.created.strftime(
        CONFIG['data']['time_format'])}


def _path(node):
    """Returns a joint path."""

    path = PATH.rstrip('/')
    node = node.lstrip('/')
    return f'{path}/{node}'


def get_metadata(file, metadata):
    """Returns file meta data."""

    try:
        function = METADATA[metadata]
    except KeyError:
        return ('Unknown metadata.', 400)

    return str(function(file))


def get_data(file):
    """Returns actual file data."""

    try:
        if not request.args.get('nocheck', False) and not file.consistent:
            return ('Corrupted file.', 500)

        return Response(file.stream(), mimetype=file.mimetype)
    except FileNotFoundError:
        return ('File not found.', 500)
    except PermissionError:
        return ('Permission error.', 500)


def _get_file(ident):
    """Returns a file by the respective identifier."""

    if len(ident) == 64:    # Probably a SHA-256 sum.
        return File.get(File.sha256sum == ident)

    return File.get(File.id == ident)


@APPLICATION.route(_path('/<ident>'), methods=['GET'])
def get_file(ident):
    """Gets the respective file."""

    metadata = request.args.get('metadata')

    try:
        file = _get_file(ident)
    except File.DoesNotExist:
        if metadata == 'exists':
            return (str(False), 404)

        return ('No such file.', 404)

    if metadata is None:
        return get_data(file)

    if metadata == 'exists':
        return str(True)

    return get_metadata(file, metadata)


@APPLICATION.route(_path('/<ident>'), methods=['DELETE'])
def delete_file(ident):
    """Deletes trhe respective file."""

    try:
        file = _get_file(ident)
    except File.DoesNotExist:
        return ('No such file.', 400)

    return str(file.unlink())


@APPLICATION.route(_path('/<ident>'), methods=['PUT'])
def touch_file(ident):
    """Increases the reference counter."""

    try:
        file = _get_file(ident)
    except File.DoesNotExist:
        return ('No such file.', 404)

    file.hardlinks += 1
    file.save()
    return 'Hardlinks increased.'


@APPLICATION.route(_path('/'), methods=['POST'])
def add_file():
    """Adds a new file."""

    stream = iter(partial(request.stream.read, CHUNK_SIZE), b'')

    try:
        record = File.from_stream(stream)
    except Exception as error:  # pylint: disable=W0703
        return (str(error), 500)

    record.save()
    return JSON(record.to_json())
