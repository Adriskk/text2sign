import configparser
import json

from dotenv import load_dotenv
import openai
import os
import subprocess
from moviepy.editor import VideoFileClip, concatenate_videoclips

from setup import Setup
from log import Logger
from ai import get_prompt, get_preprocessed_video_data, setup_model

logger = Logger()

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')
CSV_SAVE_PATH = CONFIG.get('CSV', 'save_file_path')
CSV_SAVE_FILENAME = CONFIG.get('CSV', 'save_file_name') + '.csv'
MERGED_VIDEO_OUTPUT_FOLDER = CONFIG.get('VIDEO', 'merged_video_output_folder')

client = openai.OpenAI(api_key=OPENAI_API_KEY)
# os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


def get_merged_video_filename(sentence: str) -> str:
	return '_'.join(sentence.split(' '))


if __name__ == '__main__':
	logger.info('Program has started')

	# Scrape word videos
	# setup = Setup()
	# setup.scrape()

	setup_model()

	sentence = input("Enter your sentence: ").strip().upper()

	filename = get_merged_video_filename(sentence) + '.mp4'
	path = os.path.join(MERGED_VIDEO_OUTPUT_FOLDER, filename)

	if os.path.isfile(path):
		logger.info('Video already generated, it is available at %s' % logger.green(path))
		subprocess.run(['open', path])
		exit()

	logger.log('Generating ASL language for given input: %s' % logger.yellow(sentence))

	try:
		if CONFIG.has_section('OPENAI') and CONFIG.has_option('OPENAI', 'assistant_id'):
			assistant_id = CONFIG.get('OPENAI', 'assistant_id')
			logger.info('Retrieving assistant by id saved in config - %s' % assistant_id)
			assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
		else:
			logger.info('Creating assistant...')
			assistant = client.beta.assistants.create(
				name="Sign Language Translator",
				model="gpt-4o",
			)

			CONFIG.set('OPENAI', 'assistant_id', assistant.id)
			with open('config.ini', 'w') as config_file:
				CONFIG.write(config_file)

		logger.info('Creating thread...')
		thread = client.beta.threads.create()

		logger.info('Preparing request...')
		message = client.beta.threads.messages.create(
			thread_id=thread.id,
			role="user",
			content=get_prompt(sentence),
		)

		logger.info('Sending request...')
		run = client.beta.threads.runs.create_and_poll(
			thread_id=thread.id,
			assistant_id=assistant.id,
			response_format={"type": "json_object"}
		)

		logger.log('Received response from OpenAI')
		all_messages = client.beta.threads.messages.list(
			thread_id=thread.id
		)

		response = all_messages.to_dict()['data'][0]['content'][0]['text']['value']
		result = json.loads(response)
		logger.log('Generated ASL sentence - %s' % logger.yellow(result['asl']))

		result = get_preprocessed_video_data(asl=result['asl'].upper())
		logger.log(logger.green('Found best videos representing each ASL word!'))

		logger.log('Received result - %s' % logger.yellow(result))
		for row in result['used_words']:
			print('asl: %s \ttitle: %s \tvideo: %s' % (logger.yellow(row['word']), row['title'], logger.green(row['video_path'])))

		logger.info('Concatenating videos')
		video_clips = []
		for used_word in result['used_words']:
			if used_word['video_path']:
				video_clips.append(VideoFileClip(used_word['video_path']))
				logger.log('Concatenated %s' % used_word['word'])

		final_clip = concatenate_videoclips(video_clips)
		logger.log('Created one video from clips')

		merged_video_pathname = os.path.join(MERGED_VIDEO_OUTPUT_FOLDER, get_merged_video_filename(sentence=sentence)) + '.mp4'
		if not os.path.isdir(MERGED_VIDEO_OUTPUT_FOLDER):
			os.mkdir(MERGED_VIDEO_OUTPUT_FOLDER)

		final_clip.write_videofile(merged_video_pathname)
		logger.log('Saved merged video in %s directory - %s' % (logger.green(MERGED_VIDEO_OUTPUT_FOLDER), logger.green(merged_video_pathname)))
		subprocess.run(['open', merged_video_pathname])
	except openai.BadRequestError as e:
		logger.error(e)
