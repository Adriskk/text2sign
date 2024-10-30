from setup import Setup
from log import Logger

if __name__ == '__main__':
	logger = Logger()
	logger.info('Program has started')

	setup = Setup()
	setup.scrape()
