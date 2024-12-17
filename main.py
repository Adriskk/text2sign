import configparser
import json
from dotenv import load_dotenv
import openai
import os
import ffmpeg

from setup import Setup
from log import Logger
from ai import get_prompt, get_preprocessed_video_data, setup_model
from window import open_window
from plots import display_chart
from lib import get_merged_video_filename

logger = Logger()

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

CSV_SAVE_PATH = CONFIG.get('CSV', 'save_file_path')
CSV_SAVE_FILENAME = CONFIG.get('CSV', 'save_file_name') + '.csv'
MERGED_VIDEO_OUTPUT_FOLDER = CONFIG.get('VIDEO', 'merged_video_output_folder')
DOWNLOADED_ALL = bool(int(CONFIG.get('VIDEO', 'downloaded_all'))) | False

client = openai.OpenAI(api_key=OPENAI_API_KEY)


def merge_videos_with_ffmpeg(video_clips, merged_video_pathname):
    try:
        file_list_path = os.path.join(MERGED_VIDEO_OUTPUT_FOLDER, 'file_list.txt')
        with open(file_list_path, 'w') as f:
            for clip in video_clips:
                full_clip_path = os.path.abspath(clip)
                f.write(f"file '{full_clip_path}'\n")
                logger.log(f"Writing to file_list.txt: file '{full_clip_path}'")

        ffmpeg.input(file_list_path, format='concat', safe=0, r=30, vsync=2).output(
            merged_video_pathname,
            vcodec='libx264',
            acodec='aac',
            crf=23,
            filter_complex='scale=1280:720'
        ).run()

        logger.log(logger.green(f"Videos merged successfully: {merged_video_pathname}"))
        os.remove(file_list_path)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode('utf-8') if e.stderr else "No stderr output"
        print(f"FFmpeg error: {error_message}")
        print(f"FFmpeg stdout: {e.stdout.decode('utf-8') if e.stdout else 'No stdout output'}")
        raise


def generate_asl(sentence: str):
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
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=get_prompt(sentence),
    )

    logger.info('Sending request...')
    client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        response_format={"type": "json_object"}
    )

    logger.log('Received response from OpenAI')
    all_messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    response = all_messages.to_dict()['data'][0]['content'][0]['text']['value']
    return json.loads(response)


if __name__ == '__main__':
    logger.info('Program has started')

    if not DOWNLOADED_ALL:
        # Scrape word videos
        logger.info('Starting video download procedure...')
        setup = Setup()
        setup.scrape()
    else:
        logger.info('All videos are downloaded')

    display_chart()
    setup_model()

    def on_generate(sentence: str):
        filename = get_merged_video_filename(sentence) + '.mp4'
        path = os.path.join(MERGED_VIDEO_OUTPUT_FOLDER, filename)

        if os.path.isfile(path):
            logger.info('Video already generated, it is available at %s' % logger.green(path))
            return path

        logger.log('Generating ASL language for given input: %s' % logger.yellow(sentence))

        try:
            result = generate_asl(sentence)
            logger.log('Generated ASL sentence - %s' % logger.yellow(result['asl']))

            result = get_preprocessed_video_data(asl=result['asl'].upper())
            logger.log(logger.green('Found best videos representing each ASL word!'))

            logger.log('Received result - %s' % logger.yellow(result))
            for row in result['used_words']:
                logger.log('asl: %s \t\ttitle: %s \t\tvideo: %s' % (
                    logger.yellow(row['word']), row['title'], logger.green(row['video_path'])))

            logger.info('Concatenating videos')
            video_clips = [used_word['video_path'] for used_word in result['used_words'] if used_word['video_path']]

            merged_video_pathname = os.path.join(
                MERGED_VIDEO_OUTPUT_FOLDER, get_merged_video_filename(sentence=sentence)) + '.mp4'

            if not os.path.isdir(MERGED_VIDEO_OUTPUT_FOLDER):
                os.mkdir(MERGED_VIDEO_OUTPUT_FOLDER)

            merge_videos_with_ffmpeg(video_clips, merged_video_pathname)

            return merged_video_pathname
        except openai.BadRequestError as e:
            logger.error(e)

    open_window(on_generate)
