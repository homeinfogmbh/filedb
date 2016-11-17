#! /usr/bin/env python3
"""WSGI main program for HOMIE Controller"""

from homeinfo.lib.wsgi import WsgiApp
from filedb.wsgi import FileDB

application = WsgiApp(FileDB)
