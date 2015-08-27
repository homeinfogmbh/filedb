#! /usr/bin/env python3
"""WSGI main program for HOMIE Controller"""

from filedb.wsgi import FileDBController

application = FileDBController()
