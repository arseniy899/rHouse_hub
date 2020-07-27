
import json
import requests
import re
import os
import zipfile


url = 'http://192.168.5.1/service/update/'
urlCheck = url+'update.check.php'
resp = requests.get(url=urlCheck)
jsonObj = resp.json()['responce']
print(resp)
if (jsonObj['error'] != 0):
	print ("Error get info")
else:
	data = jsonObj['data']
	hubGetVer = data['hubVer']
	if ('false' not in str(hubGetVer).lower()):
		major, minor,letter, subNum = re.search('(\d+)\.(\d+)([a-zA-Z]*)(\d?)', hubGetVer).groups()
		getVer = int(major)*1000 + int(minor)*100 + (ord(letter or 'a') - 96)*10 + int(subNum.strip() or 0)
		
		major, minor,letter, subNum = re.search('(\d+)\.(\d+)([a-zA-Z]*)(\d?)', common.config['HubServer']['VERSION']).groups()
		curVer = int(major)*1000 + int(minor)*100 + (ord(letter or 'a') - 96)*10 + int(subNum.strip() or 0)
		
		if(getVer > curVer):
			print ("New HUB version available")
			filename = 'v'+hubGetVer+'.zip'
			zipurl = url + '/hub/' + filename
			resp = requests.get(zipurl)
			zname = os.path.join(filename)
			zfile = open(zname, 'wb')
			zfile.write(resp.content)
			zfile.close()
			with zipfile.ZipFile(zname, 'r') as zip_ref:
				zip_ref.extractall('../hub')
			dir = '../hub/v'+hubGetVer
			os.system("chmod -R 777 "+os.getcwd()+"/"+dir)
			for filename in os.listdir(dir):
				if filename == 'update.exec.py': 
					print("Executing UPDATE script")
					path = dir+"/" + filename
					try:
						fUpdate = open(path, "r")
						updateScript = fUpdate.read()
						updateScript = updateScript.replace("print(","Task.logUserPrint(,")
						updateScript = updateScript.replace("print (","Task.logUserPrint(,")
						updateScript = updateScript.replace("print\t(","Task.logUserPrint(,")
						fUpdate.close()
						print(updateScript) 
						exec(updateScript, locals(), globals())
						Log.d('Update',"Executed " )
						#p = Popen("python3 , shell=True)
						#p.wait()
					except EnvironmentError:
						print('Error open','Path: '+path)
						Log.e('Update','Error open','Path: '+path)
					break
					
			
			os.remove(zname)
			common.config.set('HubServer', 'version', str('v'+hubGetVer))
			print(common.CONFIG_PATH)
			with open(common.CONFIG_PATH, 'w+') as configfile:
				common.config.write(configfile)
				print(configfile)
			#os._exit(1)
			print('Installed new version... rebooting')
			os.system(" ( sleep 60; sudo systemctl restart SH ) &")
		else:
			print('Cur version is OK')
	else:
		print('Cur version is OK')