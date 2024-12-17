import random

import matplotlib.pyplot as plt
import os
import configparser
import pandas as pd
import math

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')
CSV_SAVE_PATH = CONFIG.get('CSV', 'save_file_path')
CSV_SAVE_FILENAME = CONFIG.get('CSV', 'save_file_name')


def display_chart():
	fig, ax = plt.subplots()
	data = {"labels": sorted(os.listdir(CSV_SAVE_PATH)), "values": [], "colors": []}

	for letter in data["labels"]:
		path = os.path.join(CSV_SAVE_PATH, letter, CSV_SAVE_FILENAME + '.csv')
		csv = (pd.read_csv(path).to_dict(orient='records'))
		data["values"].append(len(csv))

	all = sum(data["values"])
	r = random.randrange(10, 100, 10) / 100
	g = random.randrange(10, 100, 10) / 100
	b = random.randrange(10, 100, 10) / 100

	for amount in data["values"]:
		opacity = (amount / all) * 10
		opacity = math.floor(opacity) if opacity > 1 else opacity
		print(r, g, b, opacity)
		data["colors"].append((r, g, b, opacity))

	bar_labels = data["labels"]
	bar_container = ax.bar(data["labels"], data["values"], label=bar_labels, color=data["colors"])
	ax.set_ylabel('Amount')
	ax.set_title('Amount of scraped videos for each letter')
	ax.bar_label(bar_container, fmt=lambda x: str(int(x)))

	plt.show()
