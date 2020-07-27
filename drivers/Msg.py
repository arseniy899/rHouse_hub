import json
class Msg1:
	device = None
	id 		= 0
	setid	= ''
	unid 	= ''
	value = ""
	cmd = ""
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
		jsonObj = json.loads(jsonStr)
		device = None
		msg = Msg(cmd = jsonObj["cmd"],unid = jsonObj["unid"],setid = jsonObj["setid"],value = jsonObj["value"])

		if("id" in jsonObj):
			msg.id = jsonObj["id"]
		msg.socket = socket
		return msg