"""Extra hacks"""

from filedb.http import FileClient

__all__ = ['FileProperty']

_param_err = ValueError('Need either file_client or key')


class FileProperty():
    """File property

    XXX: Setting to file properties will save
    the DB model for reasons of consistency.
    """

    def __init__(self, integer_field, file_client=None, key=None):
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
            previous_value = getattr(instance, self.integer_field.name)

            if data is not None:
                new_value = self.file_client.add(data)
            else:
                new_value = None

            if previous_value is not None:
                self.file_client.delete(previous_value)

            setattr(instance, self.integer_field.name, new_value)
            instance.save()     # XXX: Important for consistency!
