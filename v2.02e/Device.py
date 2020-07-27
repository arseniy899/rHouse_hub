# -*- coding: utf-8 -*-
from time import localtime, strftime
import common
from common import Log
from DB import DB
import threading
##TEST
import sys, traceback
class Device:
	id	 		= ''
	setid	 	= ''
	unid 		= ''
	lastValue 	= ''
	lastTime 	= ''
	name 		= ''
	alive		= 0
	desc		= ''
	units		= ''
	valueType	= ''
	direction	= ''
	timeout		= ''
	isOnline 	= False
	needSetValue	= False
	values		= {}
	mySocketWrap 	= None
	setValueCallback = None
	uscriptsOutputPrint = {}
	def __init__(self,unid, setid, mySocketWrap, loadDb = True):
		self.setid = setid;
		self.unid = unid
		self.mySocketWrap = mySocketWrap
		if loadDb:
			self.getInfoFRDB()
		
	#def setValue(self, newValue):
		
		 
	#def registerNew(self, unid):
	
	def getInfoFRDB(self):
		if self.unid != '' and self.setid != '':
			Log.i('Device',"Obtaining data device from DB with id %s %s" %(self.unid, self.setid) )
			sql = """
		SELECT 	units_run.lastValue,
				units_run.id,
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
		WHERE  units_run.setid = '%s' AND units_run.unid = '%s'
			"""% (self.setid, self.unid )
			
			data = DB.sqlSelect(sql)
			#print(sql)
			if len(data) == 0:
				Log.e('Device',"device with ID %s|%s not FOUND!!" % (self.unid, self.setid))
				##TODO: register as new one
				DB.addAlert(self.unid, self.setid,1003)
			else:
				data = data[0]
				self.id = data['id']
				self.lastTime = data['lastTime']
				self.lastValue = data['lastValue']
				self.needSetValue = int(data['needSetValue']) == 1
				self.name = data['name']
				self.desc = data['description']
				self.units = data['units']
				self.valueType = data['valueType']
				self.direction = data['direction']
				self.timeout = data['timeout']
				#print(self)
	
	def parseValueToFormatSing(self, format, value):
		if format=='sint':
			Log.d("Device/ValToForm","value",value, (int(value) - 128))
			return str(int(value) - 128)
		else:
			return value
	def parseFormatToValueSing(self, format, value):
		if format=='sint':
			Log.d("Device/FormToVal","value",value, (int(value) + 128))
			return str (int(value) + 128)
		else:
			return value
	def setIsOnline(self, isOnline):
		self.isOnline = isOnline
		DB.sqlUpdate("""
		UPDATE `units_run`
			SET    `alive` = '%i'
			WHERE  `setid` = '%s'
				   AND `unid` = '%s'
		""" % ((1 if self.isOnline == True else 0) , self.setid, self.unid ) )
	def parseValueToFormat(self, value):
		if ";" in value:
			values = value.split(";")
			formats = self.valueType.split(";")
			if len(values) > len(formats):
				#Log.e('Device',"ERROR: New value cannot be parsed bcs incorrect format")
				#DB.addAlert(unid, nextSetdId,1002)
				for i in range(0, len(formats)):
					values[i] = self.parseValueToFormatSing(formats[i],values[i])
				return ";".join(values)
			else:
				for i in range(0, len(values)):
					values[i] = self.parseValueToFormatSing(formats[i],values[i])
					#if formats[i]=='sint':
						#values[i] = int(values[i]) - 128
				return ";".join(values)
		else:
			return self.parseValueToFormatSing(self.valueType,value)
	def parseFormatToValue(self, value):
		if ";" in value:
			values = value.split(";")
			formats = self.valueType.split(";")
			if len(values) > len(formats):
				#Log.e('Device',"ERROR: New value cannot be parsed bcs incorrect format")
				#DB.addAlert(unid, nextSetdId,1002)
				for i in range(0, len(formats)):
					values[i] = self.parseValueToFormatSing(formats[i],values[i])
				return ";".join(values)
			else:
				for i in range(0, len(values)):
					values[i] = self.parseFormatToValueSing(formats[i],values[i])
					#if formats[i]=='sint':
						#values[i] = int(values[i]) - 128
				return ";".join(values)
		else:
			return self.parseFormatToValueSing(self.valueType,value)
	def executeTriggerSeq(self, ignoreDir):
		sql = """
			SELECT * FROM `triggers` WHERE `unid` = '%s' AND (`setid` = '%s' OR `setid` = '0000' OR `setid` = '') AND `direct` != '%i'
		""" % ( self.unid, self.setid, ignoreDir)
		data = DB.sqlSelect(sql)
		
		value = self.lastValue
		for row in data:
			run = False
			if (row['type'] == 'any'):
				run = True
			elif (row['type'] == 'contains' or row['type'] == 'cont'):
				if (row['value'] in value):
					run = True
			else:
				cmd = """
if \"\"\"%s\"\"\" %s "%s":
	run = True""" % (self.lastValue, row['type'], row['value']) 
				l = locals()
				exec(cmd, l)
				print(cmd, run)
				run = l['run']
			if run:
				DB.registerEvent(self.unid, self.setid,'Device','Executing SET trigger for device')
				threading.Thread(target = self.runUserScriptEnv, args=(row['scriptName'],)).start()
	def callbackSetValue(self, msg):
		from Msg import Msg
		from Device import Device
		if (self.setValueCallback != None):
			try:
				self.setValueCallback(msg, self)
			except:
				pass
		#if(self.isOnline == False):
		#	self.setValue(msg.value)
		#elif(msg.sendAttempt >= 0):
		if(msg.cmd == "device.val.set"  or msg.cmd == "22"):
			self.lastValue = msg.value
		self.updateValueDb(self.lastValue)
		self.executeTriggerSeq(1)
	def setValue(self, value, callback = None):
		from Msg import Msg
		Log.i('Device',"Set value for device"+self.unid+"|"+self.setid+" :"+value+", isOnline:%s"%self.isOnline)
		if self.mySocketWrap != None and self.isOnline == True:
			Log.i('Device',"Sending expl now")
			self.setValueCallback = callback
			Log.d('DeviceSetVal',"[1.1]")
			msg = self.mySocketWrap.sendValue(self, value, self.callbackSetValue)
			Log.d('DeviceSetVal',"[1.2]")
			self.needSetValue = False
		elif ( self.mySocketWrap == None and self.isOnline == True):
			DB.addAlert(self.unid, self.setid,1008)
			if(callback != None):
				msg = Msg(cmd = "device.val.set.error")
				msg.sendAttempt = -1
				callback(msg, self)
		else:
			Log.i('Device',"Scheduled for when online")
			msg = Msg(cmd = "device.val.set.scheduled")
			self.executeTriggerSeq(1)
			if(callback != None):
				callback(msg, self)
			self.needSetValue = True
			self.updateValueDb(value)
			if(self.isOnline == False):
				self.sendHeartBeat()
			#else:
			#	self.setIsOnline(False)
		self.lastValue = value
			
	@staticmethod
	def findDeviceById(unid, setid):
		from SocketWrap import SocketWrap
		setid = setid.upper()
		unid = unid.upper()
		if setid == '0000' or setid == '':
			return Device.findDeviceByUnId(unid)
		else:
			allId = unid+''+setid
			if(allId in SocketWrap.allUnits):
				return SocketWrap.allUnits[allId]
			else:
				return None
	@staticmethod
	def findDeviceByUnId(unid):
		from SocketWrap import SocketWrap
		ret = {}
		unid = unid.upper()
		for key, value in SocketWrap.allUnits.items():
			if value.unid == unid:
				ret[key] = value
		return ret
	@staticmethod
	def logUserPrint(uscript, *args):
		lineStr = ''
		for x in args:
			x 
			if(lineStr == ""):
				lineStr = str(x)
			else:
				lineStr += ","+str(x)
		if uscript not in Device.uscriptsOutputPrint:
			Device.uscriptsOutputPrint[uscript] = lineStr
		else:
			Device.uscriptsOutputPrint[uscript] += "\n"+lineStr
	def runUserScriptEnv(self, uscript):
		from SocketWrap import SocketWrap
		device = self
		value = str(self.lastValue)
		Device.uscriptsOutputPrint[uscript] = ""
		path = common.config['HubServer']['USCRIPTS_PATH']+uscript
		Log.i('Device/RunUScript',"Reading Users Script at: "+path)
		try:
			f = open(path, "r")
		except EnvironmentError:
			DB.addAlert('', '',1005, 'Path: '+path)
			return
		scriptCont = f.read()
		scriptCont = scriptCont.replace("print(","Device.logUserPrint('"+uscript+"',")
		scriptCont = scriptCont.replace("print (","Device.logUserPrint('"+uscript+"',")
		scriptCont = scriptCont.replace("print\t(","Device.logUserPrint('"+uscript+"',")
		f.close()
		#print(scriptCont) 
		try:
			exec(scriptCont, locals(), globals())
			res = Device.uscriptsOutputPrint[uscript]
		except Exception as e:
			exc = str(e)
			Log.e('Device/RunUScript',"Executing scripts failed with error " + exc)
			DB.addAlert('','',1007,uscript+":\n"+exc+"\n"+traceback.format_exc())
			res = exc
		Log.i('Device/RunUScript',"Executed: "+res)
		#del Task.uscriptsOutputPrint[uscript]
		return res	
	
	def updateValueDb(self,value):
		#traceback.print_stack()
		self.lastTime = strftime("%Y.%m.%d %H:%M:%S", localtime())
		sql = """
		UPDATE `units_run`
			SET    `lastvalue` = '%s',
				   `lasttime` = '%s',
				   `needSetValue` = '%i',
				   `alive` = '%i'
			WHERE  `setid` = '%s'
				   AND `unid` = '%s'
		""" % (value,self.lastTime, (0 if self.isOnline == True else 1) , (1 if self.isOnline == True else 0) , self.setid, self.unid ) 
		#print(sql)
		DB.sqlUpdate(sql)
		sql = """
			INSERT INTO `units_values` (`unrId`, `value`, `timeStamp`) VALUES ('%s', '%s', '%s')
		""" % (self.id, value,self.lastTime )
		DB.sqlUpdate(sql )
	def heartbeatRes(self, msg):
		Log.i('Device',"Received heartbeat.res for device",self.unid,self.setid,"sendAttempt:",msg.sendAttempt)
		if(msg.sendAttempt<0 and self.isOnline == True):
			self.setIsOnline(False)
		elif (self.isOnline == False):
		#else:
			self.setIsOnline(True)
	def sendHeartBeat(self):
		from Msg import Msg
		if(self.mySocketWrap != None):
			try:
				self.mySocketWrap.sendMsg(Msg(unid = self.unid, setid = self.setid, cmd="device.heartbeat", socket = self.mySocketWrap, callback=self.heartbeatRes) )
			except Exception as e:
				exc = str(e)
				if("Broken pipe" in exc):
					self.setIsOnline(False)
		else:
			self.setIsOnline(False)
	def onValueRecieved(self, value):
		
		self.lastValue = value.replace('\n', '').replace(';', '\;')
		self.lastTime = strftime("%Y.%m.%d %H:%M:%S", localtime())
		self.lastValue = self.parseValueToFormat(value)
		self.updateValueDb(self.lastValue)
		if(self.isOnline == False):
			self.setIsOnline(True)
		#if 'O' in self.direction and hasattr(self, 'tcpConn'):
			#self.tcpConn.send(self.unid+''+self.setid+''+self.parseFormatToValue(self.lastValue)+'\r\n') 
		Log.i('Device',"New value for device "+self.unid+" "+self.setid+" :"+self.lastValue+" at "+ self.lastTime)
		#print("Processing triggers")
		
		self.executeTriggerSeq(2)