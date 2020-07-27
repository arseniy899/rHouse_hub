from DB import DB
import os
sql = """
DELETE FROM events
WHERE time  < DATE_SUB(NOW(), INTERVAL 14 DAY)
""";
DB.sqlUpdate(sql);
sql = """
DELETE FROM units_values
WHERE timeStamp  < DATE_SUB(NOW(), INTERVAL 14 DAY)
""";
DB.sqlUpdate(sql);
sql = """
DELETE FROM alerts
WHERE time  < DATE_SUB(NOW(), INTERVAL 14 DAY)
""";
DB.sqlUpdate(sql);

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
