"""
Basic HIS system configuration
"""
from configparser import ConfigParser

__date__ = '02.12.2014'
__author__ = 'Richard Neumann <r.neumann@homeinfo.de>'
__all__ = ['db', 'fs']

CONFIG_FILE = '/usr/local/etc/filedb.conf'
config = ConfigParser()
config.read(CONFIG_FILE)
db = config['db']
