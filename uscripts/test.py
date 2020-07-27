'''print("SSS")
for key, value in SocketWrap.onlineUnits.copy().items():
	print(value.unid+":"+value.setid)'''
#power = Device.findDeviceById('00C8','')
#print(power)
cameras	= Device.findDeviceById('008c','')
if len(cameras)>0:
	for key, camera in cameras.items():
		print(camera.lastValue)
		if(camera.lastValue == '1'):
			camAlarmCount += 1
	if(camAlarmCount == 0):
		camStr = 'off'
	elif(camAlarmCount == len(cameras)):
		camStr = 'on'
	else:
		camStr = 'on/off'

print(camStr)