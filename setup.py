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
    scripts=['files/filedbd', 'files/filedbutil'],
    data_files=[('/usr/lib/systemd/system', ['files/filedb.service'])],
    description='A file database.')
