"""Extra hacks"""

from logging import basicConfig, getLogger
from filedb.http import FileError, FileClient

__all__ = ['FileProperty']


basicConfig()
logger = getLogger(__name__)
_param_err = ValueError('Need either file_client or key')


class SaveCallback():
    """Save callback wrapper"""

    def __init__(self, instance, field):
        self.instance = instance
        self.field = field
        self.old_save = self.instance.save

    def __call__(self, *args, **kwargs):
        while self.field.old_values:
            self.field.delete(self.field.old_values.pop())

        self.instance.__class__.save(self.instance)
        self.instance.save = self.old_save


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
        self.old_values = []

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

    def __set__(self, instance, data):
        """Stores file data within filedb using
        file_client and value from inter_field
        """
        if instance is not None:
            current_value = getattr(instance, self.integer_field.name)

            if data is not None:
                new_value = self.file_client.add(data)
            else:
                new_value = None

            setattr(instance, self.integer_field.name, new_value)

            if self.autosave:
                if current_value is not None:
                    self.delete(current_value)

                instance.save()
            else:
                if current_value is not None:
                    self.old_values.append(current_value)

                    if instance.save.__class__ is not SaveCallback:
                        instance.save = SaveCallback(instance, self)

    def delete(self, file_id):
        """Deletes the old file"""
        try:
            self.file_client.delete(file_id)
        except FileError as e:
            logger.error(e.result)
