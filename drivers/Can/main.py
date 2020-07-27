## prepare to import base modules
import sys
import os
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.append('../import')
import can
import time
import re
import pigpio
import binascii
from Config import Config
from DriverTCP import DriverTCP
from Msg import Msg
from Log import Log
Config.start( {
	"PWR_PIN":3
})

Log.i('Start','Bring up CAN0....')
os.system("sudo /sbin/ip link set can0 down")
#os.system("sudo ifconfig can0 txqueuelen 50000")
os.system("sudo ifconfig can0 ")
os.system("sudo ip link set can0 up type can bitrate 125000 loopback off ") # restart-ms 500
time.sleep(0.1)	
pi = pigpio.pi()


try:
	bus = can.interface.Bus(channel='can0', interface='socketcan_native', receive_own_messages=False)
	#bus.state = BusState.ACTIVE
except OSError:
	Log.e('Start','Cannot find CAN board.')
	exit()

def CAN_restart():
	os.system("sudo ip link set can0 down")
	os.system("sudo ip link set can0 up type can bitrate 125000 loopback off ") # restart-ms 500
Log.i('Start','CAN Ready')
def ACK_clb(msg):
	if (msg.unid+msg.setid) == "":
		id = 1
	elif msg.setid == "":
		msg.setid = "0000"
		id = int(msg.unid+msg.setid, 16)
	else:
		id = int(msg.unid+msg.setid, 16)
	CAN_send(id, 0,[])
def CAN_send(id,cmd, payload):
	Log.i('Send','id=%.8x,cmd=%i,payload=%s'%(id,cmd,list(payload)));
	
	if(len(payload)>6):
		frameCount = int(len(payload)/5)
	else:
		frameCount = 1
	head = cmd*16+frameCount
	
	if(frameCount == 1):
		data = []
		data.append(head)
		data+= payload
		try:
			msg = can.Message(arbitration_id=id,data=data,extended_id=True)
			bus.send(msg, timeout=0.5)
			time.sleep(0.3)
		except:
			CAN_restart()
	else:
		for i in range(frameCount):
			data = []
			data.append(head)
			data.append(i)
			data+= payload[i*5:i*5+5]
			try:
				msg = can.Message(arbitration_id=id,data=data,extended_id=True)
				bus.send(msg, timeout=0.5)
				time.sleep(0.3)
			except:
				CAN_restart()
def cmdIntToStr(cmd):
	if(type(cmd) == int):
		cmd = str(cmd)
	if(cmd == "0"):
		return "ACK"
	elif(cmd == "1"):
		return "device.heartbeat"
	elif(cmd == "2"):
		return "device.reg.renew"
	elif(cmd == "3"):
		return "device.val.set"
	elif(cmd == "4"):
		return "device.val.input"
	elif(cmd == "5"):
		return "device.reg.new"
	elif(cmd == "6"):
		return "device.reg.res"
	
def cmdStrToInt(cmd):
	if(cmd == "ACK"):
		return 0
	elif(cmd == "device.heartbeat"):
		return 1
	elif(cmd == "device.reg.renew"):
		return 2
	elif(cmd == "device.val.set"):
		return 3
	elif(cmd == "device.val.input"):
		return 4
	elif(cmd == "device.reg.new"):
		return 5
	elif(cmd == "device.reg.res"):
		return 6

messagesWaitingComplete = {}
def CAN_onRecieve(msg):
	global pi
	bytes = msg.data
	data = []
	for byte in bytes:
		data.append(int(byte))
	remote = msg.is_remote_frame
	id = msg.arbitration_id
	fd = msg.is_fd
	err = msg.is_error_frame
	strId = ('%.8x'%(id)).lower()
	print("1")
	if err == False and len(data)>0 and len(strId) == 8:
		unid = strId[:4]
		setid = strId[4:]
		powerSupply 	= pi.read(PS_PIN) == 0
		if (len(unid) == 4 and unid != "0000" and unid != "" and powerSupply == True):
			Log.i('Recv',("Received: From %s with data: %s" % (strId, ';'.join( map(str,data) ) ) ) )
			cmd = int(data[0]/16)
			Log.i('Recv',"CMD: %i"%cmd)
			frameCount = data[0]%16
			if(frameCount > 1):
				curFrame = data[1]
				if(curFrame > 0 and id in messagesWaitingComplete):
					messagesWaitingComplete[id].value += ';'.join(map(str,data[2:])  )
				elif(curFrame == 0):
					if(setid=="0000"):
						setid = ""
					messagesWaitingComplete[id] = Msg(unid = unid, setid = setid, cmd=cmdIntToStr(cmd), value = ','.join( map(str,data[2:])) , callback = ACK_clb )
				elif(curFrame == (frameCount-1) and id in messagesWaitingComplete):
					DriverTCP.sendMsg(messagesWaitingComplete[id])
					del messagesWaitingComplete[id]
				else:
					Log.e('Recv',"ERROR: Lost first frames or message incomplete")
			else:
				if(setid=="0000"):
					setid = ""
					
				msg = Msg(unid = unid, setid = setid, cmd=cmdIntToStr(cmd), value = ';'.join( map(str,data[1:]) ), callback = ACK_clb)
				Log.d("Recv/TCPSend","MSG:",msg.toJSON())
				DriverTCP.sendMsg(msg)
		elif(powerSupply == False):
			Log.w('Recv',"Skipping garbage")
		else:
			Log.w('Recv',"id:",id,"data:",data)
	else:
		Log.w('Recv',"Er:",err,"id:",id,"data:",data)
# Hub TCP receive
def onRecieve(msg):
	payload = []
	for n in msg.value.split(";"):
		if (n != ""):
			n = re.sub('[^-0-9]','', str(n)) 
			if(isinstance(n, int) or msg.cmd != "device.reg.res"):
				payload.append(int(n))
			else:
				payload.append(int(n, 16))
	if (msg.unid+msg.setid) == "":
		id = 1
	elif msg.setid == "":
		msg.setid = "0000"
		id = int(msg.unid+msg.setid, 16)
	else:
		id = int(msg.unid+msg.setid, 16)
	#print("Sending CAN msg to '%.8x' : " % id )
	
	#print (payload)
	
	CAN_send(id, cmdStrToInt(msg.cmd),payload)

DriverTCP = DriverTCP(2, onRecieve)

PS_PIN = int(Config.get('PWR_PIN'))
pi.set_mode(PS_PIN, pigpio.INPUT)
try:
	notifier = can.Notifier(bus, [CAN_onRecieve]) 
	#CAN_send(1, 1,[])
	while True:
		time.sleep(18)
		CAN_send(1, 1,[])

except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")	
print('\n\rKeyboard interrtupt') 