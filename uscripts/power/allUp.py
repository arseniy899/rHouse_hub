## self, uscript, value
import time
import os
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
print('1')
os.system("killall shutdown")
os.system("sudo shutdown -c")
print('2')
modems = Device.findDeviceById('0078','')
pwrStr = 'power,on'
print(modems)
if len(modems)>0:
	for key, modem in modems.items():
		modem.setValue(pwrStr)
time.sleep(10)
pwrStr = 'sms,all,*Power: Returned'
if len(modems)>0:
	for key, modem in modems.items():
		modem.setValue(pwrStr)

cams = Device.findDeviceById('008C','')
camsStr = 'up'
if len(cams)>0:
	for key, cam in cams.items():
		cam.setValue(camsStr)

