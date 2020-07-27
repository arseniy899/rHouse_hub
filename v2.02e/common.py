
from configparser import ConfigParser
import os
import sys
from Log import Log
config = ConfigParser()
CONFIG_PATH = os.path.abspath(os.path.dirname(__file__))+'/../config.ini'
config.read(CONFIG_PATH)

#print ("Pyhton ver",sys.version_info[0])
if sys.version_info[0] >= 3:
	unicode = str

Log.start()