import socket
import sys
import os
import time
from Device import Device
from SocketWrap import SocketWrap
from Msg import Msg
from common import Log
from DB import DB
import common
import psutil
import json 
import subprocess
import threading
from functools import partial
import string
import random
class API:
	@staticmethod
	def start():
		f=open("APItoken.txt", "r")
		API.token = f.read()
		f.close() 
		API.threadRun = True
		API.connect()
		API.socketAwaitACK = None
	
	@staticmethod
	def connect():
		try:
			API.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			API.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		except Exception as msg:
			Log.e('API',"Could not create socket. Error Code: "+ str(msg[0])+ " Error: "+ str(msg[1]) )
			DB.registerEvent('','','System','Error starting API server: %i %s' % (msg[0],msg[1] ) )
			sys.exit(0)
		

		HOST = ''
		PORT = int(common.config['HubServer']['PORT'])+1
		Log.i('API',"Socket Created at port "+str(PORT))
		# bind socket
		try:
			API.socket.bind((HOST, PORT))
			Log.i('API',"Socket Bound to port " + str(PORT))
		except Exception as msg:
			Log.e('API',"Bind Failed. Error Code: {} Error: {}".format(str(msg[0]), msg[1]))
			DB.registerEvent('','','System','Error binding socket for API server: %i %s' % (msg[0],msg[1] ) )
			sys.exit()
		API.socket.listen(1)
		threading.Thread(target = API.thread, args=()).start()
	
	@staticmethod
	def thread():
		while API.threadRun:
			conn, addr = API.socket.accept()
			Log.i('API',"API client connected from " + addr[0] + ":" + str(addr[1]))
			threading.Thread(target = API.client_thread, args=(conn,addr, )).start()
	@staticmethod
	def updateConfig():
		with open(CONFIG_PATH, 'wb') as configfile:
			config.write(configfile)
	@staticmethod
	def onValueSetACK(msg, device):
		Log.i('API/OnValueACK',msg.toJSON())
		if (API.socketAwaitACK != None):
			if(msg.cmd == "device.val.set.scheduled"):
				API.socketAwaitACK.send(json.dumps({"errcode": "0", "data": {"msg":"scheduled"}}).encode())
			elif(msg.sendAttempt < 0):
				API.socketAwaitACK.send(json.dumps({"errcode": "2004","msg":"Too many attempts where made", "data": {}}).encode())
			elif(msg.cmd == "ACK" or msg.cmd == "0"):
				API.socketAwaitACK.send(json.dumps({"errcode": "0", "data": {}}).encode())
			API.socketAwaitACK = None
	@staticmethod
	def client_thread(conn, addr):
		conn.settimeout(7)
		conn.setblocking(1)
		try:
			
			#conn.setblocking(0)
			i =0
			while API.threadRun:
				ready = False
				time.sleep(0.2)
				try:
					data = conn.recv(1024)
					if not data:
						break
					#print(data)
					jsonObj = json.loads(data.decode('utf-8'))
					if ('token' not in jsonObj or jsonObj['token'] != API.token):
						conn.send(json.dumps({"errcode": "2003", "msg": "Wrong API token"}).encode())
						conn.close()
					else:
						payload = jsonObj['data']
						if ('cmd' in payload):
							cmd = payload['cmd']
							if (cmd == 'device.value.set'):
								device = Device.findDeviceById(payload['unitId'],payload['setId'])
								Log.i('API/OnValueACK',"Is device online: %i"%device.isOnline)
								while(API.socketAwaitACK !=None):
									continue
								if (device != None):
									API.socketAwaitACK = conn
									device.setValue(payload['value'].strip(), callback=API.onValueSetACK)
									
								else:
									conn.send(json.dumps({"errcode": "3002", "msg": "No such device", "payload":payload}).encode())
							elif (cmd == 'device.value.schedule'):
								device = Device.findDeviceById(payload['unitId'],payload['setId'])
								Log.i('API/OnValueSchedule',"Is device online: %i"%device.isOnline)
								
								if (device != None):
									value = payload['value'].strip()
									print("'",value,"'")
									date = payload['date']
									unid = device.unid
									setid = device.setid
									scriptStr = f'''
newVal = '{value}'
unit    = Device.findDeviceById('{unid}','{setid}')
smsStr = 'sms,all,*'
if unit != None:
	unit.setValue(newVal)
	smsStr = smsStr + 'Value {value} set ok'
else:
	smsStr = smsStr + 'Error setting value {value}'

modems = Device.findDeviceById('0078','')
if len(modems)>0:
	for key, modem in modems.items():
		modem.setValue(smsStr)
'''
									
									uscript = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(5))+".py"
									dir = common.config['HubServer']['USCRIPTS_PATH']+'Temp/'
									path = dir+uscript
									if not os.path.exists(dir):
										os.makedirs(dir)
									outFile = open(path, "w+", encoding="utf-8")
									outFile.write(scriptStr)
									outFile.close()
									DB.sqlInsert(f"""
										INSERT INTO `schedule`
										(
											`type`, 
											`time`, 
											`lastTimeRun`, 
											`nextTimeRun`, 
											`script_name`, 
											`active`
										)
										VALUES
										(
											'1',
											'{date}',
											'',
											'',
											'{uscript}',
											'1'
										); 
									""")
									from Tasker import Task
									Task.getAllTasks()
									conn.send(json.dumps({"errcode": "0", "data": {}}).encode())
								else:
									conn.send(json.dumps({"errcode": "3002", "msg": "No such device", "payload":payload}).encode())
							elif (cmd == 'device.conf.set'):
								device = Device.findDeviceById(payload['unitId'],payload['setId'])
								Log.i('API/OnValueACK',"Is device online: %i"%device.isOnline)
								while(API.socketAwaitACK !=None):
									continue
								if (device != None):
									if(device.isOnline):
										API.socketAwaitACK = conn
										device.setSettings(payload['value'], callback=API.onValueSetACK)
									else:
										conn.send(json.dumps({"errcode": "3003", "msg": "Device offline", "payload":payload}).encode())
									
								else:
									conn.send(json.dumps({"errcode": "3002", "msg": "No such device", "payload":payload}).encode())
							elif (cmd == 'device.reg.notif'):
								unid = payload['unitId']
								setid = payload['setId']
								devices = Device.findDeviceById(unid)
								msg = Msg(unid = unid, setid = setid, cmd="device.reg.notif")
								while(API.socketAwaitACK !=None):
									continue
								isNeedAll = True
								Log.d("API/NotifyNew",devices)
								for key, device in devices.items():
									if(device.mySocketWrap != None):
										API.socketAwaitACK = conn
										device.mySocketWrap.sendMsg(msg)
										isNeedAll = False
										break

								Log.d("API/NotifyNew","[4]Point")
								if isNeedAll:
									for socketWrap in SocketWrap.allSockets:
										socketWrap.sendMsg(msg)
									#print("Disc/Is device online",SocketWrap.allUnits["00B40172"].isOnline)
								conn.send(json.dumps({"errcode": "0", "data": {}}).encode())
							elif ('wifi.update' in cmd):
								interface = 'wlan0'
								name = payload['ssid']
								password = payload['password']
								os.system('iwconfig ' + interface + ' essid ' + name + ' key ' + password)
								conn.send(json.dumps({"errcode": "0", "data": {}}).encode())
							elif ('config.update' in cmd):
								if ('db' in cmd):
									common.config.set('DataBase', 'HOST', payload['host'])
									common.config.set('DataBase', 'USER', payload['login'])
									common.config.set('DataBase', 'PASSW', payload['password'])
									common.config.set('DataBase', 'DB', payload['dbname'])
									common.config.set('DataBase', 'CHARSET', payload['charset'])
									DB.close()
									DB.start()
									Log.i('API/ConfigUpdate/DB',"MySQL reconnect")
									conn.send(json.dumps({"errcode": "0", "data": {}}).encode())
							elif ('schedule.update' in cmd):
								from Tasker import Task
								Task.getAllTasks()
								conn.send(json.dumps({"errcode": "0", "data": {}}).encode())
							elif ('uscript.run' in cmd):
								from Tasker import Task
								res = Task.runUserScriptEnv(payload['uscript'])
								conn.send(json.dumps({"errcode": "0", "data": res}).encode())
							elif (cmd == 'system.stat.get'):
								response = {}
								response['Hub_version'] = common.config['HubServer']['VERSION']
								if ('PortalConnect' in common.config):
									response['Hub_id'] = common.config['PortalConnect']['id']
								response['CPU_load'] = str(psutil.cpu_percent()) + '%'
								memory = psutil.virtual_memory()
								# Divide from Bytes -> KB -> MB
								available = round(memory.available/1024.0/1024.0,1)
								total = round(memory.total/1024.0/1024.0,1)
								response['Memory'] = str(available) + 'MB free / ' + str(total) + 'MB total ( ' + str(memory.percent) + '% )'
								
								disk = psutil.disk_usage('/')
								disk_total = round(disk.total / 2**30,2)     # GiB.
								disk_used = round(disk.used / 2**30,2)
								disk_free = round(disk.free / 2**30,2)
								disk_percent_used = disk.percent
								response['Disk'] = str(disk_free) + 'GB free / ' + str(disk_total) + 'GB total ( ' + str(disk_percent_used) + '% )'
								
								conn.send(json.dumps({"errcode": "0", "data": response}).encode())
							elif (cmd == 'system.cmd'):
								shell = payload['shell']
								Log.i('API',"Executing shell cmd %s"%shell)
								#res = str(check_output(shell.split(" ") ))
								res = subprocess.Popen(shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=10,shell=True, cwd=os.path.dirname(os.path.realpath(__file__))+"/../" )
								stdout,stderr = res.communicate()
								Log.i('API/',"Executing shell cmd res %s"%stdout)
								res = stdout.decode('utf-8')
								resLo = res.lower()
								if ("error" in resLo or "not exists" in resLo or "forbidden" in resLo or "not allow" in resLo or "failed" in resLo): 
									conn.send(json.dumps({"errcode": "2006", "msg": res}).encode())
								else:
									conn.send(json.dumps({"errcode": "0", "data": res}).encode())
							else:
								conn.send(json.dumps({"errcode": "2005", "data": {'cmd':cmd}}).encode())
				except socket.timeout: 
					try:
						if i == 5:
							i = 0
							conn.send("\n")
						i+=1
					except:
						break
				except socket.error as e:
					try:
						if i == 25:
							i = 0
							conn.send(" ")
						i+=1
					except:
						break
				except ValueError as e:
					Log.e('API/ValueError',"While E: %s"%e)
				except:
					conn.send(json.dumps({"errcode": "2003", "msg": "Error proceeding request"}).encode())
					Log.e('API/ValueError',"During API request execution fail")
		except socket.error as e:
			Log.e('API/ValueError'," Closing driver: %s"% e)
		except ValueError as e:
			Log.e('API/ValueError'," Closing driver: %s"% e)
		conn.close()
		Log.i('API/',"API client disconnected: " + addr[0] + ":" + str(addr[1]))
	@staticmethod
	def stop():
		API.threadRun = False
		Log.e('API/Socket'," Stop")
		API.socket.close()
	