## self, uscript, value
import re
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
from datetime import datetime
print "Sending SMS Report about power"
modems = Device.findDeviceById('0078','')
dataArr = value.split(",")
if len(dataArr) != 3:
	print("Hub command incorrect", dataArr)
	return
#sms,<number>,<cmd>
cmd = dataArr[0].lower() # sms
arg = dataArr[1].lower() #number
val = dataArr[2].lower() #sec=f
if val == '0':
	repStr = 'Heads up: No electricity'
else:
	repStr = 'All ok: Electricity returned'
#print(heater)
repStr = 'sms,all,'+repStr
if len(modems)>0:
	for key, modem in modems.iteritems():
		modem.setValue(repStr)