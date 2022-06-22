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
DUREE_MAXIMUM = 120
TEMPS_SLEEP = 0.23
URL_CANDLE = "https://api.upbit.com/v1/candles/minutes/" + str(UNIT)
KEY_ACCESS = ""
KEY_SECRET = ""
URL_SERVEUR = 'https://api.upbit.com'

uuid_achat = []
uuid_vente = ""
premier_prix_achete = 0

idx = 0
def animater(s):
	animation = "|/-\\"
	global idx

	idx += 1
	print(s + animation[idx % len(animation)], end="\r")

def tailler(_prix, _taux):
	t = _prix - (_prix / 100) * _taux
	if t < 0.1:
		t = round(t, 4)
	elif t < 1:
		t = round(t, 3)
	elif t < 10: 
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


class Diviser:
	def __init__(self, _symbol, _prix_courant, _somme_totale):
		self.symbol = _symbol
		self.prix_courant = _prix_courant
		self.S = _somme_totale

	def diviser_lineaire(self, _pourcent_descente, _fois_decente, _difference):
		r = _fois_decente
		h = _difference
		a = self.S / (r * ((r + 1) * h / 200 + 1))

		for n in range(1, _fois_decente + 1):
			pn = tailler(self.prix_courant, (n - 1) * _pourcent_descente)
			qn = a * h * n / 100 + a #투입 금액
			self.acheter(pn, qn)

	def diviser_exposant(self, _pourcent_descente, _fois_decente, _exposant):
		h = _fois_decente
		r = _exposant
		a = self.S * (r - 1) / (pow(r, h) - 1)

		for n in range(1, _fois_decente + 1):
			pn = tailler(self.prix_courant, (n - 1) * _pourcent_descente)
			qn = a * pow(r, n - 1)
			self.acheter(pn, qn)

	def diviser_lucas(self, _pourcent_descente, _fois_decente):
		lucas = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946] # 20
		mon_lucas = lucas[:_fois_decente - 1]

		for n in range(1, _fois_decente + 1):
			pn = tailler(self.prix_courant, (n - 1) * _pourcent_descente)
			qn = self.S * lucas[n - 1] / sum(mon_lucas)
			self.acheter(pn, qn) 

	def acheter(self, _pn, _qn):
		query = {
			'market': "KRW-" + self.symbol,
			'side': 'bid',
			'volume': str(_qn / _pn), 
			'price': str(_pn),
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


class Verifier:
	def __init__(self, _array_trade_price):
		self.prix_courant = _array_trade_price[-1]
		self.array_trade_price = _array_trade_price

	def verifier_bb(self, _n, _z):
		bb_milieu = np.mean(np.array(self.array_trade_price)[-1 * _n : -1]) 
		bb_haut = bb_milieu + np.std(np.array(self.array_trade_price)[-1 * _n : -1]) * _z
		bb_bas = bb_milieu - np.std(np.array(self.array_trade_price)[-1 * _n : -1]) * _z
		C_MULTIPLICATION_LARGEUR_BANDE = 1.2
		largeur_bande_minimum = prix_courant / 100 * C_MULTIPLICATION_LARGEUR_BANDE

		#print("최소 밴드폭 : " + str(largeur_bande_minimum))
		#print("볼린저밴드 상단 : " + str(bb_haut))
		#print("볼린저밴드 하단 : " + str(bb_bas))
	
		if(bb_haut - bb_bas > largeur_bande_minimum):
			if self.prix_courant < bb_bas:
				print("볼밴이탈 검출!")
				return True
		return False

	def verifier_tendance_positive(self):
		mm20 = np.mean(np.array(self.array_trade_price)[-20 : -1])
		mm60 = np.mean(np.array(self.array_trade_price)[-60 : -1])
		mm120 = np.mean(np.array(self.array_trade_price)[-120 : -1])

		if(mm20 > mm60 > mm120):
			if self.prix_courant * 0.04 > mm20 - mm60 > 0 and \
				self.prix_courant > mm60 * 1.01:
				print("우상향 차트 검출!")
				return True
		return False

	def verifier_std(self, _n, _z):
		mm20 = np.mean(np.array(self.array_trade_price)[-20 : -1])
		longeur = 2 * np.std(np.array(self.array_trade_price)[-1 * _n : -1]) * _z
		pourcent = longeur / self.prix_courant
	
		if(0.03 < pourcent < 0.15 and self.prix_courant > mm20):
			print("표준편차 이탈 검출!")
			return True
		return False


def obtenir_prix_courant(_dict_response): # 현재 종가 구하기
	return _dict_response[0].get('trade_price')

def obtenir_array_trade_price(_dict_response, _n): # 종가 리스트 구하기
	arr = np.zeros(_n)
	for i in range(_n):
		arr[_n - i - 1] = _dict_response[i].get('trade_price')
	return arr

def acheter_si_prix_suffit_a_verification(_symbol, _somme_totale): # 전부매집
	global DUREE_MAXIMUM
	querystring = {"market":"KRW-"+_symbol,"count":str(DUREE_MAXIMUM)}

	try:
		response = requests.request("GET", URL_CANDLE, params=querystring)
		dict_response = json.loads(response.text)

		array_trade_price = obtenir_array_trade_price(dict_response, DUREE_MAXIMUM)
	except:
		return False
	
	#print("심볼 : " + _symbol)

	v = Verifier(array_trade_price)
	#if v.verifier_bb(20, 2):
	#if v.verifier_tendance_positive():
	if v.verifier_std(20, 2): # 표준편차 이탈 관찰
		global premier_prix_achete
		premier_prix_achete = obtenir_prix_courant(dict_response)

		d = Diviser(_symbol, premier_prix_achete, _somme_totale)
		#d.diviser_lineaire(0.333, 36, 10000) # 선형 매집
		d.diviser_exposant(0.4, 30, 1.2) # 지수 매집
		#d.diviser_lucas(0.5, 16) # 뤼카수열 매집

		print(_symbol + "매수 신청을 완료했습니다.")
		t = threading.Thread(target = winsound.Beep, args=(440, 500))
		t.start()

		return True
	else:
		return False

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
		try:
			currency = mon_dict.get('currency')
			balance = float(mon_dict.get('balance'))
			locked = float(mon_dict.get('locked'))
			avg_buy_price = float(mon_dict.get('avg_buy_price'))
			montant = (balance + locked) * avg_buy_price
		except:
			time.sleep(TEMPS_SLEEP)
			return False

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
				proportion_supplement = (premier_prix_achete - avg_buy_price) / premier_prix_achete * 1.12
				proportion_vente = _proportion_profit + proportion_supplement
				print("매수평균가 : " + str(avg_buy_price) + "(매도점 : +" + str(round(proportion_vente, 3)) + "%)" )

				vendre_biens(_symbol, balance + locked, tailler(avg_buy_price, -1 * proportion_vente))
			else:
				print("경고 : 최초 매수가의 값이 0입니다.")
				vendre_biens(_symbol, balance + locked, tailler(avg_buy_price, -1 * _proportion_profit))

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
	list_symbol = []
	with open("ban.txt", 'r') as f:
		list_symbol_interdit = [line.strip() for line in f]
	headers = {"Accept": "application/json"}
	
	try:
		response = requests.request("GET", "https://api.upbit.com/v1/market/all?isDetails=false", headers=headers)
		dict_response1 = json.loads(response.text)
	except:
		raise Exception("오류 : 심볼 리스트를 받아오는데 실패하였습니다.(1)")

	for dr in dict_response1:
		market = dr.get('market')
		if(market[:3] == "KRW" and market[4:] not in list_symbol_interdit):
			querystring = {"market" : market, "count" : "24"}

			try:
				response = requests.request("GET", "https://api.upbit.com/v1/candles/minutes/60", params=querystring)
				time.sleep(0.06)
				dict_response2 = json.loads(response.text)
			except:
				raise Exception("오류 : 심볼 리스트를 받아오는데 실패하였습니다.(2)")

			prix = obtenir_prix_courant(dict_response2)
			acc_trade_price = 0
			for i in range(24):
				acc_trade_price += dict_response2[i].get('candle_acc_trade_price')

			if(0.04 < prix < 0.09 or 0.4 < prix < 0.9 or 4 < prix < 9 or 40 < prix < 90 or 400 < prix < 900 or 3200 < prix):
				if(acc_trade_price > 8000000000): #8000백만
					list_symbol.append(market[4:])

	print(list_symbol)
	print("매수 기준에 충족하는 위 코인 목록을 모니터링합니다.")

	return list_symbol

def obtenir_montant_KRW():
	for mon_dict in examiner_compte():
		if mon_dict.get('currency') == "KRW":
			return float(mon_dict.get('balance'))
	return 0
			
if __name__=="__main__":
	with open("key.txt", 'r') as f:
		KEY_ACCESS = f.readline().strip()
		KEY_SECRET = f.readline().strip()
		print("KEY_ACCESS : " + KEY_ACCESS)
		print("KEY_SECRET : " + KEY_SECRET)

	T_TIMEOUT = 40

	parser = argparse.ArgumentParser(description="J'EN SAIS RIEN.")
	parser.add_argument('-s', type=int, required=False, help='-s : 투입할 총액. 미설정 시, 업비트에 있는 총 보유KRW이 투입됩니다.')
	args = parser.parse_args()
	
	Sp = S = obtenir_montant_KRW()
	print("총 보유 KRW : " + format(int(S), ','))
	
	list_symbol = obtenir_list_symbol()

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
					
				if(acheter_si_prix_suffit_a_verification(symbol, S)):
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

			if(administrer_vente(nom_symbol, S, 0.3)):
				fault = 0
			else:
				fault += 1

		annuler_ordre_achat()

		S = int(obtenir_montant_KRW())
		print("평가손익 : " + '{0:+,}'.format(int(S - Sp)))
		S = int(S * Commission)