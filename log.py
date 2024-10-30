from time import gmtime, strftime
import configparser
import os


class Logger:
	time = strftime("%d-%B-%Y-%H-%M-%S", gmtime())
	LOG_FILENAME = f"%type-{time}.log"

	def __init__(self):
		config_filename = 'config.ini'
		self.__CONFIG = configparser.ConfigParser()
		self.__CONFIG.read(config_filename)
		self.__log_save_folder = self.__CONFIG.get('LOG', 'log_save_folder')
		self.__LOG_TYPE_FOLDERS = { "info": "info/", "errors": "errors/" }

	def __save_logs(type: str):
		def decorator(func):
			def inner(self, *args, **kwargs):
				message = func(self, *args, **kwargs)

				if not os.path.isdir(self.__log_save_folder):
					os.mkdir(self.__log_save_folder)
					for folder_type in self.__LOG_TYPE_FOLDERS.keys():
						os.mkdir(os.path.join(self.__log_save_folder, folder_type))

				with open(os.path.join(self.__log_save_folder, self.__LOG_TYPE_FOLDERS[type],
				                       Logger.LOG_FILENAME.replace('%type', type)), 'a') as log_file:
					log_file.write(message + '\n')

			return inner
		return decorator

	@__save_logs(type="info")
	def __del__(self):
		return "Quitting logger"

	@__save_logs(type="info")
	def log(self, message: str) -> str:
		time = strftime("%H:%M:%S", gmtime())
		msg = '[ %s ] - %s' % (time, message)
		print(msg)
		return msg

	@__save_logs(type="info")
	def info(self, message: str) -> str:
		time = strftime("%H:%M:%S", gmtime())
		msg = '[ INFO ][ %s ] - %s' % (time, message)
		colorized_msg = ('[ %s ]' % time) + self.blue('[ INFO ]') + (' - %s' % message)
		print(colorized_msg)
		return msg

	@__save_logs(type="errors")
	def error(self, message: str) -> str:
		time = strftime("%H:%M:%S", gmtime())
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

	__save_logs = staticmethod(__save_logs)
