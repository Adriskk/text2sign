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

logger = Logger()
vdm = VideoDataManager()

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')
SECTIONS = {"driver": "DRIVER", "video": 'VIDEO'}

CHROME_DRIVER_PATH = CONFIG.get(SECTIONS["driver"], 'driver_rel_path')
START_URL = CONFIG.get(SECTIONS['driver'], 'driver_scraping_start_url')

options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
options.enable_downloads = True
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")


def download_video(filename: str, url: str, folder: str):
	videos_folder = CONFIG.get(SECTIONS['video'], 'output_folder')

	if not os.path.isdir(videos_folder):
		logger.log('Created %s folder' % (videos_folder))
		os.mkdir(videos_folder)

	if not os.path.isdir(folder):
		logger.log('Created %s folder' % (folder))
		os.mkdir(folder)

	headers = {"Referer": url}

	soup = BeautifulSoup(requests.get(url).content, "html.parser")
	for v in soup.select("video source[src]"):
		logger.log('Downloading video %s %s' % (logger.yellow(filename), format(v["src"])))
		with open(folder + '/' + filename + '-' + v["src"].split("/")[-1].strip(), "wb") as f_out:
			f_out.write(requests.get(v["src"].strip(), headers=headers).content)
	logger.log('Downloaded')


# Starting scraping data.
with webdriver.Chrome(keep_alive=True) as chrome_driver:
	try:
		logger.log('Created driver instance')
		chrome_driver.get(START_URL)

		logger.log('Opening url in chrome browser')
		chrome_driver.maximize_window()
		TABS = {"DEFAULT": chrome_driver.current_window_handle}

		HANDLES = {
			"letter_buttons": {"type": By.CSS_SELECTOR, "handle": ".wlbutton"},
			"consent": {"type": By.CSS_SELECTOR, "handle": ".fc-cta-consent"},
			"video_tabs_list_items": {"type": By.CSS_SELECTOR, "handle": ".search_results ul li"},
			"video_tabs_list_items_link": {"type": By.CSS_SELECTOR, "handle": ".search_results ul li a"},
			"source": {"type": By.CSS_SELECTOR, "handle": ".videocontent video source"},
		}

		try:
			try:
				# Accept consent.
				logger.log('Accepting consent if available')
				WebDriverWait(chrome_driver, 10).until(
					EC.presence_of_element_located(
						(HANDLES["consent"]["type"], HANDLES["consent"]["handle"]))
				)

				consent_btn = chrome_driver.find_element(HANDLES["consent"]["type"], HANDLES["consent"]["handle"])
				if consent_btn: consent_btn.click()
			except:
				logger.log('Consent not available')

			# Find alphabet buttons
			logger.log('Waiting for letter buttons to be visible...')
			WebDriverWait(chrome_driver, 10).until(
				EC.presence_of_element_located(
					(HANDLES["letter_buttons"]["type"], HANDLES["letter_buttons"]["handle"]))
			)

			HREFS = []
			logger.log('Found letter buttons')
			alphabet_btns = chrome_driver.find_elements(HANDLES["letter_buttons"]["type"],
			                                            HANDLES["letter_buttons"]["handle"])
			logger.log('Scraping aplhabet urls...')
			if alphabet_btns:
				for btn in alphabet_btns:
					HREFS.append(btn.get_attribute('href'))
				logger.log('Finished')

				# Opening tab for every letter and scraping video tab links
				logger.log('Going through every scraped url...')
				for href in HREFS:
					logger.log('Current URL - %s' % (logger.green(href)))
					chrome_driver.execute_script('window.open('');')

					current_letter = href.split('/')[-1]
					vdm.add_letter(current_letter)

					for handle in chrome_driver.window_handles:
						if handle not in TABS.values():
							# Save tab
							logger.log('Saving newly created tab - %s' % (handle))
							TABS[href] = handle
							break

					# Switch to newly created tab
					logger.log('Switching to %s tab and loading %s url' % (logger.green(TABS[href]), href))
					chrome_driver.switch_to.window(TABS[href])
					chrome_driver.get(href)

					# Get list of all video tab links
					try:
						logger.log('Waiting for video tabs items to be visible...')
						WebDriverWait(chrome_driver, 16).until(
							EC.presence_of_element_located(
								(HANDLES["video_tabs_list_items"]["type"],
								 HANDLES["video_tabs_list_items"]["handle"]))
						)

						logger.log('Found video tabs items')
						items = chrome_driver.find_elements(HANDLES["video_tabs_list_items"]["type"],
						                                    HANDLES["video_tabs_list_items"]["handle"])
						if items:
							items = [item.text for item in items]

							# Open each video tab
							for item in items:
								folder = CONFIG.get(SECTIONS['video'], 'output_folder') + current_letter
								filename = item.strip().replace(' ', '-').replace('/', '-')

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
										logger.info('Video %s already exists, skipping to next' % (filename))
										if not vdm.value_exists(item):
											vdm.add_row(
												{
													"title": item,
													"vide_path": existing_file
												}
											)

										continue

								chrome_driver.implicitly_wait(2)

								try:
									WebDriverWait(chrome_driver, 16).until(
										EC.presence_of_element_located(
											(HANDLES["video_tabs_list_items_link"]["type"],
											 HANDLES["video_tabs_list_items_link"]["handle"]))
									)

									links = chrome_driver.find_elements(
										HANDLES["video_tabs_list_items_link"]["type"],
										HANDLES["video_tabs_list_items_link"]["handle"])

									logger.log('Opening video tab - %s' % (logger.blue(item)))
									links[items.index(item)].click()

								except exceptions.NoSuchElementException:
									logger.error('Item video link was not found')
									continue
								except exceptions.TimeoutException:
									logger.error('Waited too long for link')

								logger.log('Waiting for video element to load...')
								WebDriverWait(chrome_driver, 20).until(
									EC.presence_of_element_located(
										(HANDLES["source"]["type"],
										 HANDLES["source"]["handle"]))
								)

								logger.log('Video element loaded')
								video = chrome_driver.find_element(HANDLES["source"]["type"],
								                                   HANDLES["source"]["handle"])

								if video:
									video_src = video.get_attribute('src')
									logger.log('Current video src - %s' % (video_src))

									vdm.add_row(
									{
											"title": item,
											"video_path": folder + '/' + filename + '-' + video_src.split("/")[-1].strip()
										},
										letter=current_letter
									)

									download_video(filename, chrome_driver.current_url, folder)
									chrome_driver.implicitly_wait(1)
									chrome_driver.back()
									logger.log('Going back')
								else:
									logger.error('Video element not found')

					except exceptions.NoSuchElementException:
						logger.error('Video tab links couldn\'t be found')
					except exceptions.TimeoutException:
						logger.error('Waited too long for element')

					chrome_driver.close()
					chrome_driver.switch_to.window(TABS['DEFAULT'])

		except exceptions.NoSuchElementException:
			logger.error('No such element %s' % (HANDLES["letter_buttons"]["handle"]))
		except exceptions.TimeoutException:
			logger.error('Waited too long for element')
	finally:
		chrome_driver.quit()
