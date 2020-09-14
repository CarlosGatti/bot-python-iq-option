import json
import requests
from time import sleep
from threading import Thread, Lock

global config
config = {'url': 'https://...............', 'lock': Lock(), 'url_file': 'https://...............'}

def del_update(data):
	global config	
	
	config['lock'].acquire()
	requests.post(config['url'] + 'getUpdates', {'offset': data['update_id']+1})
	config['lock'].release()

def send_message(data, msg):
	global config
	
	config['lock'].acquire()
	requests.post(config['url'] + 'sendMessage', {'chat_id': data['message']['chat']['id'], 'text': str(msg)})
	config['lock'].release()

def get_file(file_path):
	global config
	
	return requests.get(config['url_file'] + str(file_path)).content

def upload_file(data, file):
	global config	
	
	formatos = {'png': {'metodo': 'sendPhoto', 'send': 'photo'},
				'text': {'metodo': 'sendDocument', 'send': 'document'} }
	
	return requests.post(config['url'] + formatos['text' if '.txt' in file else 'png']['metodo'], {'chat_id': data['message']['chat']['id']}, files={formatos['text' if '.txt' in file else 'png']['send']: open(file, 'rb')}).text

while True:
	x = ''
	while 'result' not in x:
		try:
			x = json.loads(requests.get(config['url'] + 'getUpdates').text)
		except Exception as e:
			x = ''
			if 'Failed to establish a new connection' in str(e):
				print('Perca de conexão')
			else:
				print('Erro desconhecido: ' + str(e))
	
	
	if len(x['result']) > 0:
		for data in x['result']:
			Thread(target=del_update, args=(data, )).start()
					
			if 'document' in data['message']:
			
				print(json.dumps(data['message'], indent=1))
				
				file = get_file(json.loads(requests.post(config['url'] + 'getFile?file_id=' + data['message']['document']['file_id']).text)['result']['file_path'])
				open(data['message']['document']['file_name'], 'wb').write(file)
			
			elif data['message']['text'] == 'Kyra':
				print(upload_file(data, 'kyra.jpg'))

			elif data['message']['text'] == 'Sinais':
				print(upload_file(data, 'sinais.txt'))	
					
			elif data['message']['text'] == 'Gatti':
				print(upload_file(data, 'documento_exemplo.txt'))						
			else:			
			
				print(json.dumps(data, indent=1))
				if data['message']['text'] == 'oi':
					Thread(target=send_message, args=(data, 'Olá, tudo bem?')).start()	
		sleep(1.5)