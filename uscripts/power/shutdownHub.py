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
Power:
    0  - all UP
	1  - no any energy
	2  - no Mains only (external)
	-1 - kinda error (no power supply but Mains exist)
'''
modems = Device.findDeviceById('0078','')
print('System lost all power! \n Scheduled switch off in 5 minutes')
time.sleep(20)	
pwrStr = 'power,off,'
if len(modems)>0:
	for key, modem in modems.iteritems():
		modem.setValue(pwrStr)
os.system("sudo shutdown -H +5")