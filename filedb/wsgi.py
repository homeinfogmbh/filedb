"""Web service for REST-based access."""

from functools import partial

from flask import request, Flask

from wsgilib import JSON

from filedb.config import PATH, CHUNK_SIZE
from filedb.orm import File


__all__ = ['APPLICATION']


APPLICATION = Flask('filedb')


def _path(node):
    """Returns a joint path."""

    path = PATH.rstrip('/')
    node = node.lstrip('/')
    return f'{path}/{node}'


@APPLICATION.route(_path('/<ident>'), methods=['DELETE'])
def delete_file(ident):
    """Deletes trhe respective file."""

    try:
        file = File.get(File.id == ident)
    except File.DoesNotExist:
        return ('No such file.', 400)

    return str(file.unlink())


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
