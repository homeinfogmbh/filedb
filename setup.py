#! /usr/bin/env python3

from distutils.core import setup
from peewee import OperationalError

setup(
    name='homeinfo',
    version='1.0',
    author='Richard Neumann',
    author_email='mail@richard-neumann.de',
    requires=['peewee'],
    packages=['filedb'],
    data_files=[('/usr/local/etc', ['files/etc/filedb.conf'])],
    license=open('LICENSE.txt').read(),
    description='HOMEINFO ORM database root',
    long_description=open('README.txt').read(),
)

try:
    from filedb import __tables__
except OperationalError:
    print('WARNING: No database access - Won\'t create any tables')
else:
    for table in __tables__:
        print('Creating table', table, end='\t')
        try:
            table.create_table(fail_silently=True)
        except OperationalError:
            print('[failed]')
        else:
            print('[done]')
