import configparser
from configparser import NoOptionError, NoSectionError
import pandas as pd
from log import Logger
import os

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

# TODO Create file save system for each letter
class VideoDataManager:
	def __init__(self):
		self.__logger = Logger()

		try:
			self.__save_filename = CONFIG.get('CSV', 'save_file_name') + ".csv"
			self.__save_folder = CONFIG.get('CSV', 'save_file_path')
			self.__save_pathname = self.__save_folder + self.__save_filename
		except NoOptionError:
			self.__logger.error('There was an error while getting data from config.ini file - no option like %s or %s available' % ('save_file_name', 'save_file_path'))
		except NoSectionError:
			self.__logger.error(
				'There was an error while getting data from config.ini file - no section like %s available' % (
				'CSV'))

		self.__data = self.load()
		print(self.__data)
		self.__logger.info('Successfully initialized Video Data Manager instance')

	def __save(func):
		def inner(self, *args, **kwargs):
			func(self, *args, **kwargs)

			if not os.path.isdir(self.__save_folder):
				os.mkdir(self.__save_folder)

			df = pd.DataFrame(self.__data)
			df.to_csv(self.__save_pathname, index=False)
			self.__logger.log('Saved data in csv file')
		return inner

	@__save
	def add_row(self, row: dict, letter: str):
		if letter not in self.__data.keys():
			self.__logger.error('')

		self.__data[letter].append(row)
		self.__logger.log('Added row to data')

	@__save
	def add_letter(self, letter: str):
		self.__data[letter] = []
		self.__logger.log('Added letter to data')

	def value_exists(self, value) -> bool:
		for key in self.__data.keys():
			for row in self.__data[key]:
				for row_key in row.keys():
					if row[row_key] == value:
						return True
		return False

	def load(self):
		if os.path.isfile(self.__save_pathname):
			data = pd.read_csv(self.__save_pathname)
			return data.to_dict(orient='records')
		else:
			return {}

	__save = staticmethod(__save)
