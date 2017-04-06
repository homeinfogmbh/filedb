#! /usr/bin/env python3

from distutils.core import setup

setup(
    name='filedb',
    version='latest',
    author='Richard Neumann',
    packages=['filedb'],
    data_files=[
        ('/etc', ['files/etc/filedb.conf']),
        ('/etc/uwsgi/apps-available',
         ['files/etc/uwsgi/apps-available/filedb.ini']),
        ('/usr/share/filedb',
         ['files/usr/share/filedb/filedb.wsgi'])],
    license=open('LICENSE.txt').read(),
    description='HOMEINFO ORM database root')
