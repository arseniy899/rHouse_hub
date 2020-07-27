from datetime import datetime
import common, threading
class Log:
	#date time PID-TID/package priority/tag: message
	#12-10 13:02:50.071 1901-4229/com.google.android.gms V/AuthZen: Handling delegate intent.
	@staticmethod
	def start():
		Log.file = open("log.txt", "w")
		Log.format = '%s [%i]%s/%s: %s'
		Log.timeFormat = "%Y.%m.%d %H:%M:%S.%f"
		#logging.basicConfig(filename='log.txt'filemode='w', format='%(asctime)s %(levelname)s/%(message)s', level=common.config['HubServer']['LOG_LEVEL'], datefmt='%m-%d %H:%M:%S')
	@staticmethod
	def i(TAG, *args):
		lineStr = ''
		logLevel = common.config['HubServer']['LOG_LEVEL'].upper()
		if('DEBUG' in logLevel or 'D' in logLevel or 'INFO' in logLevel or 'I' in logLevel):
			for x in args:
				x 
				if(lineStr == ""):
					lineStr = str(x)
				else:
					lineStr += ","+str(x)
			lineStr = Log.format %(datetime.now().strftime(Log.timeFormat)[:-3],threading.get_ident(),'I', TAG,lineStr)
			print (lineStr)
			Log.file.write(lineStr+'\n')
			Log.file.flush()
	@staticmethod
	def d(TAG, *args):
		lineStr = ''
		logLevel = common.config['HubServer']['LOG_LEVEL'].upper()
		if('DEBUG' in logLevel or 'D' in logLevel):
			for x in args:
				x 
				if(lineStr == ""):
					lineStr = str(x)
				else:
					lineStr += ","+str(x)
			lineStr = Log.format %(datetime.now().strftime(Log.timeFormat)[:-3],threading.get_ident(),'D', TAG,lineStr)
			print (lineStr)
			Log.file.write(lineStr+'\n')
			Log.file.flush()
	@staticmethod
	def w(TAG, *args):
		lineStr = ''
		logLevel = common.config['HubServer']['LOG_LEVEL'].upper()
		if('DEBUG' in logLevel or 'D' in logLevel or 'INFO' in logLevel or 'I' in logLevel or 'W' in logLevel or 'WARN' in logLevel):
			for x in args:
				x 
				if(lineStr == ""):
					lineStr = str(x)
				else:
					lineStr += ","+str(x)
			lineStr = Log.format %(datetime.now().strftime(Log.timeFormat)[:-3],threading.get_ident(),'W', TAG,lineStr)
			print (lineStr)
			Log.file.write(lineStr+'\n')
			Log.file.flush()
	@staticmethod
	def e(TAG, *args):
		lineStr = ''
		for x in args:
			x 
			if(lineStr == ""):
				lineStr = str(x)
			else:
				lineStr += ","+str(x)
		lineStr = Log.format %(datetime.now().strftime(Log.timeFormat)[:-3],threading.get_ident(),'E', TAG,lineStr)
		print (lineStr)
		Log.file.write(lineStr+'\n')
		Log.file.flush()