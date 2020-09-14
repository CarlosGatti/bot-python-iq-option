from iqoptionapi.stable_api import IQ_Option
import time, json, logging, configparser

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
timeframe = 5

velas = API.get_candles(par, (int(timeframe) * 60), 20,  time.time())

ultimo = round(velas[0]['close'], 4)
primeiro = round(velas[-1]['close'], 4)

diferenca = abs( round( ( (ultimo - primeiro) / primeiro ) * 100, 3) )
tendencia = "CALL" if ultimo < primeiro and diferenca > 0.01 else "PUT" if ultimo > primeiro and diferenca > 0.01 else False
 
print(tendencia)