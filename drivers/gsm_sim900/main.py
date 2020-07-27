# -*- coding: utf-8 -*-
## prepare to import base modules
import sys
import os
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.append('../import')
from Config import Config
from DriverTCP import DriverTCP
from Msg import Msg
from Log import Log

'''

GSM modem driver:
input cmds:
	sms,<NUMBER>,<TEXT>
		<NUMBER> exact numb, all - mass send to all in ALRM_NUMBS, last
	power,<STATE>
		<STATE> - 'on' or 'off'	
output:
	sms,<NUMBER>,<TEXT>
'''
import time
from datetime import datetime
import subprocess


Config.start( {
	"RX_PIN":17,
	"TX_PIN":18,
	"BAUDRATE":19200,
	"ALRM_NUMBS":"",
	"MODEM_PWR_PIN":21
})
from Serial import Serial
import threading
import re
REAL_TEST = True
if REAL_TEST:
	import pigpio
	
isWorkingWithModem = True
isModemRequired = True
isACKwaiting = False


if REAL_TEST:
	#subprocess.call(["sudo","pigpiod"])
	pi = pigpio.pi()
#if not pi.connected:
#	exit() 
baudrate = int(Config.get('BAUDRATE'))

txPin = int(Config.get('TX_PIN'))
rxPin = int(Config.get('RX_PIN'))


modems = Serial(baudrate, txPin, rxPin)


ph_numb = Config.get('ALRM_NUMBS').split(",")   #список телефонов для оповещения
fullInfo = ''			  #
lastUsedPhNumb = ''	# телефон с которого пришёл запрос


modem_alive = False	   #флаг признака модема в рабочем состоянии

error_try = 0
modem_try = 0

MODEM_PWR_PIN = int(Config.get('MODEM_PWR_PIN'))
if REAL_TEST:
	pi.set_mode(MODEM_PWR_PIN, pigpio.OUTPUT)

def HUB_send(text):
	global modemUnid
	global modemSetid
	global DriverTCP
	if(modemSetid != ""):
		DriverTCP.sendMsgWithCheck(Msg(unid = modemUnid, setid = modemSetid, value=text, cmd="device.val.input") )

def HUB_sendACK():
	global modemUnid
	global modemSetid
	global isACKwaiting
	global DriverTCP
	if(isACKwaiting and modemSetid != ""):
		DriverTCP.sendMsg(Msg(unid = modemUnid, setid = modemSetid, cmd="ACK") )
		isACKwaiting = False

def send_at(at_i, delay = 1):
	if len(at_i)==0:
		return
	modems.send(at_i + "\r\n")
	ret = read_serial()#modemPowerOn()
	time.sleep(delay)
	return ret
def modemPowerOff():
	if isModemRequired == False:
		modems.send("AT+CPOWD=1\r\n")
		HUB_sendACK()
	else:
		print('Cannot turn off modem. It\' required ')
def checkModemAlive():
	if isModemRequired and isSendingSMS == False:
		global modem_try
		global timesOfTime
		#threading.Timer(5.0, checkModemAlive).start()
		#modems.send("%AT+CCLK?\r\n")
		modems.send("AT\r\n")
		if 'OK' not in read_serial() and modem_try<5:
			restart()
		else:
			modem_try = 0

		timesOfTime += 1
		if timesOfTime > 35:
			timesOfTime = 0
			send_at("AT+CSQ")

def restart():

	send_at("AT")
	modems.send("AT\r\n")
	if 'OK' not in read_serial():
		modemPowerOn ()

def parseGSMstring(cmd, vals, text):
	Log.d("ParseGSM","cmd=",cmd,"vals=",vals,"text=",text)
	if 'CMT' in cmd:
		global lastUsedPhNumb
		# Received SMS
		number = vals[0]
		curNumb = number
		lastUsedPhNumb = curNumb
		Log.i("GSMParse",'---------- SMS got from %s with txt: \n %s \n --------------' %( number, text) )
		if(number in ph_numb):
			HUB_send("sms,"+number+","+text)
		else:
			print('Unknown phone')
	elif 'CSQ' in cmd:
		csq = int(vals[0])*100 / 32
		print('Signal strength: %i ' % csq )
	elif 'CREG' in cmd:
		fParam = ['нет кода регистрации сети','есть код регистрации сети','есть код регистрации сети + доп параметры']
		sParam = ['не зарегистрирован, поиска сети нет','зарегистрирован, домашняя сеть','не зарегистрирован, идёт поиск новой сети','регистрация отклонена','неизвестно','роуминг']
		#Log.i("GSMParse",'Register info: %s, %s' %(fParam[int(vals[0])],sParam[int(vals[1])]))
		Log.i("GSMParse",'Register info: %s' %(fParam[int(vals[0])]))
	
def read_serial(serial_id = 0, delay = 0):
	'''
		+CIEV: "MESSAGE",1

		+CMT: "+79215629893",,"2019/12/23,19:50:07+03"
		#ts=20;
	'''
	time.sleep(delay)
	szInput = modems.read()
	for i in range(0, 15):
		szInput += modems.read()
		time.sleep(0.05+delay)
	if len(szInput) > 0:
		#print("Modem: %s" % szInput)
		lines = szInput.split('\n')
		for index, line in enumerate(lines):
			if ":" in line:
				cmd = line[0 : line.find(":")]
				vals = line[line.find(":")+2 : line.find("\n")]
				vals = re.sub(r'(,)(?=(?:[^"]|"[^"]*")*$)', ";", vals)
				vals = vals.replace('"','')
				vals = vals.split(';')
				#text = szInput.split('\n')
				#if len(text) > 1:
				#	text = text[1]
				#else:
				#	text = ''
				if(index < len(lines)-1):
					nextLine = lines[index+1]
				else:
					nextLine = ''
				parseGSMstring (cmd, vals, nextLine)
		return szInput
	return ''

isSendingSMS = False
def send_sms(sms_text, phone = ''):
	global lastUsedPhNumb
	global isSendingSMS
	while(isSendingSMS == True):
		pass
	isSendingSMS = True
	if phone == '':
		Log.e("SendSmS","No phone number specified!")
		return
			
	Log.i("SendSmS","Sending sms: '%s' to std numb: '%s'.."% ( sms_text,phone) )
	#centr.printf("log:\r\nSend sms: '%s' to std numb: '%s'",sms_text,ph_numb[i])
	
	send_at("AT+CMGF=1")
	read_serial()
	time.sleep(0.3)
	modems.send("AT+CMGS=\"%s\"\r\n" % phone)#send sms message, be careful need to add a country code before the cellphone number
	read_serial()
	time.sleep(0.3)
	send_at(sms_text)#the content of the message
	
	time.sleep(0.3)
	modems.send("%c" % 26)#the ASCII code of the ctrl+z is 26
	time.sleep(1.5)
	if("OK" in read_serial()):
		print("Ok")
		
	time.sleep(10)
	isSendingSMS = False
def modemPowerOn ():
   
	send_at("AT")
	
	modems.send("AT\r\n")
	if 'OK' in read_serial():
		return
	Log.i("ModemPWR","\n--- Modem init ---\n")
	
	modems.send("AT+CPOWD=1\r\n")
	read_serial()
	if REAL_TEST:
		time.sleep(1)
		pi.write(MODEM_PWR_PIN,0)
		time.sleep(1)
		pi.write(MODEM_PWR_PIN,1)
		time.sleep(0.5)
		pi.write(MODEM_PWR_PIN,1)
		time.sleep(1)
		pi.write(MODEM_PWR_PIN,0)
		time.sleep(1)
	Log.i("ModemPWR","Start init!\n")
	send_at("AT+CREG?")
	
	time.sleep(5)
	send_at("AT+CSQ")
	send_at("AT+CGATT?")
	#send_at("AT+CCLK=\"15/03/09,00:40:50+03\"")
	time.sleep(1)
	#send_at("AT+CIPSTATUS")
	if( "OK" in send_at("AT")):
		Log.i("ModemPWR","GSM Ready!\n")
		HUB_sendACK()
	else:
		restart()



def setTime():
	now = datetime.now()
	if( "OK" in insend_at("AT+CCLK=\"%s+03\"" % datetime.strftime(now, "%y/%m/%d,%k:%M:%S")  ) ):
		print("GSM Ready!\n")
		HUB_sendACK()
#Обработчик сообщений от Arduino в большой комнате.
isWorkingOnCmd = False
lastSmsText = ''
def parseHubCmd(data):
	global isWorkingOnCmd
	global lastSmsText
	while(isWorkingOnCmd == True):
		pass
	isWorkingOnCmd = True
	dataArr = data.split(",")
	if len(dataArr) == 3:
		cmd = dataArr[0].lower()
		arg = dataArr[1].lower()
		val = dataArr[2]
	elif len(dataArr) == 2:
		cmd = dataArr[0].lower()
		arg = dataArr[1].lower()
		val = ''
	else:
		Log.i("parseHubCmd","Hub command incorrect", dataArr)
		return
	if cmd == 'sms' and len(val)>0 and val[0] == "*":
		HUB_sendACK()
		if(val != lastSmsText):
			if arg == 'last' and lastUsedPhNumb != "":
				send_sms(val, lastUsedPhNumb)
			elif ("+" in arg):
				send_sms(val, arg)
			elif arg == 'all' or lastUsedPhNumb == "":
				for numb in ph_numb:
					if numb == '':
						break
					send_sms(val, numb)
			lastSmsText = val
	elif cmd == 'time':
		HUB_sendACK()
		setTime()
	elif cmd == 'power' or cmd == 'pwr':
		HUB_sendACK()
		if arg == 'on' or arg == '1':
			isModemRequired = True
			checkModemAlive()
		else:
			isModemRequired = False
			modemPowerOff()
	isWorkingOnCmd = False
#elif cmd == 'tcp':
	#if arg == 'open':
		#qq
	#if arg == 'send':
		#qq
def onRecieve(msg):
	global isWorkingWithModem
	global isACKwaiting
	global modemUnid
	global modemSetid
	global DriverTCP
	
	if(msg.cmd == "device.heartbeat"):
		#if("OK" in send_at("AT").upper()) and modemSetid != "":
		DriverTCP.sendMsgWithCheck(Msg(unid = modemUnid, setid = modemSetid, cmd="device.reg.renew") )
			#DriverTCP.sendMsgWithCheck(msg)
	elif(msg.cmd == "device.val.set"):
		while isWorkingWithModem == True:
			pass
		isACKwaiting = True
		parseHubCmd(msg.value)
	elif(msg.cmd == "device.reg.res"):
		Log.i("Receive/RegFin","Got SetID", msg.value)
		modemSetid = msg.value.replace(",","")
		Config.set('id', modemSetid)
		HUB_sendACK()
	#print("I got from %s|%s : %s" % (unid,setid,value) )
	
DriverTCP = DriverTCP(2, onRecieve)
modemUnid = "0078"
modemSetid = Config.get('id')
if(modemSetid == ""):
	DriverTCP.registerDevice(modemUnid)

i = 0
try:
	modemPowerOn()
	send_at("AT+CMGDA=\"DEL ALL\"\r\n")
	send_at("AT+CPMS=\"SM\"")
	send_at("AT+CMGD=1,4\r\n")
	#send_at("AT+CPMS=\"ME\",\"SM\",\"MT\"")
	send_at("AT+CPMS=\"ME\"")
	send_at("AT+CMGF=1")
	send_at("AT+CMGD=1,4\r\n")
	#send_at("AT+CMGD=2,4\r\n")
	send_at("AT+CPMS=\"ME\",\"SM\",\"MT\"")
	#send_at("AT+CMGD=1,2\r\n")
	send_at("AT+CNMI=0,2,2,0,0")
	timesOfTime = 0
	checkModemAlive()
	while True: 
		isWorkingWithModem = True
		#if i > 15:
		#	i = 0
		#	checkModemAlive()
		#i += 1
		read_serial(delay = 0.05)
		isWorkingWithModem = False
		time.sleep(0.01)
	

except KeyboardInterrupt:
	#Catch keyboard interrupt
	print('\n\rKeyboard interrtupt') 