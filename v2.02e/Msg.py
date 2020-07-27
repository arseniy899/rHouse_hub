import common
import json
from Device import Device
from common import Log
class Msg:
	device = None
	id 		= 0
	timer 	= 0
	setid	= ''
	unid 	= ''
	value = ""
	cmd = ""
	callback = None
	socket = None
	sendAttempt = 0
	def __init__(self, cmd, setid = '', unid= '', unSetId = '', socket = None, device = None, value = "", id = 0, callback = None):
		self.device = device
		self.value = value
		self.id = id
		self.cmd = cmd
		if(unSetId != ''):
			spl = unSetId.split(',')
			self.unid = spl[0].upper()
			self.setid = spl[1].upper()
		else:
			self.setid = setid.upper()
			self.unid = unid.upper()
		self.callback = callback
	def toJSON(self):
		return json.dumps({'setid': self.setid,'unid': self.unid,'cmd': self.cmd,'value': self.value,'sendAttempt': self.sendAttempt})+"\n"
		#return json.dumps(self, default=lambda o: o.__dict__, 
		#	sort_keys=True, indent=4)
	@staticmethod
	def fromJSONstr(socket,jsonStr):
		try:
			jsonObj = json.loads(jsonStr)
			
			'''if(jsonObj["unid"] != "" and jsonObj["setid"] != ""):
				device = Device.findDeviceById(jsonObj["unid"],jsonObj["setid"])
			else:
				device = None'''
			msg = Msg(cmd = jsonObj["cmd"],unid = jsonObj["unid"],setid = jsonObj["setid"],value = jsonObj["value"])

			if("id" in jsonObj):
				msg.id = jsonObj["id"]
			msg.socket = socket
			return msg
		except json.decoder.JSONDecodeError:
			Log.e("MSG/JSON","Invalid JSON: "+jsonStr)
			return Msg(cmd = -1)
			
	def __eq__(self, other): 
		if not isinstance(other, Msg):
			# don't attempt to compare against unrelated types
			return NotImplemented
		return self.setid == other.setid and self.unid == other.unid and self.value == other.value and self.cmd == other.cmd