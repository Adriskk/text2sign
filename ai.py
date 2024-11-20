import configparser
import os
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, InputExample, util
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer
from log import Logger

logger = Logger()

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')
CSV_SAVE_PATH = CONFIG.get('CSV', 'save_file_path')
CSV_SAVE_FILENAME = CONFIG.get('CSV', 'save_file_name') + '.csv'
MODEL_SAVE_PATH = CONFIG.get('MODEL', 'save_path')
TITLES_SAVE_PATHNAME = CONFIG.get('MODEL', 'titles_dict_save_pathname')

asl_prompt = "For given sentence - '%s' convert it to ASL language and return output that includes ONLY CLEAN ASL LANGUAGE WITHOUT OTHER UNNECESSARY INFO in JSON format: {asl: 'sentence converted to asl'}"


def get_prompt(input: str) -> str:
	return asl_prompt.replace('%s', input)


def remove_brackets(title: str) -> str:
	start_index = title.find('(')
	if start_index != -1:
		return title[:start_index]
	return title


def load_titles_from_csv(csv_folder_path):
	logger.log('Loading data from .csv files...')
	titles_dict = {}
	letter_dirs = os.listdir(csv_folder_path)

	for letter in letter_dirs:
		letter = letter.upper()
		df = pd.read_csv(os.path.join(csv_folder_path, letter, CSV_SAVE_FILENAME))
		for _, row in df.iterrows():
			title = remove_brackets(row['title'])
			video_path = row.get('video_path', None)

			main_word = title.split()[0].strip().upper()
			if main_word not in titles_dict:
				titles_dict[main_word] = []

			titles_dict[main_word].append({
				"title": title,
				"video_path": video_path
			})

	logger.log('Loaded')
	return titles_dict


def prepare_training_data(titles_dict):
	logger.log('Preparing training data')
	examples = []
	for main_word, title_entries in titles_dict.items():
		logger.log('Creating InputExample objects for %s' % logger.green(main_word))
		for i, title_entry in enumerate(title_entries):
			positive_example = InputExample(texts=[main_word, remove_brackets(title_entry["title"])])
			examples.append(positive_example)

			if len(title_entries) > 1:
				negative_example = remove_brackets(title_entries[(i + 1) % len(title_entries)]["title"])
				triplet_example = InputExample(texts=[main_word, remove_brackets(title_entry["title"]), negative_example])
				examples.append(triplet_example)

	logger.log('Prepared')
	return examples


def train_model(training_examples):
	logger.log('Attempting to create & train model using training examples')
	filtered_examples = [example for example in training_examples if example is not None]
	if len(filtered_examples) == 0:
		raise ValueError("No valid training examples after filtering.")

	model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
	tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
	logger.log('Created model and tokenizer')

	logger.log('Training model...')
	embeddings = []
	for example in filtered_examples:
		embeddings.append(model.encode(remove_brackets(example.texts[1])))  # For simplicity, we take the second text (title)

	logger.log('Trained, saving model and tokenizer...')
	model.save_pretrained(MODEL_SAVE_PATH)
	tokenizer.save_pretrained(MODEL_SAVE_PATH)
	logger.log('Saved')
	return model


def find_best_title(asl_sentence, titles_dict, model):
	logger.log('Attempting to find best words corresponding to passed ASL sentence')
	asl_embedding = model.encode(asl_sentence)

	def replacers(word: str) -> str:
		if word == "I": return "ME"
		return word

	result = {"used_words": []}
	words = list(map(replacers, asl_sentence.split()))

	for word in words:
		best_match = None
		max_similarity = -1

		if word in titles_dict:
			for title_entry in titles_dict[word]:
				title_embedding = model.encode(remove_brackets(title_entry["title"]))  # Direct embedding
				similarity = util.cos_sim(asl_embedding, title_embedding).item()

				if similarity > max_similarity:
					max_similarity = similarity
					best_match = title_entry

			if best_match:
				result["used_words"].append({
					"word": word,
					"title": best_match["title"],
					"video_path": best_match["video_path"]
				})
		else:
			result["used_words"].append({
				"word": word,
				"title": "- No title found -",
				"video_path": None
			})

	return result


def get_preprocessed_video_data(asl: str):
	model = model = SentenceTransformer(MODEL_SAVE_PATH)
	titles_dict = load_titles_from_csv(CSV_SAVE_PATH)
	return find_best_title(asl_sentence=asl, titles_dict=titles_dict, model=model)


def setup_model():
	model_path = os.path.join(MODEL_SAVE_PATH, 'model.safetensors')
	tokenizer_path = os.path.join(MODEL_SAVE_PATH, 'tokenizer.json')

	if not os.path.isfile(model_path) and not os.path.isfile(tokenizer_path):
		logger.info('Training SentenceTransformer model')
		titles_dict = load_titles_from_csv(CSV_SAVE_PATH)
		training_examples = prepare_training_data(titles_dict)
		train_model(training_examples)
		return

	logger.info("Model is already trained and saved")