from Device import Device
from DB import DB
import common
import threading
from time import localtime, strftime, sleep
import time
import json
import socket
from common import Log
from Msg import Msg
import sys, traceback
import select
class SocketWrap:
	interface 	= 0
	#ip		= ''
	units	= {}
	#onlineUnits = {}
	#allUnits = {}
	allSockets = []
	tcpConn	= None
	IP = ""
	port = ""
	#outgoingMSG = []
	def __init__(self, tcpConn, IP, port):
		self.tcpConn = tcpConn
		self.IP = self.IP
		self.port = self.port
		SocketWrap.allSockets.append(self)
		self.outgoingMSG = []
		threading.Thread(target = self.reciveWorker).start()
		threading.Thread(target = self.senderWorker).start()
	def onClientConnected(self, unid, setid):
		if setid == '0000':
			device = self.registerDevice(unid)
		else:
			allId = unid+''+setid
			#device = Device(unid, setid, self)
			if allId not in SocketWrap.allUnits:
				Log.e('SocketWrap',"Not able to egt device ID")
				return
			device = SocketWrap.allUnits[allId]
			device.mySocketWrap = self
			device.isOnline = True
			self.units[allId] = device
			SocketWrap.onlineUnits[allId] = device
			Log.i('SocketWrap',"Dir: "+device.direction+ ", nedStVal = %s" % device.needSetValue)
			if 'O' in device.direction and device.needSetValue == True:
				Log.i('SocketWrap',"Sending last missed value")
				device.setValue(device.lastValue)
				
			DB.registerEvent(unid,setid,'SocketWrap','Known device connected.'	)
		return device
	def senderWorker(self):
		while(True):
			proceeded = []
			toRemove = []
			for i in range(len(self.outgoingMSG)):
				msg = self.outgoingMSG[i]
				if(msg not in proceeded):
					if(msg.timer % 7 == 0):
						Log.d('SocketWrap',"Time for msg",msg.toJSON(), msg, "proceeded", msg in proceeded,'len',len(proceeded))
						if(msg.sendAttempt> 3):
							if(msg.timer > 25):
								#DB.addAlert(msg.unid, msg.setid,1006, msg = msg.toJSON())
								msg.sendAttempt = -1
								msg.cmd += ".error"
								if(msg.callback != None):
									msg.callback(msg)
								toRemove.append(i)
							
						else:
							Log.i('SocketWrap',"Reattempt to send message :"+msg.toJSON(), msg)
							msg.sendAttempt = msg.sendAttempt + 1
							self.sendMsg(msg)
							
					proceeded.append(msg)
					Log.d('SocketWrap',"proceeded arr", msg in proceeded,'len',len(proceeded))
					msg.timer += 1
			for i in range(len(toRemove)):
				try:
					del self.outgoingMSG[i]
				except:
					pass
			time.sleep(1)
	def reciveWorker(self):
		self.tcpConn.settimeout(10)
		try:
			if self.IP == '127.0.0.1' or self.IP == 'localhost':
				self.interface = 0
			else:
				self.interface = 1
			self.tcpConn.setblocking(1)
			
			self.sendMsg(Msg(cmd="device.heartbeat", socket = self, setid = "0001") )
			#self.tcpConn.setblocking(0)
			i =0
			start = time.clock()
			while True:
				ready = False
				sleep(0.002)
				try:
					
					if ((time.clock() - start) > 5.0):
						self.tcpConn.sendall("\n".encode())
						start = time.clock()
					data = self.tcpConn.recv(2048).decode('utf-8')
					if(len(data) > 3):
						for line in data.split("\n"):
							if(line != ""):
								Log.i('SocketWrap',"Received MSG: " + line)
								msg = Msg.fromJSONstr(self, line)
								if(msg.cmd == "ACK" or msg.cmd == "0"):
									msg.cmd = "ACK"
									Log.i('SocketWrap',"ACK recived. Looking for awating msgs "+ msg.toJSON())
									toRemove = []
									for i in range(len(self.outgoingMSG)):
										if( i > len(self.outgoingMSG)):
											break
										msgS = self.outgoingMSG[i]
										if (msgS.setid == msg.setid and msgS.unid == msg.unid):
											Log.i('SocketWrap/ACK',"Msg for ACK found:"+msgS.toJSON(), msg)
											if (msgS.callback != None):
												Log.d('SocketWrap/ACK',"Calling callback")
												msgS.callback(msg)
											if (msgS.socket != None):
												msgS.socket.sendAck(setid = msgS.setid,unid = msgS.unid)
											toRemove.append(i)
											#break
									for i in range(len(toRemove)):
										try:
											del self.outgoingMSG[i]
										except:
											pass
									Log.i('SocketWrap',"ACK proceed complete")
								elif (msg.cmd == "device.reg.new"  or msg.cmd == "10"):
									msg.cmd = "device.reg.new"
									self.registerDevice(msg.unid)
									#msg.callback = self.sendMsg
									#SocketWrap.outgoingMSG.append(msg) 
								elif (msg.cmd == "device.reg.renew" or msg.cmd == "device.heartbeat"  or msg.cmd == "12"  or msg.cmd == "1"):
									Log.i('SocketWrap',"Got MSG: "+msg.toJSON())
									allId = msg.unid+''+msg.setid
									if allId not in SocketWrap.allUnits:
										Log.e('SocketWrap',"Not able to find device by ID "+allId+" . Registering as new")
										self.registerDevice(msg.unid,msg.setid)
										continue
									msg.device = SocketWrap.allUnits[allId]
									device = msg.device
									device.mySocketWrap = self
									device.setIsOnline(True)
									self.units[allId] = device
									SocketWrap.onlineUnits[allId] = device
									if(msg.cmd == "12"):
										msg.cmd = "device.reg.renew"
									elif(msg.cmd == "1"):
										msg.cmd = "device.heartbeat"
									if (msg.socket != None):
										msg.socket.sendAck(setid = msg.setid,unid = msg.unid)
									#else:
									self.sendAck(setid = msg.setid,unid = msg.unid)
									#if(device.isOnline ==False):
									Log.i('SocketWrap',"Dir: "+device.direction+ ", nedStVal = %s" % device.needSetValue)
									
									if 'O' in device.direction and device.needSetValue == True:
										Log.i('SocketWrap',"Sending last missed value")
										device.needSetValue = False
										#self.tcpConn.send(allId+''+device.parseFormatToValue(device.lastValue)+'\r\n')
										
										DB.registerEvent(device.unid,device.setid,'SocketWrap','device register renew.'	)
										device.setValue(device.lastValue)
										msg.callback = self.onNeedSetValueAck
										#SocketWrap.outgoingMSG.append(msg) 
									
										
								elif (msg.cmd == "device.val.input"  or msg.cmd == "20"):
									msg.cmd = "device.val.input"
									self.sendAck(setid = msg.setid,unid = msg.unid)
									self.onValueRecieved(msg.unid,msg.setid,msg.value)
								elif (msg.cmd == "device.val.set"  or msg.cmd == "22"):
									msg.cmd = "device.val.set"
									allId = msg.unid+''+msg.setid
									if allId not in SocketWrap.allUnits:
										Log.e('SocketWrap',"Not able to get device ID")
										return
									device = SocketWrap.allUnits[allId]
									Log.d('DeviceSetVal',"[1]")
									device.setValue(msg.value, callback = sendMsg)
									Log.d('DeviceSetVal',"[2]")
									msg.callback = self.sendMsg
									#SocketWrap.outgoingMSG.append(msg) 
									#socketWrap.onValueRecieved(msg.unid,msg.setid,value)
									Log.d('DeviceSetVal',"[3]")
						Log.i('SocketWrap',"MSG proceed complete")
				except ValueError as e:
					Log.e('SocketWrap/ValueError',"While E "+str(e),traceback.format_exc())
				'''except socket.timeout: 
					#self.tcpConn.setblocking(0)
					try:
						if i == 5:
							i = 0
							self.tcpConn.send("\n")
						i+=1
					except:
						break
					#pass
				except socket.error as e:
					#print("[D] While E ", e)
					try:
						if i == 25:
							i = 0
							#self.tcpConn.send("\n")
							self.tcpConn.send(" ")
						i+=1
					except:
						break
					#pass
				
				except Exception as e:
					exc = str(e)
					Log.e('SocketWrap/ValueError',exc)'''
		#finally:
		except socket.error:
			Log.e('SocketWrap/Thread/1',"Closing socket: %s "% socket.error,traceback.format_exc())
		except Exception as e:
			exc = str(e)
			Log.e('SocketWrap/Thread/2',exc,traceback.format_exc())
		Log.i('SocketWrap',"Closing driver ")
		
		#self.tcpConn.shutdown(2)
		self.tcpConn.close()
		self.onClientDisConnected()
		Log.i('SocketWrap',"Client disConnected: " + self.IP + ":" + self.port)
		if 'socketWrap' in locals():
			del self
		
	def onNeedSetValueAck(self, msg):
		DB.sqlUpdate("""
			UPDATE `units_run`
				SET    `needSetValue` = 0
				WHERE  `setid` = '%s'
					   AND `unid` = '%s'
			""" % (msg.setid, msg.unid ) )
	
	def onClientDisConnected(self):
		for key, value in self.units.items():
			if key in SocketWrap.onlineUnits:
				if key in SocketWrap.allUnits:
					SocketWrap.allUnits[key].isOnline = False
				#if key in SocketWrap.onlineUnits:
				#	del SocketWrap.onlineUnits[key]
				
		SocketWrap.allSockets.remove(self)
	@staticmethod
	def getAllUnitsFromDB():
		sql = """
		SELECT 	units_run.lastValue,
				units_run.id,
				units_run.unid,
				units_run.setid,
				units_run.lastTime,
				units_run.needSetValue,
				units_run.name,
				units_def.description,
				units_def.units,
				units_def.direction,
				units_def.valueType,
				units_def.timeout
		FROM   `units_run`
			   LEFT OUTER JOIN units_def ON units_def.unid = units_run.unid
			"""
		#print(sql)
		data = DB.sqlSelect(sql)
		if len(data) == 0:
			print("NOTE: No any devices where registed yet!")
			
		else:
			for row in data:
				unid = row['unid']
				setid = row['setid']
				device = Device(unid, setid, None, False);
				device.id = row['id']
				device.lastTime = row['lastTime']
				device.lastValue = row['lastValue']
				device.needSetValue = int(row['needSetValue']) == 1
				device.name = row['name']
				device.desc = row['description']
				device.units = row['units']
				device.valueType = row['valueType']
				device.direction = row['direction']
				device.timeout = row['timeout']
				allId = unid+''+setid
				device.isOnline = False
				SocketWrap.allUnits[allId] = device
	@staticmethod
	def getonlineUnits():
		return SocketWrap.onlineUnits
	def registerDevice(self, unid, setid = ''):
		Log.i('SocketWrap',"Registering new device "+unid)
		resInfo = DB.sqlSelect("SELECT units_def.description  FROM `units_def` WHERE unid = '%s'" % unid)
		if(setid == ''):
			res = DB.sqlSelect("SELECT units_run.setid  FROM `units_run` WHERE units_run.unid = '%s' ORDER BY `id` DESC LIMIT 1 " % unid)
		#print("SELECT `id` FROM `units_run` WHERE `unid` = '%s' ORDER BY `id` DESC LIMIT 1 " % unid)
		nextSetdId = ''
		
		if len(resInfo)== 0:
			Log.e('SocketWrap','Unknown produced device connected')
			DB.addAlert(unid, nextSetdId,1004)
			return Device(0,0, self)
		else:
			if(setid != ''):
				nextSetdId = setid
			elif len(res)> 0 :
				Log.i('SocketWrap',"Last id: %s" % res[0]['setid'])
				nextSetdId = '{:04x}'.format(int(res[0]['setid'], 16)+1)
			else:
				nextSetdId = '0001'
			nextSetdId = nextSetdId.upper()
			Log.i('SocketWrap',"Registering new device with id: "+unid+"|"+nextSetdId)
			
			sql = """
				INSERT INTO `units_run`
				(
				 `unid`,
				 `setid`,
				 `lastvalue`,
				 `lasttime`,
				 `timeAdded`,
				 `interface`,
				 `name`,
				 `alive`
				)
				VALUES
				(
				 '%s',
				 '%s',
				 '',
				 '',
				 '%s',
				 '%s',
				 '%s',
				 '1'
				); 
			""" % (unid, nextSetdId,strftime("%Y.%m.%d %H:%M:%S", localtime()), self.interface, resInfo[0]['description'])
			id = DB.sqlInsert( sql )
		
			msg = Msg(unid = unid, setid = setid, cmd="device.reg.res",value=nextSetdId[:2] + ',' + nextSetdId[2:], socket = self)
			self.outgoingMSG.append(msg)
			
			device = Device(unid, nextSetdId, self);
			device.id = id
			device.isOnline = True
			allId = unid+''+nextSetdId
			self.units[allId] = device
			SocketWrap.allUnits[allId] = device
			SocketWrap.onlineUnits[unid+''+nextSetdId] = device
			
			DB.registerEvent(unid,nextSetdId,'SocketWrap','Registered new device!' )
			return device
	def onValueRecieved(self, unid, setid, value):
		allId = unid+''+setid
		Log.i('SocketWrap',"New value at socket for device "+unid+" "+setid+" :"+value)
		if unid == '' and setid == '':
			return;
		if allId in SocketWrap.allUnits:
			device = SocketWrap.allUnits[allId]
			if len(value) > 0:
				device.onValueRecieved(value)
			
		else:
			if unid == '0000' and setid == '0000':
				self.registerDevice(value)
			else:
				self.registerDevice(unid,setid)
	def sendValue(self, device, value, callback = None):
		msg = Msg(unid = device.unid, setid = device.setid, cmd="device.val.set",value=value, socket = self, callback = callback)
		Log.d('DeviceSetVal',"[1.1.1]")
		self.outgoingMSG.append(msg)
		return msg
	def sendValueCheck(self, msg):
		self.outgoingMSG.append(msg)
		return 0
	def sendMsg(self, msg):
		Log.i('SocketWrap/sendMsg',msg.toJSON())
		self.tcpConn.send(msg.toJSON().encode())
		
	def sendAck(self, unid, setid):
		Log.i('SocketWrap/sendAck',"To %s %s" % (unid,setid) )
		self.sendMsg(Msg(unid = unid, setid = setid, cmd="ACK", socket = self) )
	#def sendHeartBeatAll(self):
	#