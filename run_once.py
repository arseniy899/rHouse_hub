#!/usr/bin/python3
from subprocess import Popen
import sys
from configparser import ConfigParser
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
#f=open("path.ini", "r")
#path =f.read()
config = ConfigParser()
config.read('config.ini')
vers = config['HubServer']['VERSION']
filename = vers+"/TCPM.py"
p = Popen("python3 " + filename +"", shell=True)
p.wait()

if sys.version_info[0] >= 3:
	input("Press Enter to continue...")
else:
	raw_input("Press Enter to continue...")