import pigpio
import time
from Log import Log
import subprocess
class Serial:
	def __init__(self, baudrate, txPin, rxPin):
		self.baudrate = baudrate
		self.txPin = txPin
		self.rxPin = rxPin
		self.serialpi=pigpio.pi()
		self.serialpi.set_mode(self.rxPin,pigpio.INPUT)
		self.serialpi.set_mode(self.txPin,pigpio.OUTPUT)

		pigpio.exceptions = False
		self.serialpi.bb_serial_read_close(self.rxPin)
		pigpio.exceptions = True

		self.serialpi.bb_serial_read_open(self.rxPin,self.baudrate,8)
		Serial.isSending = False
	def read(self):
		#for _ in range(10): 
		time.sleep(0.05)
		(count, data) = self.serialpi.bb_serial_read(self.rxPin)
		if data != "":
			try:
				data = str(data, 'utf-8')
			except:
				data = ''
			Log.i("Serial","Received:",data)
			return data
		else:
			return "";
#		return "";
	def send(self, text):
		while(Serial.isSending == True):
			pass
		Serial.isSending = True
		pigpio.exceptions = False
		self.serialpi.bb_serial_read_close(self.rxPin)
		pigpio.exceptions = True
		self.serialpi.wave_clear()
		Log.i("Serial","Sending",text)
		#self.serialpi.wave_add_serial(self.txPin,self.baudrate,text+'\r\n', bb_bits=8)
		self.serialpi.wave_add_serial(self.txPin,self.baudrate,text)
		wid=self.serialpi.wave_create()
		
		self.serialpi.bb_serial_read_open(self.rxPin, self.baudrate, 8)
		self.serialpi.wave_send_once(wid)
		self.serialpi.wave_delete(wid)   
		while self.serialpi.wave_tx_busy():
			pass
		Serial.isSending = False
		#print ("Send ok";)