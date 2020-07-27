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
print "Sending SMS Report about security"
modems = Device.findDeviceById('0078','')
if value == '0':
	secur = 'off'
else:
	secur = 'on'
repStr = "Security now is %s" % secur
repStr = 'sms,all,'+repStr
if len(modems)>0:
	for key, modem in modems.items():
		modem.setValue(repStr)