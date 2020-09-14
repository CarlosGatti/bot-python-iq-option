from bs4 import BeautifulSoup
import requests

headers = requests.utils.default_headers()
headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0'})

data = requests.get('http://br.investing.com/economic-calendar/', headers=headers)

resultados = []

if data.status_code == requests.codes.ok:
	info = BeautifulSoup(data.text, 'html.parser')
	
	blocos = ((info.find('table', {'id': 'economicCalendarData'})).find('tbody')).findAll('tr', {'class': 'js-event-item'})
	
	for blocos2 in blocos:
		impacto = str((blocos2.find('td', {'class': 'sentiment'})).get('data-img_key')).replace('bull', '')
		horario = str(blocos2.get('data-event-datetime')).replace('/', '-')
		moeda = (blocos2.find('td', {'class': 'left flagCur noWrap'})).text.strip()
		
		resultados.append({'par': moeda, 'horario': horario, 'impacto': impacto})
		

for info in resultados:
	print('PARIDADE: ', info['par'],'\n HORARIO: ', info['horario'], '\n IMPACTO: ', info['impacto'], '\n--------\n')

#print(resultados)