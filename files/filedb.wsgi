#! /usr/bin/env python3
"""WSGI main program for HOMIE Controller"""

from wsgilib import RestApp
from filedb.wsgi import FileDB

application = RestApp({'filedb': FileDB})
