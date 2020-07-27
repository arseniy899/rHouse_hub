import socket
import sys
import os
import atexit
from SocketWrap import SocketWrap
from DB import DB
import common
import select
from common import Log
from API import API
from Tasker import Task
from subprocess import check_output
from PortalConnect import PortalConnect
import time
import threading

HOST = '' # all availabe interfaces
PORT = int(common.config['HubServer']['PORT']) # arbitrary non privileged port 
socketWraps = {}

PortalConnect.start()
Log.i("TCPM","Continue booting of HUB")	
Log.i('PortalConnect', "Started in TCPM")
lastWiFiSockId = 32
DB.sqlUpdate("""UPDATE `units_run` SET `alive` = '0'""" )
#SocketWrap.messagesWaitingACK = dict()
SocketWrap.onlineUnits = {}
SocketWrap.allUnits = {}
SocketWrap.getAllUnitsFromDB();
Task.start()
try:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	DB.registerEvent('','','System','Hub TCP server started...')
except Exception as msg:
	Log.e('TCPM',"Could not create socket. Error Code: "+ str(msg[0])+ "Error: "+ msg[1])
	DB.registerEvent('','','System','Error starting hub TCP server: %i %s' % (msg[0],msg[1] ) )
	sys.exit(0)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

Log.i('TCPM',"Socket Created")
try:
	s.bind((HOST, PORT))
	Log.i('TCPM', "Socket Bound to port " + str(PORT))
except Exception as msg:
	Log.e('TCPM', "Bind Failed. Error Code: {} Error: {}".format(str(msg[0]), msg[1]))
	DB.registerEvent('','','System','Error binding socket for TCP server: %i %s' % (msg[0],msg[1] ) )
	sys.exit()
s.listen(1)
API.start()
def exit_handler():
	# Stopping server
	s.close()
	API.stop()
	DB.registerEvent('','','System','Stopped hub TCP server' )
	DB.close()
atexit.register(exit_handler)

Log.i('TCPM', "Listening...")
s.setblocking(1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
#s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
#s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
#s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
def self_broadcast():
	while True:
		try:
			cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			cs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			cs.sendto( ('R_HO.HUB.IP='+PortalConnect.get_lan_ip()).encode(), ('255.255.255.255', 54545))
		except:
			continue
		time.sleep(3)
threading.Thread(target = self_broadcast).start()
try:
	while True:
		conn, addr = s.accept()
		
		Log.i('TCPM', "Connected from " + addr[0] + ":" + str(addr[1]))
		SocketWrap(conn,addr[0], str(addr[1]))
		
except KeyboardInterrupt:
	#exit_handler()
	os._exit(1)

