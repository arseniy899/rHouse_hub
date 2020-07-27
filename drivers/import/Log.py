import sys
import os
from datetime import datetime
class Log:
	#date time PID-TID/package priority/tag: message
	#12-10 13:02:50.071 1901-4229/com.google.android.gms V/AuthZen: Handling delegate intent.
	file = None
	@staticmethod
	def start():
		driver = sys.argv[0].replace(".py",'')
		#Log.file = open("log_"+driver+".txt", "w")
		Log.file = open("log.txt", "w")
		Log.format = '%s %s/%s: %s'
		Log.timeFormat = "%Y.%m.%d %H:%M:%S.%f"
		#logging.basicConfig(filename='log.txt'filemode='w', format='%(asctime)s %(levelname)s/%(message)s', level=common.config['HubServer']['LOG_LEVEL'], datefmt='%m-%d %H:%M:%S')
	@staticmethod
	def i(TAG, *args):
		if (Log.file == None):
			Log.start()
		lineStr = ''
		for x in args:
			if(lineStr == ""):
				lineStr = str(x)
			else:
				lineStr += ","+str(x)
		lineStr = Log.format %(datetime.now().strftime(Log.timeFormat)[:-3],'I', TAG,lineStr)
		print (lineStr)
		Log.file.write(lineStr+'\n')
		Log.file.flush()
	@staticmethod
	def d(TAG, *args):
		if (Log.file == None):
			Log.start()
		lineStr = ''
		for x in args:
			if(lineStr == ""):
				lineStr = str(x)
			else:
				lineStr += ","+str(x)
		lineStr = Log.format %(datetime.now().strftime(Log.timeFormat)[:-3],'D', TAG,lineStr)
		print (lineStr)
		Log.file.write(lineStr+'\n')
		Log.file.flush()
	@staticmethod
	def w(TAG, *args):
		if (Log.file == None):
			Log.start()
		lineStr = ''
		for x in args:
			if(lineStr == ""):
				lineStr = str(x)
			else:
				lineStr += ","+str(x)
		lineStr = Log.format %(datetime.now().strftime(Log.timeFormat)[:-3],'W', TAG,lineStr)
		print (lineStr)
		Log.file.write(lineStr+'\n')
		Log.file.flush()
	@staticmethod
	def e(TAG, *args):
		if (Log.file == None):
			Log.start()
		lineStr = ''
		for x in args:
			if(lineStr == ""):
				lineStr = str(x)
			else:
				lineStr += ","+str(x)
		lineStr = Log.format %(datetime.now().strftime(Log.timeFormat)[:-3],'E', TAG,lineStr)
		print (lineStr)
		Log.file.write(lineStr+'\n')
		Log.file.flush()
