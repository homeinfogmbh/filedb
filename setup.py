#! /usr/bin/env python3

from distutils.core import setup

setup(
    name='filedb',
    version='latest',
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='info@homeinfo.de',
    maintainer='Richard Neumann',
    maintainer_email='r.neumann@homeinfo.de',
    packages=['filedb'],
    scripts=['files/filedbutil'],
    data_files=[
        ('/usr/local/bin', ['files/filedbutil']),
        ('/etc/uwsgi/apps-available', ['files/filedb.ini']),
        ('/usr/share/filedb', ['files/filedb.wsgi'])],
    description='A file database.')
