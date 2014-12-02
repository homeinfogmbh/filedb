#! /usr/bin/env python3

from distutils.core import setup

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
except:
    print('Cannot import __tables__')
else:
    for table in __tables__:
        print('Creating table', table)
        table.create_table(fail_silently=True)
