"""Extra hacks"""

from logging import basicConfig, getLogger
from filedb.http import FileError, FileClient

__all__ = ['FileProperty']


basicConfig()
logger = getLogger(__name__)
_param_err = ValueError('Need either file_client or key')


class FileProperty():
    """File property"""

    def __init__(self, integer_field, file_client=None,
                 key=None, autosave=False):
        self.integer_field = integer_field

        if file_client is not None and key is not None:
            raise _param_err
        elif file_client is not None:
            self.file_client = file_client
        elif key is not None:
            self.file_client = FileClient(key)
        else:
            raise _param_err

        self.file_client = file_client
        self.autosave = autosave

    def __get__(self, instance, instance_type=None):
        """Returns file data from filedb using
        file_client and value from inter_field
        """
        if instance is not None:
            value = getattr(instance, self.integer_field.name)

            if value is not None:
                return self.file_client.get(value)
        else:
            return self.integer_field

    def __set__(self, instance, value):
        """Stores file data within filedb using
        file_client and value from inter_field
        """
        if instance is not None:
            try:
                self.file_client.delete(
                    getattr(instance, self.integer_field.name))
            except FileError as e:
                logger.error(e)

            if value is not None:
                value = self.file_client.add(value)

            setattr(instance, self.integer_field.name, value)

            if self.autosave:
                instance.save()
