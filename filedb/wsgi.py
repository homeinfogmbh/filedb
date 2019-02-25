"""Web service for REST-based access."""

from flask import request, Flask, Response

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
    return '/'.join((path, node))


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


@APPLICATION.route(_path('/<int:ident>'), methods=['GET'])
def get_file(ident):
    """Gets the respective file."""

    metadata = request.args.get('metadata')

    try:
        file = File.get(File.id == ident)
    except File.DoesNotExist:
        if metadata == 'exists':
            return (str(False), 404)

        return ('No such file.', 404)

    if metadata is None:
        return get_data(file)

    if metadata == 'exists':
        return str(True)

    return get_metadata(file, metadata)


@APPLICATION.route(_path('/<int:ident>'), methods=['DELETE'])
def delete_file(ident):
    """Deletes trhe respective file."""

    try:
        file = File.get(File.id == ident)
    except File.DoesNotExist:
        return ('No such file.', 400)

    return str(file.unlink())


@APPLICATION.route(_path('/<int:ident>'), methods=['PUT'])
def touch_file(ident):
    """Increases the reference counter."""

    try:
        file = File.get(File.id == ident)
    except File.DoesNotExist:
        return ('No such file.', 404)

    file.hardlinks += 1
    file.save()
    return 'Hardlinks increased.'


@APPLICATION.route(_path('/'), methods=['POST'])
def add_file():
    """Adds a new file."""

    stream = request.iter_content(chunk_size=CHUNK_SIZE)

    try:
        record = File.from_stream(stream)
    except Exception as error:  # pylint: disable=W0703
        return (str(error), 500)

    return str(record.id)
