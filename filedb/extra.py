"""Extra hacks"""

from filedb.http import FileClient

__all__ = ['FileProperty']

_param_err = ValueError('Need either file_client or key')


class SaveCallback():
    """Save callback wrapper"""

    def __init__(self, instance, field):
        self.instance = instance
        self.field = field
        self.old_save = self.instance.save

    def __call__(self, *args, **kwargs):
        if self.field.new_value is not None:
            new_value = self.field.file_client.add(self.field.new_value)
            self.field.new_value = None
        else:
            new_value = None

        setattr(self.instance, self.field.integer_field.name, None)

        if self.field.old_value is not None:
            self.field.file_client.delete(self.field.old_value)
            self.field.old_value = None

        self.instance.__class__.save(self.instance)
        self.instance.save = self.old_save


class FileProperty():
    """File property"""

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
        self.old_value = None
        self.new_value = None

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
            if self.old_value is None:
                self.old_value = getattr(instance, self.integer_field.name)

            self.new_value = data

            if instance.save.__class__ is not SaveCallback:
                instance.save = SaveCallback(instance, self)

    def delete(self, file_id):
        """Deletes the old file"""
