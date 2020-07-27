#!/usr/bin/python3
from subprocess import Popen
import sys
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')
vers = config['HubServer']['VERSION']
filename = vers+"/TCPM.py"
while True:
	print("\nStarting " + filename)
	p = Popen("python3 " + filename +"", shell=True)
	p.wait()
	if("-once" in sys.argv):
		if sys.version_info[0] >= 3:
			input("Press Enter to continue...")
		else:
			raw_input("Press Enter to continue...")
		break