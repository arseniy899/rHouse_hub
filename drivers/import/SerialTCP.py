import socket
import pigpio
import time
from thread import start_new_thread
import subprocess
import random
class Serial:
	sock = None
	isSent = False
	data = ''
	def __init__(self, baudrate, txPin, rxPin):
		print('Starting')
		start_new_thread(self.client_thread, ())
		
		# Stopping server
		
	
	def client_thread(self):
		try:
			print 'Connected'
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			server_address = ('localhost', 27020 )
			self.sock.connect(server_address)
			while True:
				self.data = self.sock.recv(1024)
				#print(self.data)
		except ValueError:
			print ('closing socket')
		sock.close()
	def read(self):
		while self.isSent == True and len(self.data) == 0:
			pass
		if 'none' in self.data or 'NONE' in self.data:
			d = ''
		else:
			d = self.data
		self.data = ''
		#print(d)
		self.isSent = False
		return d
		
	def send(self, text):
		if(self.sock != None):
			self.isSent = True
			self.sock.sendall(text)
		print ("Sent to SERIAL: "+text);