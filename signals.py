from iqoptionapi.stable_api import IQ_Option
import time, json, logging, configparser
from datetime import datetime, date, timedelta
from dateutil import tz
import sys
from esqueleto import Esqueleto
import pandas as pd
logging.disable(level=(logging.DEBUG))

arquivo_user = configparser.RawConfigParser()
arquivo_user.read('config_user.txt')	
API = IQ_Option(arquivo_user.get('USER', 'user'), arquivo_user.get('USER', 'password'))
API.connect()

API.change_balance('PRACTICE') # PRACTICE / REAL

while True:
	if API.check_connect() == False:
		print('Erro ao se conectar')
		
		API.connect()
	else:
		print('\n\nConectado com sucesso')
		break
	
	time.sleep(1)

def perfil():
	perfil = json.loads(json.dumps(API.get_profile_ansyc()))
	
	return perfil
	
	'''
		name
		first_name
		last_name
		email
		city
		nickname
		currency
		currency_char 
		address
		created
		postal_index
		gender
		birthdate
		balance		
	'''

def timestamp_converter(x, retorno = 1):
	hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
	hora = hora.replace(tzinfo=tz.gettz('GMT'))
	
	return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6] if retorno == 1 else hora.astimezone(tz.gettz('America/Sao Paulo'))

def banca():
	return API.get_balance()

def payout(par, tipo, timeframe = 1):
	if tipo == 'turbo':
		a = API.get_all_profit()
		return int(100 * a[par]['turbo'])
		
	elif tipo == 'digital':
	
		API.subscribe_strike_list(par, timeframe)
		while True:
			d = API.get_digital_current_profit(par, timeframe)
			if d != False:
				d = int(d)
				break
			time.sleep(1)
		API.unsubscribe_strike_list(par, timeframe)
		return d

def configuracao():
	arquivo = configparser.RawConfigParser()
	arquivo.read('config.txt')	
		
	return {'seguir_ids': arquivo.get('GERAL', 'seguir_ids'),'stop_win': arquivo.get('GERAL', 'stop_win'), 'stop_loss': arquivo.get('GERAL', 'stop_loss'), 'payout': 0, 'banca_inicial': banca(), 'filtro_diferenca_sinal': arquivo.get('GERAL', 'filtro_diferenca_sinal'), 'martingale': arquivo.get('GERAL', 'martingale'), 'sorosgale': arquivo.get('GERAL', 'sorosgale'), 'niveis': arquivo.get('GERAL', 'niveis'), 'filtro_pais': arquivo.get('GERAL', 'filtro_pais'), 'filtro_top_traders': arquivo.get('GERAL', 'filtro_top_traders'), 'valor_minimo': arquivo.get('GERAL', 'valor_minimo'), 'paridade': arquivo.get('GERAL', 'paridade'), 'valor_entrada': arquivo.get('GERAL', 'valor_entrada'), 'timeframe': arquivo.get('GERAL', 'timeframe')}

def martingale(tipo, valor, payout):

	if tipo == 'simples':
		return valor * 2.2
	else:
		lucro_esperado = float(valor) * float(payout)
		perca = valor
		while True:
			if round(float(valor) * float(payout), 2) > round(float(abs(perca)) + float(lucro_esperado), 2):
				return round(valor, 2)
				break
			valor += 0.01
	 
def entradas(config, paridade, entrada, direcao, timeframe):
	status,id = API.buy_digital_spot(paridade, entrada, direcao, timeframe)

	if status:
		# STOP WIN/STOP LOSS
		banca_att = banca()
		stop_loss = False
		stop_win = False

		if round((banca_att - float(config['banca_inicial'])), 2) <= (abs(float(config['stop_loss'])) * -1.0):
			stop_loss = True
			
		if round((banca_att - float(config['banca_inicial'])) + (float(entrada) * float(config['payout'])) + float(entrada), 2) >= abs(float(config['stop_win'])):
			stop_win = True
		
		while True:
			status,lucro = API.check_win_digital_v2(id)
			
			if status:
				if lucro > 0:		
					return 'win',round(lucro, 2),stop_win
				else:				
					return 'loss',0,stop_loss
				break	
	else:

		return 'error',0,False

config = configuracao()
config['banca_inicial'] = banca()	

def carregar_sinais():
	arquivo = open('sinais.txt', encoding='UTF-8')
	lista = arquivo.read()
	arquivo.close
	
	lista = lista.split('\n')
	
	for index,a in enumerate(lista):
		if a == '':
			del lista[index]
	return lista

def carregar_sinais_pro():
	arquivo = open('sinais.txt', encoding='UTF-8')
	lista = pd.read_csv(arquivo)
	return lista
	
config['payout'] = float(payout(config['paridade'], 'digital', int(config['timeframe'])) / 100)
tipo = 'live-deal-digital-option' # live-deal-binary-option-placed
#lista = carregar_sinais()
lista_sinal = carregar_sinais_pro()	

while True:	
	
	for i in range(len(lista_sinal)):

		data_hora = lista_sinal['data_hora']
		paridade =  lista_sinal['paridade']
		direcao = lista_sinal['direcao']
		timeframe = lista_sinal['timeframe']
		DATA_HORA = datetime.now()
		DATA_HORA_FORMATADA = DATA_HORA.strftime("%Y-%m-%d %H:%M:%S")


		if (DATA_HORA_FORMATADA == data_hora[i]):

			resultado,stop,lucro = entradas(config, paridade[i], config['valor_entrada'], direcao[i], timeframe[i])
			print('   -> ',resultado,'/',lucro,'\n\n')

			if stop:
				print('\n\nStop',resultado.upper(),'batido!')
				sys.exit()
			
			# Martingale
			if resultado == 'loss' and config['martingale'] == 'S':		
				valor_entrada = martingale('auto', float(config['valor_entrada']), float(config['payout']))


				for i in range(int(config['niveis']) if int(config['niveis']) > 0 else 1):
					
					print('   MARTINGALE NIVEL '+str(i+1)+'..', end='')
					resultado,lucro,stop = entradas(config, paridade[i], valor_entrada, direcao[i], timeframe[i])
					print(' ',resultado,'/',lucro,'\n')
					if stop:
						print('\n\nStop',resultado.upper(),'batido!')
						sys.exit()
					
					if resultado == 'win':
						print('\n')
						break
					else:
						valor_entrada = martingale('auto', float(valor_entrada), float(config['payout']))
						
			elif resultado == 'loss' and config['sorosgale'] == 'S': # SorosGale
				
				if float(config['valor_entrada']) > 5:
					
					lucro_total = 0
					lucro = 0
					perca = float(config['valor_entrada']) 
					# Nivel
					for i1 in range(int(config['niveis']) if int(config['niveis']) > 0 else 1):
						
						# Mao
						for i2 in range(2):
						
							if lucro_total >= perca:
								break
						
							print('   SOROSGALE NIVEL '+str(i1+1)+' | MAO '+str(i2+1)+' | ', end='')
							
							# Entrada
							resultado,lucro,stop = entradas(config, paridade[i], (perca / 2)+lucro, direcao[i], timeframe[i])							
							print(resultado,'/',lucro,'\n')	
							if stop:
								print('\n\nStop',resultado.upper(),'batido!')
								sys.exit()
							
							if resultado == 'win':			
								lucro_total += lucro
							else:
								lucro_total = 0
								perca += perca / 2								
								break	

	time.sleep(0.2)
			