from iqoptionapi.stable_api import IQ_Option
import time, configparser

arquivo_user = configparser.RawConfigParser()
arquivo_user.read('config_user.txt')	
API = IQ_Option(arquivo_user.get('USER', 'user'), arquivo_user.get('USER', 'password'))
API.connect()

API.change_balance('PRACTICE') # PRACTICE / REAL

if API.check_connect():
	print(' Conectado com sucesso!')
else:
	print(' Erro ao conectar')
	input('\n\n Aperte enter para sair')
	sys.exit()

def best_payout(par, timeframe = 1):
	par = par.upper()
	
	tb = API.get_all_profit()
	
	API.subscribe_strike_list(par, timeframe)
	tentativas = 0
	while True:
		d = API.get_digital_current_profit(par, timeframe)
		
		if d != False:
			d = int(d)
			break
		time.sleep(1)
		
		if tentativas == 5:
			print('Não foi possivel capturar o payout')
			d = 0
			break
		tentativas += 1
	API.unsubscribe_strike_list(par, timeframe)
	
	payout = {'binario': 0, 'digital': d}
	payout['binario'] = int(100 * tb[par]['turbo']) if timeframe <= 5 else int(100 * tb[par]['binary'])
	
	
	return 'binario' if payout['binario'] > payout['digital'] else 'digital'

print(best_payout('EURUSD', 5))