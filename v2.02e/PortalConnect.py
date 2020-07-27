import socket, sys, traceback, os, time, errno
from common import Log
from DB import DB
from configparser import ConfigParser
import psutil, common, json, subprocess, threading, re
from functools import partial
from subprocess import check_output
import select
class PortalConnect:
	@staticmethod
	def start():
		PortalConnect.config = common.config
		if('PortalConnect' in PortalConnect.config):
			PortalConnect.IP = PortalConnect.config ['PortalConnect']['GATE-IP']
			#PortalConnect.IP = 'localhost'
			
			PortalConnect.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			res = str(check_output(["sudo","ls","-l","/etc/ppp/peers/"]))

			if "main" not in res:
				vpnConfig = "pptpsetup --create main --server %s --username %s --password %s --encrypt MPPE --start" % (common.config['PortalConnect']['PUBLIC-IP'],common.config['PortalConnect']['user'],common.config['PortalConnect']['passw'])
				res =  str(check_output(vpnConfig.split(" ")))
				Log.i("VPN Setup","pptpsetup create main:",res)
			else:
				print(os.system("sudo poff -a") )
				
			res = os.system("sudo pon main updetach persist")
			print(res)
			if res != 0:	
				Log.e("VPN Setup","Error connecting to VPN server(",res)
			threading.Thread(target = PortalConnect.connect, args=()).start()
			
		else:
			Log.w('PortalConnect',"Hub server not registed, so working in 'offline' mode. Run 'register.py'")
			#os._exit(1)
	
	@staticmethod
	def checkVPN():
		res = str(check_output("ifconfig".split(" ") ))
		Log.i("PortalConnect","Checking for VPN res:",res)
		if "ppp" not in res:
			res = os.system("sudo pon main updetach persist")
			print(res)
			if res != 0:	
				Log.e("VPN Setup","Error connecting to VPN server(",res)
			
	@staticmethod
	def getMaxVer():
		version = {}
		#for folder in os.listdir(os.getcwd()):
		#	if(folder.startswith('v')):
		#major, minor,letter, subNum = re.search('(\d+)\.(\d+)([a-zA-Z]*)(\d?)', common.config['HubServer']['VERSION']).groups()
		#version [int(major)*1000 + int(minor)*100 + (ord(letter or 'a') - 96)*10 + int(subNum.strip() or 0)] = folder
		#return version[max(version)]
		return common.config['HubServer']['VERSION']
	@staticmethod
	def get_lan_ip():
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		return s.getsockname()[0]
	@staticmethod
	def connect():
		connected = False
		while True:
			try:
				if(connected == False):
					Log.i("PortalConnect","Connecting to PORTAL",PortalConnect.IP, 4046)
					PortalConnect.checkVPN()
					server_address = (PortalConnect.IP, 4046 )
					PortalConnect.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					PortalConnect.sock.connect(server_address)
					PortalConnect.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
					PortalConnect.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
					PortalConnect.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
					PortalConnect.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
					Log.i("PortalConnect","Connected to PORTAL")
					PortalConnect.sock.settimeout(3)
					data = {
						'cmd'		: 'register.renew',
						'locIP' 	: PortalConnect.get_lan_ip(),
						'webVer'	: PortalConnect.config ['PortalConnect']['webVer'],
						'hubVer' 	: PortalConnect.getMaxVer(),
						'id' 		: PortalConnect.config ['PortalConnect']['id'],
						
					}
					#PortalConnect.sock.setblocking(0)
					connected = True
					PortalConnect.sock.sendall(json.dumps({"data":data}).encode())
					PortalConnect.thread()
				#data = PortalConnect.sock.recv(1024)
				#Log.i('PortalConnect', "ReReged: ", data)
				#PortalConnect.sock.sendall(b"")
				
				time.sleep(1)
				#if not data:
					#connected = False
					#break
			except ConnectionError as e:
				Log.e('PortalConnect/Connect',"While E: %s"%e)
				connected = False
				time.sleep(5)
				#break
			except ValueError as e:
				Log.e('PortalConnect/Connect',"While E: %s"%e)
				connected = False
				time.sleep(5)
			except socket.error as e:
				#if(e.errno != 11):
				Log.w('PortalConnect/Connect',"Retrying...\n%s"%e)
				connected = False
				time.sleep(5)
				
		
	@staticmethod
	def sendJS(json):
		PortalConnect.sock.sendall(json.encode())
		
	@staticmethod
	def setupVPN(user, pwd):
		IP = PortalConnect.IP
		# setting UP VPN
	@staticmethod
	def thread():
		try:
			conn = PortalConnect.sock
			start = time.clock()
			Log.i('PortalConnect/Thread','Connected')
			i =0
			while True:
				time.sleep(0.002)
				try:
					ready_to_read, ready_to_write, in_error = select.select([conn,], [conn,], [], 5)
				except select.error:
					conn.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
					# connection error event here, maybe reconnect
					
					break
				
				#Log.d('PortalConnect/Time',(time.clock() - start))
				if ((time.clock() - start) > 5.0):
					#Log.d('PortalConnect/Thread','Keep Alvie sent')
					conn.sendall("".encode())
					start = time.clock()
				#try:
				#if len(ready_to_read) > 0:
				data = PortalConnect.sock.recv(len(ready_to_read))
				#if not data:
				#	break
				data = data.decode('utf-8')
				if(data != ""):
					for line in data.split("\n"):
						if len(line)>2:
							Log.i('PortalConnect/Thread','received "%s"' % line)
								
				#time.sleep(0.3)
				#else:
					#break
				'''except socket.timeout: 
					#self.tcpConn.setblocking(0)
					try:
						if i == 5:
							i = 0
							PortalConnect.sock.send("\n".encode())
							time.sleep(0.1)
						i+=1
					except Exception as e:
						Log.e('PortalConnect/ValueError',e)
						break#pass
				except ValueError as e:
					pass
				except socket.error as e:
					#print("[D] While E ", e)
					try:
						if i == 5:
							i = 0
							#self.tcpConn.send("\n")
							PortalConnect.sock.send(" ".encode())
							time.sleep(0.1)
						i+=1
					except Exception as e:
						Log.e('PortalConnect/ValueError',e)
						break
					#pass
				except Exception as e:
					if('Broken pipe'in str(e).lower()):
						Log.e('PortalConnect/Thread',"While E:",e)
						break'''
		except socket.error:
			Log.e('PortalConnect/Thread/1',"Closing socket: %s "% socket.error,traceback.format_exc())
		except Exception as e:
			exc = str(e)
			Log.e('PortalConnect/Thread/2',' %s \n %s' % (exc,traceback.format_exc()))
		Log.e('PortalConnect/Thread/3',"Closing socket")
		#except ValueError:
			#print ('closing socket', ValueError)
		PortalConnect.sock.shutdown(2)
		PortalConnect.sock.close()
		PortalConnect.connect()
	@staticmethod
	def updateConfig():
		with open(CONFIG_PATH, 'wb') as configfile:
			PortalConnect.config.write(configfile)
	
	@staticmethod
	def stop():
		PortalConnect.socket.close()
	