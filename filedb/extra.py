"""Extra hacks."""

from filedb.client import add, get, delete

__all__ = ['FileProperty']


class FileProperty:
    """File property.

    Setting to file properties will save the
    DB model for reasons of consistency.
    """

    def __init__(self, integer_field, ensure_consistency=True):
        """Sets the referenced integer field, file client or key
        and optional flag whether to ensure database consistency.
        """
        self.integer_field = integer_field
        self.ensure_consistency = ensure_consistency

    def __get__(self, instance, instance_type=None):
        """Returns file data from filedb using
        file_client and value from inter_field.
        """
        if instance is not None:
            value = getattr(instance, self.integer_field.name)

            if value is not None:
                return get(value)
        else:
            return self.integer_field

    def __set__(self, instance, data):
        """Stores file data within filedb using
        file_client and value from inter_field.
        """
        if instance is not None:
            previous_value = getattr(instance, self.integer_field.name)

            if data is not None:
                new_value = add(data)
            else:
                new_value = None

            if previous_value is not None:
                delete(previous_value)

            setattr(instance, self.integer_field.name, new_value)

            if self.ensure_consistency:
                instance.save()
