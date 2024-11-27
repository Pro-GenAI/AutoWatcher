# Copyright (c) 2024 Praneeth Vadlapati

import os
import time

import base64
from dotenv import load_dotenv
from IPython.display import display, Markdown
import openai

def load_env():
	load_dotenv(override=True)  # bypass the cache and reload the variables
load_env()


def display_md(md_text):
	display(Markdown(md_text))

def print_progress(chr='.'):
	if chr == 0 and type(chr) == int:
		return
	if type(chr) == bool:
		chr = '.' if chr else ','
	print(chr, end='', flush=True)

def print_error(err=None, chr='!'):
	# print(err)
	print_progress(chr)


model = os.getenv('LM_MODEL')
if model:
	model = model.strip()
else:
	raise Exception('LM_MODEL is not set in the environment variables')


client = []
current_client_index = 0
def get_client():
	global client, current_client_index
	if not client or not len(client):
		raise ValueError('No clients available')
	current_client = client[current_client_index]
	current_client_index = (current_client_index + 1) % len(client)
	return current_client
def load_client():
	if len(client):  # if already loaded, and reloading now
		print('Reloading clients...')
	client.clear()
	load_dotenv(override=True)
	base_url = os.getenv('LM_PROVIDER_BASE_URL').strip() or None
	api_key = os.getenv('LM_API_KEY').strip() or None
	client1 = openai.OpenAI(base_url=base_url, api_key=api_key)
	client.append(client1)
	api_key_2 = os.getenv('LM_API_KEY_2') or None
	if api_key_2:
		client2 = openai.OpenAI(base_url=base_url, api_key=api_key_2.strip())
		client.append(client2)
	api_key_3 = os.getenv('LM_API_KEY_3') or None
	if api_key_3:
		client3 = openai.OpenAI(base_url=base_url, api_key=api_key_3.strip())
		client.append(client3)
	api_key_4 = os.getenv('LM_API_KEY_4') or None
	if api_key_4:
		client4 = openai.OpenAI(base_url=base_url, api_key=api_key_4.strip())
		client.append(client4)
load_client()
get_client()  # check errors during import


def encode_image(image_path):
	with open(image_path, 'rb') as image_file:
		return base64.b64encode(image_file.read()).decode('utf-8')

def create_image_b64_url_from_frame(buffer):
	return base64.b64encode(buffer.tobytes()).decode('utf-8')

def load_image(buffer=None, image_path=None):
	image_b64_url = create_image_b64_url_from_frame(buffer) \
     				if buffer is not None else encode_image(image_path)
	return {
		'type': 'image_url',
		'image_url': {
			'url': f'data:image/jpeg;base64,{image_b64_url}'
		}
	}

def user_message(text, role='user', image_path=None, image_frame_buffer=None):
	content = text
	if image_frame_buffer is not None:
		content = [
			load_image(buffer=image_frame_buffer),
			{ 'type': 'text', 'text': text },
		]
	if image_path:
		content = [
			load_image(image_path=image_path),
			{ 'type': 'text', 'text': text },
		]
	return { 'role': role, 'content': content }


def get_lm_response(messages, max_retries=3):
	if isinstance(messages, str):
		messages = [user_message(messages)]
	if not isinstance(messages, list):
		messages = [messages]

	for _ in range(max_retries):
		response = None
		try:
			response = get_client().chat.completions.create(messages=messages, model=model)
			response = response.choices[0].message.content.strip()
			if not response:
				raise Exception('Empty response from the bot')
			return response
		except Exception as e:
			e = str(e)
			if '429' in e or 'Resource has been exhausted' in e:  # Rate limit
				total_wait_time = None
				if 'Please retry after' in e:  # Please retry after X sec
					total_wait_time = e.split('Please retry after')[1].split('sec')[0].strip()
					# print(f'Rate Limit reached. Waiting for {total_wait_time} seconds. ', end='')
					total_wait_time = int(total_wait_time) + 1
				elif 'Please try again in' in e:  # 'Please try again in 23m3s. ...'
					rate_limit_time = e.split('Please try again in')[1].split('.')[0].strip()
					# print(f'Rate Limit reached for {rate_limit_time}. ', end='', flush=True)
	 				# rate_limit_time = '1m20s'
					rate_limit_time_min = 0
					rate_limit_time_sec = 0
					if 'm' in rate_limit_time:
						rate_limit_time_min = rate_limit_time.split('m')[0]
						rate_limit_time = rate_limit_time.split('m')[1]  # get text after 'm'
					if 's' in rate_limit_time:
						rate_limit_time_sec = rate_limit_time.split('s')[0]
					total_wait_time = (int(rate_limit_time_min) * 60) + int(rate_limit_time_sec) + 1
				else:
					total_wait_time = 20
				print_progress(f' RL Wait{total_wait_time}s ')
				time.sleep(int(total_wait_time))
			elif '503' in e:  # Service Unavailable
				print_progress('Unavailable Wait ')
				time.sleep(15)
			elif e == 'Connection error.':
				print_progress('Server not online ')
			else:
				print_progress(f'Error Retrying '+ e)
	raise Exception(f'No response from the bot after {max_retries} retries')
