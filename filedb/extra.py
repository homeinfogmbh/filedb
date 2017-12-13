"""Extra hacks."""

from filedb.client import add, get, delete

__all__ = ['FileProperty']


class FileProperty:
    """A class to enable propertiy-like file
    access for peewee.Model ORM models.
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
            file_id = getattr(instance, self.integer_field.name)

            if file_id is not None:
                return get(file_id)

            return None

        return self

    def __set__(self, instance, data):
        """Stores file data within filedb using
        file_client and value from inter_field.
        """
        if instance is not None:
            old_id = getattr(instance, self.integer_field.name)

            if data is not None:
                new_id = add(data)
            else:
                new_id = None

            if old_id is not None:
                delete(old_id)

            setattr(instance, self.integer_field.name, new_id)

            if self.ensure_consistency:
                instance.save()
