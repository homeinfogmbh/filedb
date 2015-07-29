#! /usr/bin/env python3

from distutils.core import setup

setup(
    name='homeinfo',
    version='1.0',
    author='Richard Neumann',
    author_email='mail@richard-neumann.de',
    requires=['peewee'],
    packages=['filedb'],
    data_files=[('/etc', ['files/etc/filedb.conf'])],
    license=open('LICENSE.txt').read(),
    description='HOMEINFO ORM database root',
    long_description=open('README.txt').read(),
)
