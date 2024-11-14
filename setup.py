import configparser
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import exceptions
from bs4 import BeautifulSoup
import requests

from log import Logger
from data import VideoDataManager


class Setup:
	def __init__(self):
		self.__logger = Logger()
		self.__vdm = VideoDataManager()

		self.__logger.info('Initialized Setup object')
		self.__logger.info('Created Video Data Manager object')

		config_filename = 'config.ini'
		self.__CONFIG = configparser.ConfigParser()
		self.__CONFIG.read(config_filename)
		self.__SECTIONS = {"driver": "DRIVER", "video": 'VIDEO'}
		self.__logger.info('Loaded config from %s file' % (config_filename))

		self.__CHROME_DRIVER_PATH = self.__CONFIG.get(self.__SECTIONS["driver"], 'driver_rel_path')
		self.__START_URL = self.__CONFIG.get(self.__SECTIONS['driver'], 'driver_scraping_start_url')

		self.__chrome_options = webdriver.ChromeOptions()
		self.__chrome_options.add_experimental_option("detach", True)
		self.__chrome_options.enable_downloads = True
		self.__chrome_options.add_argument('--ignore-certificate-errors')
		self.__chrome_options.add_argument("--test-type")

		self.__HANDLES = {
			"letter_buttons": {"type": By.CSS_SELECTOR, "handle": ".wlbutton"},
			"consent": {"type": By.CSS_SELECTOR, "handle": ".fc-cta-consent"},
			"video_tabs_list_items": {"type": By.CSS_SELECTOR, "handle": ".search_results ul li"},
			"video_tabs_list_items_link": {"type": By.CSS_SELECTOR, "handle": ".search_results ul li a"},
			"source": {"type": By.CSS_SELECTOR, "handle": ".videocontent video source"},
		}

	def scrape(self):
		with webdriver.Chrome(keep_alive=True) as self.__chrome_driver:
			try:
				self.__logger.log('Created driver instance')
				self.__chrome_driver.get(self.__START_URL)

				self.__logger.log('Opening url in chrome browser')
				self.__chrome_driver.maximize_window()
				TABS = {"DEFAULT": self.__chrome_driver.current_window_handle}

				try:
					# Accept consent if available
					self.__accept_consent()

					# Find alphabet buttons
					self.__logger.log('Waiting for letter buttons to be visible...')
					WebDriverWait(self.__chrome_driver, 10).until(
						EC.presence_of_element_located(
							(self.__HANDLES["letter_buttons"]["type"], self.__HANDLES["letter_buttons"]["handle"]))
					)

					HREFS = []
					self.__logger.log('Found letter buttons')
					alphabet_btns = self.__chrome_driver.find_elements(self.__HANDLES["letter_buttons"]["type"],
					                                            self.__HANDLES["letter_buttons"]["handle"])
					self.__logger.log('Scraping aplhabet urls...')
					if alphabet_btns:
						for btn in alphabet_btns:
							HREFS.append(btn.get_attribute('href'))
						self.__logger.log('Finished')

						# Opening tab for every letter and scraping video tab links
						self.__logger.log('Going through every scraped url...')
						for href in HREFS:
							self.__logger.log('Current URL - %s' % (self.__logger.green(href)))
							self.__chrome_driver.execute_script('window.open('');')

							current_letter = href.split('/')[-1]
							self.__vdm.add_letter(current_letter)
							self.__logger.info('Current letter - %s' % (current_letter))

							for handle in self.__chrome_driver.window_handles:
								if handle not in TABS.values():
									# Save tab
									self.__logger.log('Saving newly created tab - %s' % (handle))
									TABS[href] = handle
									break

							# Switch to newly created tab
							self.__logger.log(
								'Switching to %s tab and loading %s url' % (self.__logger.green(TABS[href]), href))
							self.__chrome_driver.switch_to.window(TABS[href])
							self.__chrome_driver.get(href)

							# Get list of all video tab links
							try:
								self.__logger.log('Waiting for video tabs items to be visible...')
								WebDriverWait(self.__chrome_driver, 16).until(
									EC.presence_of_element_located(
										(self.__HANDLES["video_tabs_list_items"]["type"],
										 self.__HANDLES["video_tabs_list_items"]["handle"]))
								)

								self.__logger.log('Found video tabs items')
								items = self.__chrome_driver.find_elements(self.__HANDLES["video_tabs_list_items"]["type"],
								                                    self.__HANDLES["video_tabs_list_items"]["handle"])
								if items:
									items = [item.text for item in items]

									# Open each video tab
									for item in items:
										folder = self.__CONFIG.get(self.__SECTIONS['video'],
										                    'output_folder') + current_letter
										filename = self.get_filename(item)

										# Checking if video already exists in folder
										if os.path.isdir(folder):
											exists = False
											existing_file = None

											for file in os.listdir(folder):
												if file.startswith(filename):
													exists = True
													existing_file = file
													break
											if exists:
												if not self.__vdm.value_exists(item):
													self.__logger.info('Adding existing video %s to .csv' % (self.__logger.yellow(item)))
													self.__vdm.add_row(
														{
															"title": item,
															"video_path": os.path.join(folder, existing_file),
														},
														letter=current_letter
													)
												else:
													self.__logger.info('Video %s already exists, skipping to next' % (filename))

												continue
										self.__chrome_driver.implicitly_wait(2)

										try:
											WebDriverWait(self.__chrome_driver, 16).until(
												EC.presence_of_element_located(
													(self.__HANDLES["video_tabs_list_items_link"]["type"],
													 self.__HANDLES["video_tabs_list_items_link"]["handle"]))
											)

											links = self.__chrome_driver.find_elements(
												self.__HANDLES["video_tabs_list_items_link"]["type"],
												self.__HANDLES["video_tabs_list_items_link"]["handle"])

										except exceptions.NoSuchElementException:
											self.__logger.error('Item video link was not found')
											continue
										except exceptions.TimeoutException:
											self.__logger.error('Waited too long for link')

										link = links[items.index(item)]
										video_src = self.__download_video(filename, link.get_attribute('href'), folder)
										self.__vdm.add_row(
											{
												"title": item,
												"video_path": os.path.join(folder,
												                           filename + '-' +
												                           video_src.split("/")[
													                           -1].strip())
											},
											letter=current_letter
										)
										self.__logger.info('%s videos remaining (%s / %s)' % (
											self.__logger.yellow(len(links) - (items.index(item) + 1)),
											self.__logger.blue(items.index(item) + 1),
											self.__logger.blue(len(links)),
										))


							except exceptions.NoSuchElementException:
								self.__logger.error('Video tab links couldn\'t be found')
							except exceptions.TimeoutException:
								self.__logger.error('Waited too long for element')

							self.__chrome_driver.close()
							self.__chrome_driver.switch_to.window(TABS['DEFAULT'])

						self.__logger.log(self.__logger.green('Successfully downloaded all videos'))
						self.__logger.log('Alphabet is ready')

				except exceptions.NoSuchElementException:
					self.__logger.error('No such element %s' % (self.__HANDLES["letter_buttons"]["handle"]))
				except exceptions.TimeoutException:
					self.__logger.error('Waited too long for element')
			finally:
				self.__chrome_driver.quit()
				self.__logger.log(self.__logger.green('All videos has been successfully downloaded'))

	def __download_video(self,filename: str, url: str, folder: str):
		video_src = ''
		try:
			videos_folder = self.__CONFIG.get(self.__SECTIONS['video'], 'output_folder')

			if not os.path.isdir(videos_folder):
				self.__logger.log('Created %s folder' % (videos_folder))
				os.mkdir(videos_folder)

			if not os.path.isdir(folder):
				self.__logger.log('Created %s folder' % (folder))
				os.mkdir(folder)

			headers = {"Referer": url}
			soup = BeautifulSoup(requests.get(url).content, "html.parser")
			for v in soup.select("video source[src]"):
				video_src = v['src']
				self.__logger.log('Downloading video %s %s' % (self.__logger.yellow(filename), format(v["src"])))
				with open(os.path.join(folder, filename + '-' + v["src"].split("/")[-1].strip()), "wb") as f_out:
					f_out.write(requests.get(v["src"].strip(), headers=headers).content)
		except requests.exceptions.ConnectionError as e:
			self.__logger.error('Requests error - %s' % (e))
		except requests.exceptions.Timeout as e:
			self.__logger.error('Requests error - %s' % (e))
		except requests.exceptions.RequestException as e:
			self.__logger.error('Requests error - %s' % (e))
		finally:
			self.__logger.log('Downloaded')
			return video_src

	def __accept_consent(self):
		try:
			self.__logger.log('Accepting consent if available')
			WebDriverWait(self.__chrome_driver, 10).until(
				EC.presence_of_element_located(
					(self.__HANDLES["consent"]["type"], self.__HANDLES["consent"]["handle"]))
			)

			consent_btn = self.__chrome_driver.find_element(self.__HANDLES["consent"]["type"],
			                                              self.__HANDLES["consent"]["handle"])
			if consent_btn: consent_btn.click()
		except exceptions.NoSuchElementException:
			self.__logger.log('Consent not available')

	def get_filename(self, name):
		return name.strip().replace(' ', '-').replace('/', '-')