"""Extra hacks"""

from logging import basicConfig, getLogger
from filedb.http import FileError

__all__ = ['FileProperty']


basicConfig()
logger = getLogger(__name__)


class FileProperty():
    """File property"""

    def __init__(self, integer_field, file_client, saving=False):
        self.integer_field = integer_field
        self.file_client = file_client
        self.saving = saving

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return self.file_client.get(
                getattr(instance, self.integer_field.name))
        return self

    def __set__(self, instance, value):
        try:
            self.file_client.delete(getattr(instance, self.integer_field.name))
        except FileError as e:
            logger.error(e)

        print(instance)
        print(self.integer_field)
        print(self.integer_field.name)

        setattr(instance, self.integer_field.name,
                self.file_client.add(value))

        if self.saving:
            instance.save()
