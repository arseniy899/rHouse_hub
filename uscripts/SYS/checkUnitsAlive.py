#from DB import DB
sql = """UPDATE `units_run` SET `alive` = '0';""";
DB.sqlUpdate(sql);
for key, value in SocketWrap.onlineUnits.copy().items():
	print(value.unid+" "+value.setid)
	value.sendHeartBeat()
