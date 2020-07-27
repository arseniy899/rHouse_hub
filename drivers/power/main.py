'''
Power supply values set:
	0  - all UP	
	1  - no any energy
	//2  - no Mains only (external)
	//-1 - kinda error (no power supply but Mains exist)
'''

## prepare to import base modules
import sys
import os
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.append('../import')

from Config import Config
from DriverTCP import DriverTCP
from Log import Log
from Msg import Msg
import os.path
import time
from datetime import datetime
import subprocess
import pigpio

Config.start( {
	"TIME-DELAY-S":"3",
	"PS-PIN":"3"
})

rebootReasonPwrFile = os.getcwd()+"/pwr-off.txt"
def onRecieve(msg):
	global DriverTCP
	if(msg.cmd == "device.heartbeat" and Config.get('id') != ""):
		DriverTCP.sendMsgWithCheck(Msg(unSetId = Config.get('id'),cmd="device.reg.renew") )
	elif(msg.cmd == "device.reg.res"):
		Log.i("Receive/RegFin","Got SetID", msg.value)
		Config.set('id',"00C8,"+msg.value.replace(",","") )
	
DriverTCP = DriverTCP(5, onRecieve)
if(Config.get('id') == ""):
	Log.w("Start","No ID found for device. Registering new...")
	DriverTCP.registerDevice("00C8")
#def sendPowerSupplyValue(value):
#	global DriverTCP
#	DriverTCP.sendMsgWithCheck(Msg(unSetId = DriverTCP.config['PWR-DRIVER']['ID-PS'], value=value,cmd="device.val.input") )

def sendPowerSupplyValue(value):
	global DriverTCP
	DriverTCP.sendMsgWithCheck(Msg(unSetId = Config.get('id'), value=str(value),cmd="device.val.input") )

#def sendExternalPowerValue(value):
#	global DriverTCP
#	DriverTCP.sendMsgWithCheck(Msg(unSetId = DriverTCP.config['PWR-DRIVER']['ID-EP'], value=value,cmd="device.val.input") )

#subprocess.call(["sudo","pigpiod"]);
pi = pigpio.pi()
PS_PIN = int(Config.get('PS-PIN'))
#EP_PIN = int(DriverTCP.config['PWR-DRIVER']['EP-PIN'])

pi.set_mode(PS_PIN, pigpio.INPUT)
#pi.set_mode(EP_PIN, pigpio.INPUT)
TIME_DELAY_S = Config.get('TIME-DELAY-S')
powerSupply = True
extrenalPower = True
isMainsOnBef = True
isNotWorkingBattery = True
i = 0
isEpEx = True
isPsEx = True
Log.i ("Init","isNotWorkingBattery=", isNotWorkingBattery)

def readVl():
	global powerSupply
	global extrenalPower
	global isNotWorkingBattery
	powerSupply 	= pi.read(PS_PIN) == 0
	#extrenalPower 	= pi.read(EP_PIN) == 1
	#print ("powerSupply=",powerSupply)
	#print ("isNotWorkingBattery=", isNotWorkingBattery)

readVl()
if(os.path.isfile(rebootReasonPwrFile)):
	isNotWorkingBattery = False
	Log.i ("Init","Before were working on battery!");
	if(powerSupply == True):
		os.remove(rebootReasonPwrFile) 

#DriverTCP.sendMsgWithCheck(  Msg(unSetId = DriverTCP.config['WANSCAM-DRIVER']['ID'], cmd="device.reg.renew")  )
time.sleep(5)
try:
	while True:
		readVl()
		#print ("isNotWorkingBattery != powerSupply = ", isNotWorkingBattery != powerSupply)
		#print ("isMainsOnBef != extrenalPower = ", isMainsOnBef != extrenalPower)
		if (isMainsOnBef != extrenalPower or isNotWorkingBattery != powerSupply):
			Log.i ("Loop","No power: Waiting to be sure");
			time.sleep(int(TIME_DELAY_S))
			readVl()
			if (powerSupply == False):
				value = 0
			else:
				value = 1
				if(os.path.isfile(rebootReasonPwrFile)):
					os.remove(rebootReasonPwrFile) 
			'''if (extrenalPower   == True and powerSupply == False):
				value = -1
			elif (extrenalPower == True and powerSupply == True):
				value = 0
			elif (extrenalPower == False and powerSupply == False):
				value = 1
			elif (extrenalPower == False and powerSupply == True):
				value = 2'''
			print ("Value %i" % value);
			isMainsOnBef = extrenalPower
			isNotWorkingBattery = powerSupply
			if(powerSupply == False):
				f = open(rebootReasonPwrFile, "w")
				f.write('1')
				f.close()
			sendPowerSupplyValue(value)
		
		time.sleep(5)

except KeyboardInterrupt:
	#Catch keyboard interrupt
	
	print('\n\rKeyboard interrtupt') 