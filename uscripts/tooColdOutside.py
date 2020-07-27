print("HEY! It's too cold outside! Let's turn on heater")
heater = Device.findDeviceById('00B4','')
#print(heater)
if len(heater)>0:
	for key, value in heater.items():
		value.setValue('20')	
print('sss',55)