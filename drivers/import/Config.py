import sys
import csv
import os.path
from Log import Log
PY3 = sys.version_info.major > 2
class Config:
	#static:
	#data = None
	#filename = 'c.properties'
	
	@staticmethod
	def start(defaultConfig):
		
		Config.filename = os.getcwd()+'/c.properties'
		Config.defaultConfig = defaultConfig
		if os.path.isfile(Config.filename) == False:
			Config.data = defaultConfig
			Config._write_properties()  # Create csv from data dictionary.
		else:
			Config.data = Config._read_properties()  # Read it back into a new dictionary.
		Log.i('ConfigParser','Properties read: ',Config.data)
		
		
	
	@staticmethod
	def get(key):
		if (key in Config.data):
			Log.d('ConfigParser',"Got property '%s' with value '%s'." % (key, Config.data[key]))
			return Config.data[key]
		elif (key in Config.defaultConfig):
			Config.set(key,Config.defaultConfig[key])
			
			return Config.defaultConfig[key]
		else:
			Log.e('ConfigParser',"No property '%s' found in config." % key)
			return "";
			
	
	@staticmethod
	def set(key, value):
		Config.data[key] = value;
		Log.d('ConfigParser',"Setting property '%s' with value '%s'." % (key, value))
		Config._write_properties()
	@staticmethod
	def _read_properties(delimiter='='):
		""" Reads a given properties file with each line in the format:
			key<delimiter>value. The default delimiter is '='.

			Returns a dictionary containing the pairs.
		"""
		open_kwargs = dict(mode='r', newline='') if PY3 else dict(mode='rb')

		with open(Config.filename, **open_kwargs) as csvfile:
			reader = csv.reader(csvfile, delimiter=delimiter, escapechar='\\',
								quoting=csv.QUOTE_NONE)
			return {row[0]: row[1] for row in reader}

	@staticmethod
	def _write_properties(delimiter='='):
		""" Writes the provided dictionary in key-sorted order to a properties
			file with each line of the format: key<delimiter>value
			The default delimiter is ':'.
		"""
		open_kwargs = dict(mode='w', newline='') if PY3 else dict(mode='wb')

		with open(Config.filename, **open_kwargs) as csvfile:
			writer = csv.writer(csvfile, delimiter=delimiter, escapechar='\\',
								quoting=csv.QUOTE_NONE)
			writer.writerows(sorted(Config.data.items()))
