# -*- coding: utf-8 -*-
import croniter
from datetime import datetime
from common import Log
from DB import DB
from _thread import start_new_thread
import time
import common
import traceback
import sys
import threading
class Task:
	id = 0
	_i = 0
	type = 0
	time = ''
	script = ''
	lastTimeRun = ''
	nextTimeRun = ''
	active = True
	allTasks = {}
	uscriptsOutputPrint = {}
	def __init__(self,id, time, type, script):
		self.id = id
		self.time = time
		self.type = type
		self.updateNextTime()
		self.script = script
	def secsBetween(self, d1, d2):
		return ((d2 - d1).total_seconds())
	def ping(self, now):
		if(self.active == True):
			
			#now = datetime(2018, 1, 22, 18, 3, 30)
			if (self.type == 1):
				d1 = datetime.strptime(self.time, "%Y.%m.%d %H:%M:%S")
				#print(now, "- ", d1, "=", self.secsBetween(now, d1))
				delta = self.secsBetween(d1, now)
				if (delta > 0):
					self.execute()
					self.active = False
			elif (self.type == 2):
				d1 = datetime.strptime(self.nextTimeRun, "%Y.%m.%d %H:%M:%S")
				#cron = croniter.croniter(self.time, now)
				#d1 = cron.get_next(datetime)
				d1 = d1.replace(second=0, microsecond=0)
				delta = self.secsBetween(d1, now)
				if (delta > 0):
					self.execute()
					time.sleep(1)
			if len(self.nextTimeRun)==0:
				self.updateNextTime()
	@staticmethod
	def logUserPrint(uscript, *args):
		lineStr = ''
		for x in args:
			x 
			if(lineStr == ""):
				lineStr = str(x)
			else:
				lineStr += ","+str(x)
		if uscript not in Task.uscriptsOutputPrint:
			Task.uscriptsOutputPrint[uscript] = lineStr
		else:
			Task.uscriptsOutputPrint[uscript] += "\n"+lineStr
	@staticmethod
	def runUserScriptEnv(uscript):
		from SocketWrap import SocketWrap
		from Device import Device
		value = ''
		Task.uscriptsOutputPrint[uscript] = ""
		path = common.config['HubServer']['USCRIPTS_PATH']+uscript
		Log.i('Tasker',"Reading Users Script at: "+path)
		try:
			f = open(path, "r")
		except EnvironmentError:
			DB.addAlert('', '',1005, 'Path: '+path)
			return
		scriptCont = f.read()
		scriptCont = scriptCont.replace("print(","Task.logUserPrint('"+uscript+"',")
		scriptCont = scriptCont.replace("print (","Task.logUserPrint('"+uscript+"',")
		scriptCont = scriptCont.replace("print\t(","Task.logUserPrint('"+uscript+"',")
		f.close()
		#print(scriptCont) 
		try:
			exec(scriptCont, locals(), globals())
			res = Task.uscriptsOutputPrint[uscript]
		except Exception as e:
			exc = str(e)
			Log.e('Tasker',"Executing task failed with error " + exc)
			DB.addAlert('','',1007,uscript+":\n"+exc+"\n"+traceback.format_exc())
			res = exc
		Log.i('Tasker',"Executed: "+res)
		#del Task.uscriptsOutputPrint[uscript]
		return res
	def execute(self):
		Log.i('Tasker',"Executing task %i NOW" % self.id)
		threading.Thread(target = Task.runUserScriptEnv, args=(self.script,)).start()
		#self.runUserScriptEnv(self.script)
		DB.registerEvent('','','Tasker','Executing task #%i' % (self.id ) )
		now = datetime.now()
		self.lastTimeRun = datetime.strftime(now, "%Y.%m.%d %H:%M:%S")
		self.updateNextTime()
	def updateNextTime(self):
		now = datetime.now()
		if self.type == 2:
			cron = croniter.croniter(self.time, now)
			d1 = cron.get_next(datetime)
			if( self.lastTimeRun == d1):
				d1 = cron.get_next(datetime)
			self.nextTimeRun = datetime.strftime(d1, "%Y.%m.%d %H:%M:%S")
		if (len(self.lastTimeRun) > 0):
			DB.sqlUpdate("""
			UPDATE `schedule` SET `lastTimeRun`='%s',`nextTimeRun`='%s',`active`='%i' WHERE `id`=%i
			""" % (self.lastTimeRun, self.nextTimeRun,self.active, self.id) )
		else:
			DB.sqlUpdate("""
			UPDATE `schedule` SET `nextTimeRun`='%s',`active`='%i' WHERE `id`=%i
			""" % (self.nextTimeRun, self.active, self.id) )
	@staticmethod
	def getAllTasks():
		Task.allTasks.clear()
		#print("Updating tasks list")
		res = DB.sqlSelect("""
		SELECT * FROM `schedule` WHERE `active` = 1 AND `type` = 2
		UNION ALL
		SELECT * FROM `schedule` WHERE `active` = 1 AND `type` = 1 AND `time` >= NOW()
		""")
		for row in res:
			Task.allTasks[row['id']] = Task(row['id'],row['time'],row['type'],row['script_name']) 
			Task.allTasks[row['id']].lastTimeRun = row['lastTimeRun']
			#print "Task: %i, %s, " % ( row['id'],row['time'] )
		#print("Tasks list updated. Total: %i" % len(Task.allTasks) )
		#return SocketWrap.onlineUnits	
		#config = ConfigParser()
		#config.read('config.ini')
	@staticmethod
	def pingAllTasks():
		now = datetime.now()
		for key, value in Task.allTasks.copy().items():
			value.ping(now)
	
	@staticmethod
	def run():
		taskCheckTimout = int(common.config['HubServer']['TASK_CHECK_TIMOUT_MIN'])
		while True:
			time.sleep(1)
			Task._i += 1
			Task.pingAllTasks()
			if Task._i >=  taskCheckTimout* 60:
				Task.getAllTasks()
				Task._i = 0
	@staticmethod
	def start():
		Task.getAllTasks()
		start_new_thread(Task.run, () )