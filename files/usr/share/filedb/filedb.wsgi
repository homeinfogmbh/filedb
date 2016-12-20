#! /usr/bin/env python3
"""WSGI main program for HOMIE Controller"""

from homeinfo.lib.rest import RestApp
from filedb.wsgi import FileDB

application = RestApp({'filedb': FileDB})
