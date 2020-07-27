# -*- coding: utf-8 -*-
## prepare to import base modules
import sys
import os
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.append('../import')
from Config import Config
from DriverTCP import DriverTCP
from Msg import Msg
from Log import Log

import requests
import time
import logging
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1
camUnid = "008C"
isACKwaiting = False
def getConfBySetId(setid):
	conf = Config.get('cam_'+setid)
	conf = conf.split(',')
	
	IP 		= conf[0]
	port 	= conf[1]
	login 	= conf[2]
	passw 	= conf[3]
	camSens= conf[4]
	if(len(conf)>=6):
		up = conf[5]
	else:
		up = ''
	return (IP, port, login,passw,camSens, up)
def sendAlarm(on, setid):
	#IP,port,user,pwd,sens,
	(IP, port, login,passw,camSens, up) = getConfBySetId(setid)

	Log.i('Send/Alarm/http',"IP: %s:%s, camSens:%s" % (IP, port, camSens) )
	url = "http://%s:%s@%s/cgi-bin/hi3510/param.cgi?cmd=setmdattr&-enable=%i&-name=1&-s=%s&user=admin&pwd=admin" %(login, passw, IP, on, camSens) 
	headers  ={"Host": IP,"Authorization": "Basic YWRtaW46YWRtaW4=","User-Agent": "wget/1.12","content-type":"text"}
	Log.i('Send/Alarm/http',"Final url: "+url+"Headers:"+ str( headers) )
	req=requests.get(url, headers=headers)
	if req.status_code != 200 or "ok" not in req.text:
		Log.e('Send/Alarm/http','Error setting cam +'+str(req)+'; '+req.text)
	else:
		HUB_sendACK(setid)
		#http://192.168.2.56/web/cgi-bin/hi3510/ytup.cgi
def sendCamsUp(setid):
	i = 0
	(IP, port, login,passw,camSens, up) = getConfBySetId(setid)
	
	isOk = True
	HUB_sendACK(setid)
	if(up != ""):
		for q in range(10):
			url = "http://%s:%s@%s/web/cgi-bin/hi3510/ytup.cgi" %(login, passw, IP)
			headers  ={"Host": IP,"Authorization": "Basic YWRtaW46YWRtaW4=","User-Agent": "wget/1.12","content-type":"text"}
			Log.i('Send/UP/http',"Final url: "+url+"Headers:"+ str( headers) )
			req=requests.get(url, headers=headers)
			if req.status_code != 200 or "ok" not in req.text:
				isOk = False
				Log.e('Send/UP/http','Error setting cam +'+str(req)+'; '+req.text)
	i+=1
	#if isOk:
		#http://192.168.2.56/web/cgi-bin/hi3510/ytup.cgi

def HUB_sendACK(setid):
	global camUnid
	global isACKwaiting
	global DriverTCP
	#if(isACKwaiting):
	DriverTCP.sendAck( camUnid, setid)
	isACKwaiting = False

def onRecieve(msg):
	global isACKwaiting
	global camUnid
	global DriverTCP
	if(msg.cmd == "device.heartbeat"):
		#008C
		if(msg.unid == "0000" or msg.unid == ""):
			cams = Config.get('cams')
			cams = cams.split(',')
			for setid in cams:
				if(setid != ""):
					DriverTCP.sendMsgWithCheck(  Msg(unid = camUnid, setid = setid, cmd="device.reg.renew")  )
		else:
			DriverTCP.sendMsgWithCheck(  Msg(unid = camUnid, setid = msg.setid, cmd="device.reg.renew")  )
	elif(msg.cmd == "device.val.set"):
		isACKwaiting = True
		value = msg.value
		if '1' in value or 'true' in value or 't' in value or 'on' in value or 'вкл' in value:
			Log.i('OnRecv','Turning Wanscam Alarm ON')
			sendAlarm(1, msg.setid)
		elif '0' in value or 'false' in value or 'f' in value or 'off' in value or 'выкл' in value:
			Log.i('OnRecv','Turning Wanscam Alarm OFF')
			sendAlarm(0, msg.setid)
		elif 'up' in value or 'UP' in value:
			Log.i('OnRecv','Rotating Wanscam UP')
			sendCamsUp(msg.setid)
	elif (msg.cmd == 'device.reg.notif'):	
		setid = msg.setid
		Config.set('cam_'+setid,'')
		cams = Config.get('cams')
		if cams == "":
			Config.set('cams',setid)
		else:
			Config.set('cams',cams + "," + setid)
	#print("I got from %s|%s : %s" % (unid,setid,value) )
Config.start( {
})
DriverTCP = DriverTCP(3, onRecieve)	
time.sleep(1)


#sendHTTP(0)
#sendHTTP(1)
while True:
	time.sleep(100)
	continue