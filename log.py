from datetime import datetime
import configparser
import os


class Logger:
	time = datetime.now().strftime("%H:%M:%S")
	LOG_FILENAME = f"%type-{time}.log"

	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, '__instance'):
			cls.__instance = super(Logger, cls).__new__(cls)
		return cls.__instance

	def __init__(self):
		config_filename = 'config.ini'
		self.__CONFIG = configparser.ConfigParser()
		self.__CONFIG.read(config_filename)
		self.__log_save_folder = self.__CONFIG.get('LOG', 'log_save_folder')
		self.__LOG_TYPE_FOLDERS = { "info": "info/", "errors": "errors/" }

	def __save_logs(type: str):
		def decorator(func):
			def inner(self, *args, **kwargs):
				try:
					message = func(self, *args, **kwargs)

					if not os.path.isdir(self.__log_save_folder):
						os.mkdir(self.__log_save_folder)
						for folder_type in self.__LOG_TYPE_FOLDERS.keys():
							os.mkdir(os.path.join(self.__log_save_folder, folder_type))

					with open(os.path.join(self.__log_save_folder, self.__LOG_TYPE_FOLDERS[type],
					                       Logger.LOG_FILENAME.replace('%type', type)), 'a') as log_file:
						log_file.write(message + '\n')
				except Exception as e:
					print('\033[31m%s\033[0m' % e)
					print('\033[31m%s\033[0m' % "Error occurred while saving logs")

			return inner
		return decorator

	@__save_logs(type="info")
	def __del__(self):
		message = 'Quitting logger...'
		self.log(message)
		return message

	@__save_logs(type="info")
	def log(self, message: str) -> str:
		time = self.get_local_time()
		msg = '[ %s ] - %s' % (time, message)
		print(msg)
		return msg

	@__save_logs(type="info")
	def info(self, message: str) -> str:
		time = self.get_local_time()
		msg = '[ %s ][ INFO ] - %s' % (time, message)
		colorized_msg = ('[ %s ]' % time) + self.blue('[ INFO ]') + (' - %s' % message)
		print(colorized_msg)
		return msg

	@__save_logs(type="errors")
	def error(self, message: str) -> str:
		time = self.get_local_time()
		msg = '[ ERROR ][ %s ] - %s' % (time, message)
		colorized_msg = '\033[31m%s\033[0m' % msg
		print(colorized_msg)
		return msg

	def green(self, text):
		return "\033[32m%s\033[0m" % (text)

	def blue(self, text):
		return "\033[34m%s\033[0m" % (text)

	def yellow(self, text):
		return "\033[33m%s\033[0m" % (text)

	def get_local_time(self):
		return datetime.now().strftime("%H:%M:%S")

	__save_logs = staticmethod(__save_logs)
