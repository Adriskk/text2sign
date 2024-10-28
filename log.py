from time import gmtime, strftime


class Logger:
	def __init__(self):
		pass

	def log(self, message: str):
		time = strftime("%H:%M:%S", gmtime())
		print('[ %s ] - %s' % (time, message))

	def info(self, message: str):
		time = strftime("%H:%M:%S", gmtime())
		print(self.blue('[ INFO ][ %s ] - %s' % (time, message)))

	def error(self, message: str):
		time = strftime("%H:%M:%S", gmtime())
		print('\033[31m[ ERROR ][ %s ] - %s\033[0m' % (time, message))

	def green(self, text):
		return "\033[32m%s\033[0m" % (text)

	def blue(self, text):
		return "\033[34m%s\033[0m" % (text)

	def yellow(self, text):
		return "\033[33m%s\033[0m" % (text)

