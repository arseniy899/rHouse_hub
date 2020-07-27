# -*- coding: utf-8 -*-
import MySQLdb
import MySQLdb.cursors
import time
import common
from common import Log
from time import localtime, strftime
alertsTexts = {
		1001: 'Добавлено новое устройство.',
		1002: 'Устройство передаёт данные в неверном формате',
		1003: 'Обнаружено устройство с неверным ID',
		1004: 'Обнаруженное устройство неопознано',
		1005: 'Указанный скрипт не найден',
		1006: 'Ошибка доставки сообщения',
		1007: 'Ошибка выполнения скрипта',
		1008: 'Устройство в сети, но недоступно'
	}
class DB:
	@staticmethod
	def start():
		dbLink = MySQLdb.connect(host=str(common.config['DataBase']['HOST']),
					user=str(common.config['DataBase']['USER']),
					passwd=str(common.config['DataBase']['PASSW']),
					db=str(common.config['DataBase']['DB']),
					charset=str(common.config['DataBase']['CHARSET']),
					use_unicode=True,
					cursorclass=MySQLdb.cursors.DictCursor)
		
		dbLink.ping(True)
		return dbLink, dbLink.cursor()
	@staticmethod
	def sqlSelect(sql):
		data = []
		dbLink, dbCursor = DB.start()
		try:
			
			dbCursor.execute(sql)
			dbLink.commit()
			data = (dbCursor.fetchall())
		except (AttributeError, MySQLdb.OperationalError):
			dbLink, dbCursor = DB.start()
			dbCursor.execute(sql)
			data = (dbCursor.fetchall())
		except MySQLdb.Error as e:
			Log.e('DB'," MySQL.Error: %s"% e)
			dbCursor.close()
			dbLink.close()
		dbCursor.close()
		dbLink.close()
		time.sleep(0.1) # workaround for MySQL cursor hang
		return data
	@staticmethod
	def close():
		if DB._dbLink != None:
			DB._dbLink.close()
	@staticmethod
	def sqlUpdate(sql):
		dbLink, dbCursor = DB.start()
		try:
			
			dbCursor.execute(sql)
			dbLink.commit()
		except (AttributeError, MySQLdb.OperationalError):
			dbLink, dbCursor = DB.start()
			dbCursor.execute(sql)
		except MySQLdb.Error as e:
			Log.e('DB'," MySQL.Error: %s"% e)
			dbCursor.close()
			dbLink.close()
		dbCursor.close()
		dbLink.close()
		
		time.sleep(0.1) # workaround for MySQL cursor hang
	@staticmethod
	def addAlert(unid,setid,code,msg=''):
		global alertsTexts
		text = ''
		if code in alertsTexts:
			text = alertsTexts[code]
		DB.sqlInsert("""
			INSERT INTO `alerts` 	(`unid`, 	`setid`, 	`code`, `text`, `time`) VALUES ('%s', '%s', '%i', '%s', '%s')
		""" % 					 	(unid, 		setid,		code,	(text+"\\n"+str(msg).replace("'","""\\'""") ), strftime("%Y.%m.%d %H:%M:%S", localtime()) )  )
	@staticmethod
	def registerEvent(unid,setid,level,event):
		global alertsTexts
		DB.sqlInsert("""
			INSERT INTO `events` (`unid`, `setid`, `level`,`event`, `time`) VALUES ('%s', '%s','%s', '%s', '%s')
		""" % (unid, setid, level,event, strftime("%Y.%m.%d %H:%M:%S", localtime()) )  )
	@staticmethod
	def sqlInsert(sql):
		dbLink, dbCursor = DB.start()
		try:
			
			dbCursor.execute(sql)
			dbLink.commit()
		except (AttributeError, MySQLdb.OperationalError):
			dbLink, dbCursor = DB.start()
			dbCursor.execute(sql)
		except MySQLdb.Error as e:
			Log.e('DB'," MySQL.Error: %s"% e)
			dbCursor.close()
			dbLink.close()
		dbCursor.close()
		dbLink.close()
		
		
		time.sleep(0.1)  # workaround for MySQL cursor hang
		return dbCursor.lastrowid