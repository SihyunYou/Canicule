import requests
import json
import math
import time
import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import winsound
import argparse
import numpy as np
import threading

UNIT = 3
DUREE_MAXIMUM = 20
C_MULTIPLICATION_LARGEUR_BANDE = 1.16
URL_CANDLE = "https://api.upbit.com/v1/candles/minutes/" + str(UNIT)
KEY_ACCESS = ""
KEY_SECRET = ""
URL_SERVEUR = 'https://api.upbit.com'
uuid_achat = []
uuid_vente = ""
premier_prix_achete = 0
idx = 0
TEMPS_SLEEP = 0.25

def animater(s):
	animation = "|/-\\"
	global idx

	idx += 1
	print(s + animation[idx % len(animation)], end="\r")

def tailler(_prix, _taux):
	t = _prix - (_prix / 100) * _taux
	if t < 10: 
		t = round(t, 2)
	elif 10 <= t < 100:
		t = round(t, 1)
	elif 100 <= t < 1000:
		t = round(t, 0)
	elif 1000 <= t < 10000:
		t = round(t, 0)
		t -= t % 5
	elif 10000 <= t < 100000:
		t = round(t, 0)
		t -= t % 10
	elif 100000 <= t < 500000:
		t = round(t, 0)
		t -= t % 50
	elif 500000 <= t < 1000000:
		t = round(t, 0)
		t -= t % 100
	elif 1000000 <= t < 2000000:
		t = round(t, 0)
		t -= t % 500
	elif 2000000 <= t:
		t = round(t, 0)
		t -= t % 1000

	return t

def acheter_prix_marche(_symbol, _montant):
	query = {
		'market': 'KRW-'+ _symbol,
		'side': 'bid',
		'price': str(_montant),
		'ord_type': 'price',
	}
	query_string = urlencode(query).encode()

	m = hashlib.sha512()
	m.update(query_string)
	query_hash = m.hexdigest()

	payload = {
		'access_key': KEY_ACCESS,
		'nonce': str(uuid.uuid4()),
		'query_hash': query_hash,
		'query_hash_alg': 'SHA512',
	}

	jwt_token = jwt.encode(payload, KEY_SECRET)
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	res = requests.post(URL_SERVEUR + "/v1/orders", params=query, headers=headers)

def vendre_prix_marche(_symbol, _volume):
	query = {
		'market': 'KRW-'+ _symbol,
		'side': 'ask',
		'volume': str(_volume),
		'ord_type': 'market',
	}
	query_string = urlencode(query).encode()

	m = hashlib.sha512()
	m.update(query_string)
	query_hash = m.hexdigest()

	payload = {
		'access_key': KEY_ACCESS,
		'nonce': str(uuid.uuid4()),
		'query_hash': query_hash,
		'query_hash_alg': 'SHA512',
	}

	jwt_token = jwt.encode(payload, KEY_SECRET)
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	res = requests.post(URL_SERVEUR + "/v1/orders", params=query, headers=headers)

def acheter_divise(_symbol, _prix_courant, _somme_totale, _taux, _fragmentation, _taux_augmentation_de_a):
	S = _somme_totale
	r = _taux * _fragmentation
	h = _taux_augmentation_de_a
	a = S / (r * ((r + 1) * h / 200 + 1))

	for n in range(1, r + 1):
		pn = tailler(_prix_courant, (n - 1) * (1 / _fragmentation))
		qn = a * h * n / 100 + a
		vn = qn / pn 

		query = {
			'market': "KRW-" + _symbol,
			'side': 'bid',
			'volume': str(vn), 
			'price': str(pn),
			'ord_type': 'limit',
		}
		query_string = urlencode(query).encode()

		m = hashlib.sha512()
		m.update(query_string)
		query_hash = m.hexdigest()

		payload = {
			'access_key': KEY_ACCESS,
			'nonce': str(uuid.uuid4()),
			'query_hash': query_hash,
			'query_hash_alg': 'SHA512',
		}

		jwt_token = jwt.encode(payload, KEY_SECRET)
		authorize_token = 'Bearer {}'.format(jwt_token)
		headers = {"Authorization": authorize_token}

		response = requests.post(URL_SERVEUR + "/v1/orders", params=query, headers=headers)
		dict_response = json.loads(response.text)
		global uuid_achat
		uuid_achat.append(dict_response.get('uuid'))

		#print(response.text)
		time.sleep(TEMPS_SLEEP)

def obtenir_prix_courant(_dict_response): # 현재 종가 구하기
	return _dict_response[0].get('trade_price')

def obtenir_array_trade_price(_dict_response, _n): # 종가 리스트 구하기
	arr = np.zeros(_n)
	for i in range(_n):
		arr[_n - i - 1] = _dict_response[i].get('trade_price')
	return arr

def verifier_bb(_n, _z, _array_trade_price):
	prix_courant = _array_trade_price[-1]
	bb_milieu = np.mean(np.array(_array_trade_price)) 
	bb_haut = bb_milieu + np.std(np.array(_array_trade_price)) * _z
	bb_bas = bb_milieu - np.std(np.array(_array_trade_price)) * _z
	global C_MULTIPLICATION_LARGEUR_BANDE
	largeur_bande_minimum = prix_courant / 100 * C_MULTIPLICATION_LARGEUR_BANDE

	#print("최소 밴드폭 : " + str(largeur_bande_minimum))
	#print("볼린저밴드 상단 : " + str(bb_haut))
	#print("볼린저밴드 하단 : " + str(bb_bas))
	
	if(bb_haut - bb_bas > largeur_bande_minimum):
		if prix_courant < bb_bas:
			print("볼밴이탈 검출!")
			return 1
		return 0
	return -1

def acheter_si_criteres_suffits(_symbol, _z, _somme_totale, _taux, _fragmentation, _taux_augmentation_de_a):
	global DUREE_MAXIMUM
	querystring = {"market":"KRW-"+_symbol,"count":str(DUREE_MAXIMUM)}

	try:
		response = requests.request("GET", URL_CANDLE, params=querystring)
		dict_response = json.loads(response.text)

		array_trade_price = obtenir_array_trade_price(dict_response, DUREE_MAXIMUM)
	except:
		return False
	
	#print("심볼 : " + _symbol)
	if(verifier_bb(20, 2, array_trade_price) <= 0):
		return False

	global premier_prix_achete
	premier_prix_achete = obtenir_prix_courant(dict_response);

	acheter_divise(_symbol, premier_prix_achete, _somme_totale, _taux, _fragmentation, _taux_augmentation_de_a)
	print(_symbol + "매수 신청을 완료했습니다.")
	t = threading.Thread(target = winsound.Beep, args=(440, 500))
	t.start()

	return True

def examiner_compte():
	payload = {
		'access_key': KEY_ACCESS,
		'nonce': str(uuid.uuid4()),
	}

	jwt_token = jwt.encode(payload, KEY_SECRET)
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	while(True):
		try:
			response = requests.get(URL_SERVEUR + "/v1/accounts", headers=headers)
			dict_response = json.loads(response.text)
			time.sleep(TEMPS_SLEEP)

			#print(dict_response)
			return dict_response
		except:
			time.sleep(TEMPS_SLEEP)

def examiner_symbol_compte(_symbol):
	for mon_dict in examiner_compte():
		if(mon_dict.get('currency') == _symbol):
			balance = float(mon_dict.get('balance'))
			locked = float(mon_dict.get('locked'))
			avg_buy_price = float(mon_dict.get('avg_buy_price'))

			return balance, locked, avg_buy_price
	return -1, -1, -1

def annuler_ordre_achat():
	global KEY_ACCESS
	global uuid_achat

	while(True):
		try:
			for p in uuid_achat:
				query = {
					'uuid': p,
				}
				query_string = urlencode(query).encode()

				m = hashlib.sha512()
				m.update(query_string)
				query_hash = m.hexdigest()

				payload = {
					'access_key': KEY_ACCESS,
					'nonce': str(uuid.uuid4()),
					'query_hash': query_hash,
					'query_hash_alg': 'SHA512',
				}

				jwt_token = jwt.encode(payload, KEY_SECRET)
				authorize_token = 'Bearer {}'.format(jwt_token)
				headers = {"Authorization": authorize_token}

				response = requests.delete(URL_SERVEUR + "/v1/order", params=query, headers=headers)
				dict_response = json.loads(response.text)
				#print(dict_response)
			
				time.sleep(TEMPS_SLEEP)	

			uuid_achat.clear()
			return
		except:
			print("오류 : 매수신청 취소에 실패했습니다.")
			time.sleep(TEMPS_SLEEP)

def annuler_ordre_vente():
	global KEY_ACCESS
	global uuid_vente

	while(True):
		try:
			query = {
				'uuid': uuid_vente,
			}
			query_string = urlencode(query).encode()

			m = hashlib.sha512()
			m.update(query_string)
			query_hash = m.hexdigest()

			payload = {
				'access_key': KEY_ACCESS,
				'nonce': str(uuid.uuid4()),
				'query_hash': query_hash,
				'query_hash_alg': 'SHA512',
			}

			jwt_token = jwt.encode(payload, KEY_SECRET)
			authorize_token = 'Bearer {}'.format(jwt_token)
			headers = {"Authorization": authorize_token}

			response = requests.delete(URL_SERVEUR + "/v1/order", params=query, headers=headers)
			dict_response = json.loads(response.text)
			#print(dict_response)

			time.sleep(TEMPS_SLEEP)

			uuid_vente = ""
			return
		except:
			print("오류 : 매도신청 취소에 실패했습니다.")
			time.sleep(TEMPS_SLEEP)
		

# flag_ordre_vendre는 매도주문이 걸려 있는지 여부에 대한 플래그
PRIX_MINIMUM_VENDU = 10000 
flag_ordre_vendre = False
count_montant_insuffissant = 0

def est_ordre_vente_complete(_symbol):
	global flag_ordre_vendre
	global count_montant_insuffissant
	dict_response = examiner_compte()

	if(count_montant_insuffissant > 300):
		print("잔여 매도요청이 체결되지 않아 매도를 취소합니다.")
		count_montant_insuffissant = 0
		flag_ordre_vendre = False
		return True

	for mon_dict in dict_response:
		currency = mon_dict.get('currency')
		balance = float(mon_dict.get('balance'))
		locked = float(mon_dict.get('locked'))
		avg_buy_price = float(mon_dict.get('avg_buy_price'))
		montant = (balance + locked) * avg_buy_price

		if currency == _symbol:
			if(montant < PRIX_MINIMUM_VENDU):
				count_montant_insuffissant += 1
			else:
				count_montant_insuffissant = 0

			if(balance + locked > 0.00001):
				return False
			else:
				break

	if(flag_ordre_vendre == False):
		return False
	else:
		flag_ordre_vendre = False
		return True
	
def vendre_biens(_symbol, _volume, _prix):
	query = {
		'market': 'KRW-' + _symbol,
		'side': 'ask',
		'volume': _volume,
		'price': _prix,
		'ord_type': 'limit',
	}
	query_string = urlencode(query).encode()

	m = hashlib.sha512()
	m.update(query_string)
	query_hash = m.hexdigest()

	payload = {
		'access_key': KEY_ACCESS,
		'nonce': str(uuid.uuid4()),
		'query_hash': query_hash,
		'query_hash_alg': 'SHA512',
	}

	jwt_token = jwt.encode(payload, KEY_SECRET)
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	response = requests.post(URL_SERVEUR + "/v1/orders", params=query, headers=headers)
	dict_response = json.loads(response.text)
	time.sleep(TEMPS_SLEEP)

	global uuid_vente
	uuid_vente = dict_response.get('uuid')
	
	#print(dict_response)
	return dict_response

def administrer_vente(_symbol, _somme_totale, _proportion_profit):
	global flag_ordre_vendre
	global count_montant_insuffissant

	try:
		balance, locked, avg_buy_price = examiner_symbol_compte(_symbol)
		if(balance < 0):
			return False
		
		montant = (balance + locked) * avg_buy_price
		count_montant_insuffissant = 0
		global premier_prix_achete

		if(balance > 0.00001 and montant > 5000):
			if uuid_vente != "":
				annuler_ordre_vente()
				time.sleep(TEMPS_SLEEP)

			time.sleep(1)
			balance, locked, avg_buy_price = examiner_symbol_compte(_symbol)

			if(premier_prix_achete > 0):
				proportion_supplement = (premier_prix_achete - avg_buy_price) / premier_prix_achete * 1.32
				proportion_vente = _proportion_profit + proportion_supplement
				print("매수평균가 : " + str(avg_buy_price) + "(매도점 : +" + str(round(proportion_vente, 3)) + "%)" )

				vendre_biens(_symbol, balance + locked, tailler(avg_buy_price, proportion_vente))
			else:
				print("경고 : 최초 매수가의 값이 0입니다.")
				vendre_biens(_symbol, balance + locked, tailler(avg_buy_price, _proportion_profit))

			flag_ordre_vendre = True
			return True
		elif(montant >= PRIX_MINIMUM_VENDU):
			return True
		else:
			return False	
	except:
		pass
	return False

def obtenir_list_symbol():
	list_symbol = [""]
	with open("ban.txt", 'r') as f:
		list_symbol_interdit = [line.strip() for line in f]
	headers = {"Accept": "application/json"}
	
	try:
		response = requests.request("GET", "https://api.upbit.com/v1/market/all?isDetails=false", headers=headers)
		dict_response1 = json.loads(response.text)
	except:
		print("오류 : 심볼 리스트를 받아오는데 실패하였습니다.")
		return

	for dr in dict_response1:
		market = dr.get('market')
		if(market[:3] == "KRW" and market[4:] not in list_symbol_interdit):
			querystring = {"market" : market, "count" : "24"}

			try:
				response = requests.request("GET", "https://api.upbit.com/v1/candles/minutes/60", params=querystring)
				time.sleep(0.06)
				dict_response2 = json.loads(response.text)
			except:
				return False

			prix = dict_response2[0].get('trade_price')
			acc_trade_price = 0
			for i in range(24):
				acc_trade_price += dict_response2[i].get('candle_acc_trade_price')

			if(7 < prix < 9 or 50 < prix < 90 or 400 < prix < 900 or 3300 < prix):
				if(acc_trade_price > 5000000000):
					list_symbol.append(market[4:])
	del list_symbol[0]

	print(list_symbol)
	print("매수 기준에 충족하는 위 코인 목록을 모니터링합니다.")

	return list_symbol

def obtenir_montant_KRW():
	for mon_dict in examiner_compte():
		if mon_dict.get('currency') == "KRW":
			return float(mon_dict.get('balance'))
	return 0
			
if __name__=="__main__":
	f = open("key.txt", 'r')
	with open("key.txt", 'r') as f:
		KEY_ACCESS = f.readline().strip()
		KEY_SECRET = f.readline().strip()
		print("KEY_ACCESS : " + KEY_ACCESS)
		print("KEY_SECRET : " + KEY_SECRET)

	T_TIMEOUT = 60

	parser = argparse.ArgumentParser(description="J'EN SAIS RIEN.")
	parser.add_argument('-s', type=int, required=False, help='-s : 투입할 총액. 미설정 시, 업비트에 있는 총 보유KRW이 투입됩니다.')
	parser.add_argument('-n', type=int, help='-n : 밴드를 관찰할 n분봉의 n 값 (ex. 1, 3, 5, 10, 15, 30...)')
	parser.add_argument('-z', type=float, help='-z : 볼린저 밴드의 표준정규분포 곱상수. 값이 커질수록 저점에서 매수할 수 있으나 매수포착 기회가 줄어듭니다.')
	parser.add_argument('-t', type=int, help='-t : 최종 매수 지점의 상위비율 (ex. t가 6이라면, 첫 분할매수액의 94퍼까지 분할매수주문을 요청합니다.)')
	parser.add_argument('-f', type=int, help='-f : 1% 당 분절할 분할매수주문 개수 (ex. f가 4라면, 0.25%의 비율로 분할매수합니다.)')
	parser.add_argument('-x', type=int, help='-x : 분할매수할 주문액의 증가비율')
	parser.add_argument('-m', type=float, help='-m : 매수 제한 밴드 폭의 길이. 값이 커질수록 저점에서 매수할 수 있으나 매수포착 기회가 줄어듭니다.')
	parser.add_argument('-v', type=float, help='-v : 매도 지점 비율')
	args = parser.parse_args()
	
	Sp = S = obtenir_montant_KRW()
	print("총 보유 KRW : " + format(int(S), ','))
	
	list_symbol = obtenir_list_symbol()
	z = t = f = x = 0

	DEFAULT_Z = 2
	DEFAULT_T = 10
	DEFAULT_F = 3
	DEFAULT_X = 2000
	DEFAULT_V = 0.34

	if(args.n is not None):
		UNIT = args.n
	else:
		pass

	if(args.z is not None): 
		z = args.z
	else: 
		z = DEFAULT_Z
	
	if(args.t is not None): 
		t = args.t
	else: 
		t = DEFAULT_T

	if(args.f is not None): 
		f = args.f
	else: 
		f = DEFAULT_F

	if(args.x is not None): 
		x = args.x
	else: 
		x = DEFAULT_X

	if(args.v is not None): 
		v = args.v
	else: 
		v = DEFAULT_V

	if(args.m is not None):
		C_MULTIPLICATION_LARGEUR_BANDE = args.m
	else:
		pass

	Commission = 0.9995
	if(args.s is not None):
		if(args.s < 2000000):
			print("2,000,000원 이상을 입력해야 합니다.")
			exit()
		else:
			S = int(args.s * Commission)
	else:
		S = int(S * Commission)

	while(True):
		nom_symbol = ""
		breakable, flag_ordre_vendre = False, False
		fault = 0

		while(True):
			if(breakable): 
				break
			
			for symbol in list_symbol:
				if(breakable): 
					break
				animater("모니터링 중... ")
					
				if(acheter_si_criteres_suffits(symbol, z, S, t, f, x)):
					nom_symbol = symbol
					breakable = True
				else:
					time.sleep(0.055)
		
		while(True):
			if(est_ordre_vente_complete(nom_symbol)):
				print("매도 완료. 잔여 매수 요청을 취소합니다.")
				break
			elif(fault >= T_TIMEOUT):
				print("시간 초과.")
				break

			if(administrer_vente(nom_symbol, S, v)):
				fault = 0
			else:
				fault += 1

		annuler_ordre_achat()

		S = int(obtenir_montant_KRW())
		print("평가손익 : " + '{0:+,}'.format(int(S - Sp)))
		S = int(S * Commission)