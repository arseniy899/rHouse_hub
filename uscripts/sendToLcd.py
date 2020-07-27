
lcds    = Device.findDeviceById('01C8','')
#tempin  = Device.findDeviceById('01B8','0001')
#tempout = Device.findDeviceById('01B8','0002')

camAlarmCount = 0
camStr = '0'
cameras    = Device.findDeviceById('008c','')
if len(cameras)>0:
	for key, camera in cameras.items():
		if(camera.lastValue == '1'):
			camAlarmCount += 1
	if(camAlarmCount == 0):
		camStr = '0'
	else:
		camStr = '1'
#pwr = Device.findDeviceById('00C8','0001')


now = datetime.now()
timeStr =  datetime.strftime(now, "%H;%M;%S")
# 0,hours,minutes,seconds,temp_out,cur_security,power;
#reportStr = timeStr+","+tempout.lastValue+","+wanscam.lastValue+","+","+pwr.lastValue
reportStr = timeStr+";128;"+camStr+";1"
#print(heater)
if len(lcds)>0:
	for key, value in lcds.items():
		value.setValue(reportStr)	
