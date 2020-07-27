import socket
import sys
import threading
from configparser import ConfigParser
import time
import json
import errno
import os
from datetime import datetime
from Log import Log
from Msg import Msg
import select
import traceback

class DriverTCP:
	config = None 
	intfId = 0
	devicesId = []
	onRecieveCallback = None
	def __init__(self, intfId, onRecieveCallback):
		# Create a TCP/IP socket
		
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		abspath = os.path.abspath(__file__)
		dname = os.path.dirname(abspath)
		os.chdir(dname)
		config = ConfigParser()
		config.read('../config.ini')
		self.config = config
		# Connect the socket to the port where the server is listening
		self.intfId = intfId
		self.connect()
		self.outgoingMSG = []
		self.onRecieveCallback = onRecieveCallback
		threading.Thread(target=self.senderWorker).start()
	def connect(self):
		
		connected = False
		while connected == False:
			try:
				server_address = (self.config['HubServer']['IP'], int(self.config['HubServer']['PORT']) )
				self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
				self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
				self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
				self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
				self.sock.connect(server_address)
				self.sock.settimeout(10)
				self.sock.setblocking(1)
				connected = True
				
			except socket.error as e:
				Log.e('DriverTCP',"Retrying...\n%s"%e)
				self.sock.close()
				connected = False
				time.sleep(5)
		threading.Thread(target=self.thread, args=(self.intfId,)).start()
		#self.send("%s0000" % str(self.intfId).zfill(4) )
		
		for id in self.devicesId:
			self.send(id )
	def sendAck(self, unid, setid):
		Log.i('SocketWrap/sendAck',"To %s %s" % (unid,setid) )
		msg = Msg(unid = unid, setid = setid, cmd="ACK", socket = self) 
		self.sendMsg(msg)
		#time.sleep(0.1)
		#self.sendMsg(msg)
	def senderWorker(self):
		while(True):
			proceeded = []
			toRemove = []
			for i in range(len(self.outgoingMSG)):
				msg = self.outgoingMSG[i]
				if(msg not in proceeded):
					if(msg.timer % 7 == 0):
						#Log.d('SocketWrap',"Time for msg",msg.toJSON(), msg, "proceeded", msg in proceeded,'len',len(proceeded))
						if(msg.sendAttempt> 3):
							if(msg.timer > 25):
								msg.sendAttempt = -1
								msg.cmd += ".error"
								if(msg.callback != None):
									msg.callback(msg)
								toRemove.append(i)
							
						elif(msg.sendAttempt>= 0):
							Log.i('SocketWrap',"Reattempt to send message :"+msg.toJSON(), msg)
							msg.sendAttempt = msg.sendAttempt + 1
							self.sendMsg(msg)
							#try:
							#except socket.error as e:
							#	msg.cmd = "device.offline"
							#	if(msg.device != None):
							#		msg.device.isOnline = False
					proceeded.append(msg)
					#Log.d('SocketWrap',"proceeded arr", msg in proceeded,'len',len(proceeded))
					msg.timer += 1
			for i in range(len(toRemove)):
				try:
					del self.outgoingMSG[i]
				except Exception as e:
					Log.w('SocketWrap',"Unsuccessfull attempt to delete out message :"+msg.toJSON(), e)
					pass
			time.sleep(1)
	def thread(self,intfId):
		try:
			start = time.clock()
			Log.i('DriverTCP/Thread','Connected')
			
			while True:
				#try:
				if ((time.clock() - start) > 5.0):
					#Log.d('PortalConnect/Thread','Keep Alvie sent')
					self.sock.sendall("\n".encode())
					start = time.clock()
				try:
					ready_to_read, ready_to_write, in_error = select.select([self.sock,], [self.sock,], [], 5)
				except select.error:
					#conn.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
					# connection error event here, maybe reconnect
					break
				
				#if len(ready_to_read) > 0:
				data = self.sock.recv(2048).decode('utf-8')
				if not data:
					break
				if len(data)>5:
					for line in data.split("\n"):
						if len(line)>5:
							Log.i('DriverTCP/Thread','received "%s"' % line)
							from DriverTCP import Msg
							msg = Msg.fromJSONstr(self, line)
							if(msg.cmd == "ACK" or msg.cmd == "0" or msg.cmd == "device.reg.res"):
								#msg.cmd = "ACK"
								Log.i('DriverTCP/Thread',"ACK recived. Looking for awating msgs "+ msg.toJSON())
								isAckThere = False
								toRemove = []
								for i in range(len(self.outgoingMSG)):
									msgS = self.outgoingMSG[i]
									if (msgS.setid == msg.setid and msgS.unid == msg.unid):
										Log.i('DriverTCP/ACK',"Msg for ACK found:"+msgS.toJSON(), msg)
										if (msgS.callback != None):
											Log.d('DriverTCP/ACK',"Calling callback")
											msgS.callback(msg)
										if (msgS.socket != None):
											msgS.socket.sendAck(setid = msgS.setid,unid = msgS.unid)
										toRemove.append(i)
										isAckThere = True
										#break
								for i in range(len(toRemove)):
									try:
										del self.outgoingMSG[i]
									except:
										pass
								Log.i('DriverTCP/Thread',"ACK proceed complete")
								if ( (isAckThere == False or msg.cmd == "device.reg.res") and self.onRecieveCallback != None):
									Log.i('DriverTCP/Thread',"Calling callback",msg.cmd)
									self.onRecieveCallback(msg)
							elif(msg != None and self != None and self.onRecieveCallback != None):
								self.onRecieveCallback(msg)
				#else:
					#break
				#time.sleep(0.3)
				'''except ValueError as e:
					Log.e('DriverTCP/Thread',"While E: %s"%e)
				except ConnectionError as e:
					Log.e('DriverTCP/Thread',"While E: %s"%e)'''
				#except socket.error:
				#	Log.e('DriverTCP/Thread',"Closing driver: ", socket.error)
		except socket.error:
			Log.e('DriverTCP/Thread/1',"Closing socket: %s "% socket.error,traceback.format_exc())
		except Exception as e:
			exc = str(e)
			Log.e('DriverTCP/Thread/2',exc,traceback.format_exc())
		#except ValueError:
		Log.d ('DriverTCP/Thread','closing socket', ValueError)
		self.sock.close()
		self.connect()
	
	def send(self, message):
		if self.sock != None:
			if len(message) == 8 and str(self.intfId).zfill(4) not in message and message not in self.devicesId:
				self.devicesId.append(message)
			self.sock.sendall(message+'\n')
			Log.i('DriverTCP/Send','sending TO HUB:"%s"' % message)
		
	def registerDevice(self, unid):
		msg = Msg(unid = unid, value=str(1),cmd="device.reg.new")
		self.sendMsg(msg)
	def sendValueCheck(self, msg):
		if(msg.cmd != "device.reg.new" and (msg.setid == "" or msg.setid == "0000")):
			Log.e('DriverTCP/Send','sending TO HUB without setID!')
			return
		Log.i('DriverTCP/SendValCheck','sending TO HUB:"%s"' % msg.toJSON())
		self.outgoingMSG.append(msg)
		return 0
	def sendMsg(self, msg):
		if(msg.cmd != "device.reg.new" and (msg.setid == "" or msg.setid == "0000")):
			Log.e('DriverTCP/Send','sending TO HUB without setID!')
			return
		str = msg.toJSON()
		Log.i('DriverTCP/Send','sending TO HUB:"%s"' % str)
		try:
			self.sock.send(str.encode())
		except socket.error as e:
			Log.e('DriverTCP/Send','Exception: ', e)
			if e.errno == errno.EPIPE:
				time.sleep(2)
				self.sock.close()
				self.connect()
	def sendMsgWithCheck(self, msg):
		str = msg.toJSON()
		Log.i('DriverTCP/SendMsgCheck','sending TO HUB:"%s"' % str)
		self.outgoingMSG.append(msg)
