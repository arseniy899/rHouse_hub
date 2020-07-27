import json
import socket
from Log import Log
class Msg:
	device = None
	id 		= 0
	setid	= ''
	unid 	= ''
	value = ""
	cmd = ""
	timer	= 0
	callback = None
	socket = None
	sendAttempt = 0
	def __init__(self, cmd, setid = '', unid= '',unSetId = '', socket = None, device = None, value = "", id = 0, callback = None):
		self.device = device
		self.value = value
		self.id = id
		self.cmd = cmd
		if(unSetId != ''):
			spl = unSetId.split(",")
			self.unid = spl[0]
			self.setid = spl[1]
		else:
			self.setid = setid
			self.unid = unid
		self.callback = callback
	def toJSON(self):
		return json.dumps({'setid': self.setid,'unid': self.unid,'cmd': self.cmd,'value': self.value,'sendAttempt': self.sendAttempt})+"\n"
		#return json.dumps(self, default=lambda o: o.__dict__, 
		#	sort_keys=True, indent=4)
	@staticmethod
	def fromJSONstr(socket,jsonStr):
		try:
			jsonObj = json.loads(jsonStr)
			
			
			msg = Msg(cmd = jsonObj["cmd"],unid = jsonObj["unid"],setid = jsonObj["setid"],value = jsonObj["value"])

			if("id" in jsonObj):
				msg.id = jsonObj["id"]
			msg.socket = socket
			return msg
		except json.decoder.JSONDecodeError:
			Log.e("MSG/JSON","Invalid JSON: "+jsonStr)
			return Msg(cmd = -1)