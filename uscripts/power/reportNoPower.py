## self, uscript, value
import time
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
modems = Device.findDeviceById('0078','')
pwrStr = 'sms,all,*Power: No power'
if len(modems)>0:
	for key, modem in modems.items():
		modem.setValue(pwrStr)
