import configparser
from configparser import NoOptionError, NoSectionError
import pandas as pd
from log import Logger
import os

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')


class VideoDataManager:
	def __init__(self):
		self.__logger = Logger()

		try:
			self.__save_filename = CONFIG.get('CSV', 'save_file_name') + ".csv"
			self.__save_folder = CONFIG.get('CSV', 'save_file_path')
		except NoOptionError:
			self.__logger.error('[ VDM ] There was an error while getting data from config.ini file - no option like %s or %s available' % ('save_file_name', 'save_file_path'))
		except NoSectionError:
			self.__logger.error(
				'[ VDM ] There was an error while getting data from config.ini file - no section like %s available' % (
				'CSV'))

		self.__data = self.load()
		self.__logger.info('[ VDM ] Successfully initialized Video Data Manager instance')

	def __save(func):
		def inner(self, *args, **kwargs):
			letter = func(self, *args, **kwargs)

			if not os.path.isdir(self.__save_folder):
				os.mkdir(self.__save_folder)
				os.mkdir(letter)

			df = pd.DataFrame(self.__data[letter])
			path = os.path.join(self.__save_folder, letter, self.__save_filename)
			df.to_csv(path, index=False)
			self.__logger.log('[ VDM ] Saved data in csv file')
		return inner

	@__save
	def add_row(self, row: dict, letter: str):
		if letter not in self.__data.keys():
			self.__logger.error('[ VDM ] This letter key doesn\'t exist in dataset')
			self.add_letter(letter)

		self.__data[letter].append(row)
		self.__logger.log('[ VDM ] Added row to data')

		return letter.upper()

	def add_letter(self, letter: str):
		letter = letter.upper()
		if not os.path.isdir(self.__save_folder): os.mkdir(self.__save_folder)
		if os.path.isdir(self.__save_folder + letter): return

		os.mkdir(self.__save_folder + letter)
		self.__data[letter] = []
		self.__logger.log('[ VDM ] Added letter key to data')

	def value_exists(self, value) -> bool:
		for key in self.__data.keys():
			for row in self.__data[key]:
				for row_key in row.keys():
					if row[row_key] == value:
						return True
		return False

	def load(self):
		if os.path.isdir(self.__save_folder):
			data = {}
			for dir in os.listdir(self.__save_folder):
				path = os.path.join(self.__save_folder, dir, self.__save_filename)
				if os.path.isfile(path):
					data[dir] = (pd.read_csv(path).to_dict(orient='records'))
				else:
					data[dir] = []
			return data
		else:
			return {}

	__save = staticmethod(__save)
