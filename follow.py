from datetime import datetime, date, timedelta
from dateutil import tz
import sys
from iqoptionapi.stable_api import IQ_Option
import time, json, logging, configparser
from datetime import datetime, date, timedelta
from dateutil import tz
import sys

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
	 
def entradas(config, entrada, direcao, timeframe):
	status,id = API.buy_digital_spot(config['paridade'], entrada, direcao, timeframe)

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

# Carrega as configuracoes
config = configuracao()
config['banca_inicial'] = banca()


# Filtros
# 1? Filtro por valor da entrada copiada
# 2? Filtro para copiar entrada dos top X 
# 3? Filtro Pais

# Captura os dados necessarios do ranking
def filtro_ranking(config):
	
	user_id = []
	
	try:
		ranking = API.get_leader_board('Worldwide' if config['filtro_pais'] == 'todos' else config['filtro_pais'].upper() , 1, int(config['filtro_top_traders']), 0)
	
		if int(config['filtro_top_traders']) != 0:
			for n in ranking['result']['positional']:
				id = ranking['result']['positional'][n]['user_id']
				user_id.append(id)				
	except:
		pass
		
	return user_id

filtro_top_traders = filtro_ranking(config)

if config['seguir_ids'] != '':
	if ',' in config['seguir_ids']:
		x = config['seguir_ids'].split(',')
		for old in x:
			filtro_top_traders.append(int(old))
	else:
		filtro_top_traders.append(int(config['seguir_ids']))


tipo = 'live-deal-digital-option' # live-deal-binary-option-placed
timeframe = 'PT'+config['timeframe']+'M' # PT5M / PT15M
old = 0

# Captura o Payout
config['payout'] = float(payout(config['paridade'], 'digital', int(config['timeframe'])) / 100)

API.subscribe_live_deal(tipo, config['paridade'], timeframe, 10)

while True:
	trades = API.get_live_deal(tipo, config['paridade'], timeframe)
	
	if len(trades) > 0 and old != trades[0]['user_id'] and trades[0]['amount_enrolled'] >= float(config['valor_minimo']):
		ok = True
		
		# Correcao de bug em relacao ao retorno de datas errado
		res = round( time.time() - datetime.timestamp( timestamp_converter(trades[0]['created_at'] / 1000, 2) ), 2)
		ok = True if res <= int(config['filtro_diferenca_sinal']) else False
		
		if len(filtro_top_traders) > 0:
			if trades[0]['user_id'] not in filtro_top_traders:
				ok = False
		
		if ok:
			# Dados sinal
			print(res, end='')
			print(' [',trades[0]['flag'],']',config['paridade'],'/',trades[0]['amount_enrolled'],'/',trades[0]['instrument_dir'],'/',trades[0]['name'],trades[0]['user_id'])
			
			# 1 entrada
			resultado,lucro,stop = entradas(config, config['valor_entrada'], trades[0]['instrument_dir'], int(config['timeframe']))
			print('   -> ',resultado,'/',lucro,'\n\n')

			if stop:
				print('\n\nStop',resultado.upper(),'batido!')
				sys.exit()
		
			
			# Martingale
			if resultado == 'loss' and config['martingale'] == 'S':
				valor_entrada = martingale('auto', float(config['valor_entrada']), float(config['payout']))
				for i in range(int(config['niveis']) if int(config['niveis']) > 0 else 1):
					
					print('   MARTINGALE NIVEL '+str(i+1)+'..', end='')
					resultado,lucro,stop = entradas(config, valor_entrada, trades[0]['instrument_dir'], int(config['timeframe']))
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
					for i in range(int(config['niveis']) if int(config['niveis']) > 0 else 1):
						
						# Mao
						for i2 in range(2):
						
							if lucro_total >= perca:
								break
						
							print('   SOROSGALE NIVEL '+str(i+1)+' | MAO '+str(i2+1)+' | ', end='')
							
							# Entrada
							resultado,lucro,stop = entradas(config, (perca / 2)+lucro, trades[0]['instrument_dir'], int(config['timeframe']))							
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
			

		old = trades[0]['user_id']
	time.sleep(0.2)

API.unscribe_live_deal(tipo, config['paridade'], timeframe)