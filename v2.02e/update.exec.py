DB.sqlUpdate("UPDATE `units_def` SET `direction` = 'O' WHERE (`unid` = '0118');")
path = common.config['HubServer']['USCRIPTS_PATH']+"SYS/clearOldValuesDb.py"
scriptStr = '''
sql = """
SELECT `script_name` FROM schedule
	WHERE 	`type` =  '1'
    AND		`time` < (CURRENT_TIMESTAMP)
    AND 	`script_name`  LIKE '%Temp%'
    AND 	`active` = 0;
""";
data = DB.sqlSelect(sql);
print(data)
path = common.config['HubServer']['USCRIPTS_PATH']
for line in data:
	file = line['script_name']
	if os.path.isfile(path+file):
		os. remove(path+file)
ql = """
DELETE FROM schedule
	WHERE 	`type` =  '1'
    AND		`time` < (CURRENT_TIMESTAMP)
    AND 	`script_name`  LIKE '%Temp%'
    AND 	`active` = 0;
""";
DB.sqlUpdate(sql);

'''
outFile = open(path, "a+", encoding="utf-8")
outFile.write(scriptStr)
outFile.close()