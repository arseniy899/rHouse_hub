#!/usr/bin/python

import os

import socket
from configparser import ConfigParser
import psutil
import json 
import subprocess
import threading
from functools import partial
import sys
import re
import uuid
import platform
config = ConfigParser()
CONFIG_PATH = 'config.ini'



IP = 'r-ho.ml'
#IP = '95.182.121.172'
#IP = 'localhost'
def getMaxVer():
	version = {}
	for folder in os.listdir(os.getcwd()):
		if(folder.startswith('v')):
			major, minor,letter, subNum = re.search('(\d+)\.(\d+)([a-zA-Z]*)(\d?)', folder).groups()
			version [ int(major)*1000 + int(minor)*100 + (ord(letter or 'a') - 96)*10 + int(subNum.strip() or 0)] = folder
	return version[max(version)]
def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
if('PortalConnect' in config):
	print('Error','PortalConnect',"Hub server already registed. Turn on SH service and enjoy\n")
	
else:


	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	ip = get_lan_ip()
	secret = ""
	webVer = ""
	dbIP = ""
	dbUser = ""
	dbPwd = ""
	hardID = str(uuid.UUID(int=uuid.getnode()))
	dbDB = ""
	dbCharset = "utf8"
	hubVer = getMaxVer()
	for arg in sys.argv:
		if ('secret' in arg):
			secret = arg.split("=")[1]
		elif ('webVer' in arg):
			webVer = arg.split("=")[1]
		elif ('dbIP' in arg):
			dbIP = arg.split("=")[1]
		elif ('dbUser' in arg):
			dbUser = arg.split("=")[1]
		elif ('dbPwd' in arg):
			dbPwd = arg.split("=")[1]
		elif ('dbDB' in arg):
			dbDB = arg.split("=")[1]
		elif ('dbCharset' in arg):
			dbCharset = arg.split("=")[1]
		
	try:
		
		server_address = (IP, 4045 )
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(server_address)
		hardInfo = str(platform.uname())
		data = {
			'cmd'	: 'register.new',
			'locIP' : ip,
			'webVer' : webVer,
			'hubVer' : hubVer,
			'secret' : secret,
			'hardID' : hardID,
			'hardInfo' : hardInfo,
			'dbName' : dbDB,
			'dbUser' : dbUser,
			'dbPwd' : dbPwd,
			'sshPwd' : "",
		}
		sock.sendall(json.dumps({"data":data}).encode())
		data = sock.recv(1024).decode('ascii')
		jsonObj = json.loads(data)
		if (jsonObj['errcode'] != '0'):
			print(data)
			#os._exit(1)
		else:
			data = jsonObj['data']

			configfile = open(CONFIG_PATH, 'w+')
			config.read(CONFIG_PATH)
			#{'errcode': '0', 'cmd': 'register.new', 'data': {'id': 4, 'vpnUsr': 'hub_4', 'vpnPwd': '7TIPGasGr84DBf7jYf7FJPUQoSqO9Me80zhkprmkqH8', 'token': 'mX_6pl0ZydOi4tErrlrTKIXaQdbTwdLASyYRYo8cR7w'}}
			config.add_section('HubServer')
			config.set('HubServer', 'VERSION',hubVer)
			config.set('HubServer', 'PORT','4043')
			config.set('HubServer', 'USCRIPTS_PATH','uscripts/')
			config.set('HubServer', 'TASK_CHECK_TIMOUT_MIN','15')
			config.set('HubServer', 'LOG_LEVEL','WARN')
			
			config.add_section('DataBase')
			config.set('DataBase', 'HOST',dbIP)
			config.set('DataBase', 'USER',dbUser)
			config.set('DataBase', 'PASSW',dbPwd)
			config.set('DataBase', 'DB',dbDB)
			config.set('DataBase', 'CHARSET',dbCharset)
			
			config.add_section('PortalConnect')
			config.set('PortalConnect', 'USER',data['vpnUsr'])
			config.set('PortalConnect', 'PASSW',data['vpnPwd'])
			config.set('PortalConnect', 'ID',str(data['id']))
			config.set('PortalConnect', 'webVer',webVer)
			config.set('PortalConnect', 'GATE-IP',data['gateIP'])
			config.set('PortalConnect', 'PUBLIC-IP',IP)

			config.write(configfile)
			
			f	= open("APItoken.txt","w+")
			f.write(data['token'])
			f.close() 
			
			print (json.dumps({"data":data}))
			#updating config
	except socket.error as e:
		print('Error','PortalConnect',"Register server unreachable\n%s"%e)
	
	