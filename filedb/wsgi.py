"""Web service for REST-based access."""

from flask import request, make_response, Flask

from filedb.orm import ChecksumMismatch, NoDataError, File
from filedb.config import CONFIG

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
        if request.args.get('nocheck'):
            data = file.read()
        else:
            data = file.data
    except FileNotFoundError:
        return ('File not found.', 500)
    except PermissionError:
        return ('Cannot read file.', 500)
    except ChecksumMismatch:
        return ('Corrupted file.', 500)

    response = make_response(data)
    response.headers['Content-Type'] = file.mimetype
    return response


@APPLICATION.route('/<int:ident>', methods=['GET'])
def get_file(ident):
    """Gets the respective file."""

    metadata = request.args.get('metadata')

    try:
        file = File.get(File.id == ident)
    except File.DoesNotExist:
        if metadata == 'exists':
            return (str(False), 404)

        return ('No such file.', 404)
    else:
        if metadata == 'exists':
            return str(True)

    if metadata is None:
        return get_data(file)

    return get_metadata(file, metadata)


@APPLICATION.route('/<int:ident>', methods=['DELETE'])
def delete_file(ident):
    """Deletes trhe respective file."""

    try:
        file = File.get(File.id == ident)
    except File.DoesNotExist:
        return ('No such file.', 400)

    return str(file.unlink())


@APPLICATION.route('/<int:ident>', methods=['PUT'])
def touch_file(ident):
    """Increases the reference counter."""

    try:
        file = File.get(File.id == ident)
    except File.DoesNotExist:
        return ('No such file.', 404)

    file.hardlinks += 1
    file.save()
    return 'Hardlinks increased.'


@APPLICATION.route('/', methods=['POST'])
def add_file():
    """Adds a new file."""

    try:
        record = File.from_bytes(request.get_data())
    except NoDataError:
        return ('No data provided.', 400)
    except Exception as error:
        return (str(error), 500)

    return str(record.id)
