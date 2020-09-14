from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
import time, configparser
import sys


def stop(lucro, gain, loss):
	if lucro <= float('-' + str(abs(loss))):
		print('Stop Loss batido!')
		sys.exit()
		
	if lucro >= float(abs(gain)):
		print('Stop Gain Batido!')
		sys.exit()

def Martingale(valor, payout):
	lucro_esperado = valor * payout
	perca = float(valor)	
		
	while True:
		if round(valor * payout, 2) > round(abs(perca) + lucro_esperado, 2):
			return round(valor, 2)
			break
		valor += 0.01

def Payout(par):
	API.subscribe_strike_list(par, 1)
	while True:
		d = API.get_digital_current_profit(par, 1)
		if d != False:
			d = round(int(d) / 100, 2)
			break
		time.sleep(1)
	API.unsubscribe_strike_list(par, 1)
	
	return d

print('''
	     Gatti Trading
 ------------------------------------
''')

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


while True:
	try:
		operacao = int(input('\n Deseja operar na\n  1 - Digital\n  2 - Binaria\n  :: '))
		
		if operacao > 0 and operacao < 3 : break
	except:
		print('\n Opção invalida')

while True:
	try:
		tipo_mhi = int(input(' Deseja operar a favor da\n  1 - Minoria\n  2 - Maioria\n  :: '))
		
		if tipo_mhi > 0 and tipo_mhi < 3 : break
	except:
		print('\n Opção invalida')


par = input(' Indique uma paridade para operar: ').upper()
valor_entrada = float(input(' Indique um valor para entrar: '))
valor_entrada_b = float(valor_entrada)

martingale = int(input(' Indique a quantia de martingales: '))
martingale += 1

stop_loss = float(input(' Indique o valor de Stop Loss: '))
stop_gain = float(input(' Indique o valor de Stop Gain: '))

lucro = 0
payout = Payout(par)
while True:

	minutos = float(((datetime.now()).strftime('%M.%S'))[1:])
	entrar = True if (minutos >= 4.58 and minutos <= 5) or minutos >= 9.58 else False

	print('Hora de entrar?',entrar,'/ Minutos:',minutos)
	
	if entrar:
		print('\n\nIniciando operação!')
		dir = False
		print('Verificando cores..', end='')
		velas = API.get_candles(par, 60, 3, time.time())
		
		velas[0] = 'g' if velas[0]['open'] < velas[0]['close'] else 'r' if velas[0]['open'] > velas[0]['close'] else 'd'
		velas[1] = 'g' if velas[1]['open'] < velas[1]['close'] else 'r' if velas[1]['open'] > velas[1]['close'] else 'd'
		velas[2] = 'g' if velas[2]['open'] < velas[2]['close'] else 'r' if velas[2]['open'] > velas[2]['close'] else 'd'
		
		cores = velas[0] + ' ' + velas[1] + ' ' + velas[2]		
		print(cores)
	
		if cores.count('g') > cores.count('r') and cores.count('d') == 0 : dir = ('put' if tipo_mhi == 1 else 'call')
		if cores.count('r') > cores.count('g') and cores.count('d') == 0 : dir = ('call' if tipo_mhi == 1 else 'put')
		
		if dir:
			print('Direção:',dir)
			
			valor_entrada = valor_entrada_b
			
			for i in range(martingale):
			
				status,id = API.buy_digital_spot(par, valor_entrada, dir, 1) if operacao == 1 else API.buy(valor_entrada, par, dir, 1)
				
				if status:
					while True:
						try:
							status,valor = API.check_win_digital_v2(id) if operacao == 1 else API.check_win_v3(id)
						except:
							status = True
							valor = 0
						
						if status:
							valor = valor if valor > 0 else float('-' + str(abs(valor_entrada)))
							lucro += round(valor, 2)
							
							print('Resultado operação: ', end='')
							print('WIN /' if valor > 0 else 'LOSS /' , round(valor, 2) ,'/', round(lucro, 2),('/ '+str(i)+ ' GALE' if i > 0 else '' ))
							
							valor_entrada = Martingale(valor_entrada, payout)
							
							stop(lucro, stop_gain, stop_loss)
							
							break
						
					if valor > 0 : break
					
				else:
					print('\nERRO AO REALIZAR OPERAÇÃO\n\n')
				
	time.sleep(0.5)