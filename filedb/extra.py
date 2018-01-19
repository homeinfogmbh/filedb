"""Extra hacks."""

from filedb.client import add, get, delete

__all__ = ['FileProperty']


class FileProperty:
    """A class to enable propertiy-like file
    access for peewee.Model ORM models.
    """

    def __init__(self, integer_field):
        """Sets the referenced integer field."""
        self.integer_field = integer_field

    def __get__(self, instance, instance_type=None):
        """Returns file data from filedb using
        file_client and value from inter_field.
        """
        if instance is not None:
            file_id = getattr(instance, self.integer_field.name)
            print('Got file id:', file_id, flush=True)

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
            print('Got old id:', old_id, flush=True)

            if data is not None:
                print('Adding data.', flush=True)
                new_id = add(data)
            else:
                print('Not adding data.', flush=True)
                new_id = None

            print('New ID:', new_id, flush=True)

            if old_id is not None:
                print('Deleting old file.', flush=True)
                delete(old_id)
                print('Deleted old file.', flush=True)


            print('Setting new value:', instance, self.integer_field.name,
                  new_id, flush=True)
            setattr(instance, self.integer_field.name, new_id)
            print('New value set.', flush=True)
            print('Saving instance.', flush=True)
            instance.save(only=[self.integer_field])
            print('Instance saved.', flush=True)
