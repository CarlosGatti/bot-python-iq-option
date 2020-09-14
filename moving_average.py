from iqoptionapi.stable_api import IQ_Option
import logging, json, sys, time, configparser
from talib.abstract import *
import numpy as np


logging.disable(level=(logging.DEBUG))

arquivo_user = configparser.RawConfigParser()
arquivo_user.read('config_user.txt')	
API = IQ_Option(arquivo_user.get('USER', 'user'), arquivo_user.get('USER', 'password'))
API.connect()

API.change_balance('PRACTICE') # PRACTICE / REAL

if API.check_connect():
	print('\n\nConectado com sucesso')
else:
	print('\n Erro ao se conectar')
	sys.exit()


par = 'EURUSD'
periodo = 14
tempo_segundos = 60

API.start_candles_stream(par, tempo_segundos, 280)
while True:
	velas = API.get_realtime_candles(par, tempo_segundos)
	
	valores = {'open': np.array([]), 'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'volume': np.array([]) }
	
	
	for x in velas:
		valores['open'] = np.append(valores['open'], velas[x]['open'])
		valores['high'] = np.append(valores['open'], velas[x]['max'])
		valores['low'] = np.append(valores['open'], velas[x]['min'])
		valores['close'] = np.append(valores['open'], velas[x]['close'])
		valores['volume'] = np.append(valores['open'], velas[x]['volume'])
	
	
	calculo_sma = SMA(valores, timeperiod=periodo)
	print(calculo_sma)
	sys.exit()
	print(calculo_sma[-1])
	time.sleep(1)