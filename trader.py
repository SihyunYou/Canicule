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
from tqdm import tqdm
import datetime
from datetime import datetime
from datetime import timedelta
from colorama import init, Fore, Back, Style

init(autoreset = True)

UNIT = 3
DUREE_MAXIMUM = 20 # >= 20
TEMPS_DORMIR = 0.2
TEMPS_EXCEPTION = 0.25
URL_CANDLE = "https://api.upbit.com/v1/candles/minutes/" + str(UNIT)
CLE_ACCES = ''
CLE_SECRET = ''
URL_SERVEUR = 'https://api.upbit.com'
TEMPS_INITIAL = datetime.now()

uuid_achat = []
uuid_vente = ''
premier_prix_achete = 0

class Niveau:
	INFORMATION = Fore.GREEN + Style.BRIGHT
	SUCCES = Fore.LIGHTWHITE_EX + Back.LIGHTCYAN_EX + Style.BRIGHT
	AVERTISSEMENT = Fore.LIGHTWHITE_EX + Back.LIGHTMAGENTA_EX + Style.BRIGHT
	EXCEPTION = Fore.LIGHTYELLOW_EX + Style.BRIGHT
	ERREUR = Fore.LIGHTWHITE_EX + Back.LIGHTRED_EX + Style.BRIGHT

def imprimer(_niveau, _s):
	niveau_datetime = Fore.MAGENTA + Style.NORMAL
	print(niveau_datetime + '[' + datetime.now().strftime('%m/%d %X') + '] ' + \
		_niveau + _s)

def tailler(_prix, _taux):
	t = _prix - (_prix / 100) * _taux
	if t < 0.1:
		t = round(t, 4)
	elif t < 1:
		t = round(t, 3)
	elif t < 10: 
		t = round(t, 2)
	elif t < 100:
		t = round(t, 1)
	elif t < 1000:
		t = round(t, 0)
	elif t < 10000:
		t = round(t, 0)
		t -= t % 5
	elif t < 100000:
		t = round(t, 0)
		t -= t % 10
	elif t < 500000:
		t = round(t, 0)
		t -= t % 50
	elif t < 1000000:
		t = round(t, 0)
		t -= t % 100
	elif t < 2000000:
		t = round(t, 0)
		t -= t % 500
	elif 2000000 <= t:
		t = round(t, 0)
		t -= t % 1000

	return t

def coller(_prix):
	t = _prix
	if t < 0.1:
		t += 0.0001
	elif t < 1:
		t += 0.001
	elif t < 10: 
		t += 0.01
	elif t < 100:
		t += 0.1
	elif t < 1000:
		t += 1
	elif t < 10000:
		t += 5
	elif t < 100000:
		t += 10
	elif t < 500000:
		t += 50
	elif t < 1000000:
		t += 100
	elif t < 2000000:
		t += 500
	elif 2000000 <= t:
		t += 1000

	return t

class Acheter:
	def __init__(self, _symbol, _prix_courant, _somme_totale):
		self.symbol = _symbol
		self.prix_courant = _prix_courant
		self.S = _somme_totale
		self.poids = 0.018

	# lineaire -> 10 20 30 40 50 = 150
	# parabolique I -> 10 20 40 70 110 = 250
	# parabolique II -> 10 20 35 55 80 = 200 

	def diviser_lineaire(self, _pourcent_descente, _fois_decente, _difference):
		r = _fois_decente
		h = _difference
		a = self.S / (r * ((r + 1) * h / 200 + 1))

		for n in range(1, _fois_decente + 1):
			poids_hauteur = 1 + self.poids * (n - 1)
			pn = tailler(coller(self.prix_courant), (n - 1) * (_pourcent_descente * poids_hauteur))
			qn = a * h * n / 100 + a
			self.acheter(pn, qn)

	def diviser_exposant(self, _pourcent_descente, _fois_decente, _exposant):
		h = _fois_decente
		r = _exposant
		a = self.S * (r - 1) / (pow(r, h) - 1)

		for n in range(1, _fois_decente + 1):
			poids_hauteur = 1 + self.poids * (n - 1)
			pn = tailler(coller(self.prix_courant), (n - 1) * (_pourcent_descente * poids_hauteur))
			qn = a * pow(r, n - 1)
			self.acheter(pn, qn)

	def diviser_parabolique(self, _pourcent_descente, _fois_decente):
		s = _fois_decente * (pow(_fois_decente, 2) + 5) / 6
		for n in range(1, _fois_decente + 1):
			poids_hauteur = 1 + self.poids * (n - 1)
			pn = tailler(coller(self.prix_courant), (n - 1) * (_pourcent_descente * poids_hauteur))
			kn = (pow(n, 2) / 2) - (n / 2) + 1
			qn = self.S * kn / s
			self.acheter(pn, qn)

	def diviser_parabolique2(self, _pourcent_descente, _fois_decente):
		s = _fois_decente * (5 * pow(_fois_decente, 2) + 15 * _fois_decente + 40) / 6
		for n in range(1, _fois_decente + 1):
			poids_hauteur = 1 + self.poids * (n - 1)
			pn = tailler(coller(self.prix_courant), (n - 1) * (_pourcent_descente * poids_hauteur))
			kn = 5 / 2 * pow(n, 2) + 5 / 2 * n + 5
			qn = self.S * kn / s
			self.acheter(pn, qn)

	def diviser_lapin(self, _pourcent_descente, _fois_decente):
		lapin = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946] # 20
		mon_lapin = lapin[:_fois_decente - 1]

		for n in range(1, _fois_decente + 1):
			poids_hauteur = 1 + self.poids * (n - 1)
			pn = tailler(coller(self.prix_courant), (n - 1) * (_pourcent_descente * poids_hauteur))
			qn = self.S * lapin[n - 1] / sum(mon_lapin)
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
			'access_key': CLE_ACCES,
			'nonce': str(uuid.uuid4()),
			'query_hash': query_hash,
			'query_hash_alg': 'SHA512',
		}

		jwt_token = jwt.encode(payload, CLE_SECRET)
		authorize_token = 'Bearer {}'.format(jwt_token)
		headers = {"Authorization": authorize_token}

		response = requests.post(URL_SERVEUR + "/v1/orders", params=query, headers=headers)
		dict_response = json.loads(response.text)
		global uuid_achat
		uuid_achat.append(dict_response.get('uuid'))

		#print(response.text)
		time.sleep(TEMPS_DORMIR)


std_bas = 0
class Verifier:
	def __init__(self, _array_trade_price):
		self.prix_courant = _array_trade_price[-1]
		self.array_trade_price = _array_trade_price

	##### Premiere verification #####
	def verfier_surete(self): # 동적 보호매수
		p = self.array_trade_price[-20]
		q = self.prix_courant
		if - 0.1 < (q - p) / self.prix_courant < 0.25:
			return True
		return False

	def verifier_prix(self):
		if 0.045 < self.prix_courant < 0.0995 or 0.45 < self.prix_courant < 0.995 or 4.5 < self.prix_courant < 9.95 or \
				45 < self.prix_courant < 99.5 or 450 < self.prix_courant < 995 or 3600 < self.prix_courant:
			return True
		return False

	def verifier_tendance_non_negatif(self):
		mm20 = np.mean(np.array(self.array_trade_price)[-20 : -1])
		mm60 = np.mean(np.array(self.array_trade_price)[-60 : -1])
		mm120 = np.mean(np.array(self.array_trade_price)[-120 : -1])

		if mm20 <= mm60 <= mm120:
			return False
		return True

	##### Deuxieme verification #####
	def verifier_bb(self, _n, _z):
		bb_milieu = np.mean(np.array(self.array_trade_price)[-1 * _n : -1]) 
		bb_std = np.std(np.array(self.array_trade_price)[-1 * _n : -1])
		bb_haut = bb_milieu + bb_std * _z
		bb_bas = bb_milieu - bb_std * _z
		largeur_bande_minimum = self.prix_courant / 100 * 1.1

		#print("최소 밴드폭 : " + str(largeur_bande_minimum))
		#print("볼린저밴드 상단 : " + str(bb_haut))
		#print("볼린저밴드 하단 : " + str(bb_bas))
	
		if(bb_haut - bb_bas > largeur_bande_minimum):
			if self.prix_courant < bb_bas:
				imprimer(Niveau.INFORMATION, "Hors de bb !")
				return True
		return False

	def verifier_tendance_positive(self):
		mm20 = np.mean(np.array(self.array_trade_price)[-20 : -1])
		mm60 = np.mean(np.array(self.array_trade_price)[-60 : -1])
		mm120 = np.mean(np.array(self.array_trade_price)[-120 : -1])

		if mm20 > mm60 > mm120:
			if self.prix_courant * 0.04 > mm20 - mm60 > 0 and \
				self.prix_courant > mm60 * 1.01:
				imprimer(Niveau.INFORMATION, "Graphique dont la tendance est positive !")
				return True
		return False

	def verifier_std(self, _n, _z):
		mm20 = np.mean(np.array(self.array_trade_price)[-1 * _n : -1])
		bb_std = np.std(np.array(self.array_trade_price)[-1 * _n : -1])
		bb_limite = mm20 + bb_std * _z # z note 90%
		longeur = bb_std * 4
		pourcent = longeur / self.prix_courant
	
		global std_bas
		p = 0.04 - std_bas
		q = 0.2
		if p < pourcent < q and self.prix_courant < bb_limite:
			imprimer(Niveau.INFORMATION, "Hors de la deviation normale ! : " + str(round(p, 3)))
			return True
		return False


def obtenir_prix_courant(_dict_response): # 현재 종가 구하기
	return _dict_response[0].get('trade_price')

def obtenir_array_trade_price(_dict_response, _n): # 종가 리스트 구하기
	arr = np.zeros(_n)
	for i in range(_n):
		arr[_n - i - 1] = _dict_response[i].get('trade_price')
	return arr

DERNIER_SYMBOL = ''
def controler_achats(_symbol, _somme_totale): # 전부매집
	global DUREE_MAXIMUM
	querystring = {
		"market" : "KRW-" + _symbol,
		"count" : str(DUREE_MAXIMUM)
		}

	try:
		response = requests.request("GET", URL_CANDLE, params=querystring)
		dict_response = json.loads(response.text)

		array_trade_price = obtenir_array_trade_price(dict_response, DUREE_MAXIMUM)
	except:
		imprimer(Niveau.EXCEPTION, "Rate de recuperer les donnes de prix.")
		return False
	
	#print("심볼 : " + _symbol)

	v = Verifier(array_trade_price)
	global DERNIER_SYMBOL
	global std_bas
	if _symbol == DERNIER_SYMBOL:
		if std_bas < 0.01: 
			std_bas += 0.002

	if v.verifier_prix():
		if v.verifier_bb(20, 2) or v.verifier_std(20, -1.68):
			global premier_prix_achete
			premier_prix_achete = obtenir_prix_courant(dict_response)
			a = Acheter(_symbol, premier_prix_achete, _somme_totale)
			#a.diviser_lineaire(0.3333, 36, 10000000) # 선형 매집
			#a.diviser_exposant(0.38, 29, 1.2) # 지수 매집
			#a.diviser_parabolique(0.3333, 25) # 제1형 포물선 매집
			a.diviser_parabolique2(0.3333, 28) # 제2형 포물선 매집
			#a.diviser_lapin(0.34, 16) # 토끼 매집
			
			std_bas = 0
			imprimer(Niveau.INFORMATION, "Acheve de demander l'achat \'" + _symbol + '\'')
			t = threading.Thread(target = winsound.Beep, args=(440, 500))
			t.start()

			return True
	return False


class Annuler:
	def annuler_achats(self):
		global uuid_achat

		while True:
			try:
				for p in uuid_achat:
					self.annuler_commande(p)
				uuid_achat.clear()
				return
			except:
				imprimer(Niveau.EXCEPTION, "Rate d'annuler le demande d'achat.")
				time.sleep(TEMPS_EXCEPTION)
			
	def annuler_vente(self):
		global uuid_vente
		
		while True:
			try:
				self.annuler_commande(uuid_vente)
				uuid_vente = ''
				return
			except:
				imprimer(Niveau.EXCEPTION, "Rate d'annuler le demande de vente.")
				time.sleep(TEMPS_EXCEPTION)

	def annuler_commande(self, _uuid):
		global CLE_ACCES
		query = {
			'uuid': _uuid,
		}
		query_string = urlencode(query).encode()

		m = hashlib.sha512()
		m.update(query_string)
		query_hash = m.hexdigest()

		payload = {
			'access_key': CLE_ACCES,
			'nonce': str(uuid.uuid4()),
			'query_hash': query_hash,
			'query_hash_alg': 'SHA512',
		}

		jwt_token = jwt.encode(payload, CLE_SECRET)
		authorize_token = 'Bearer {}'.format(jwt_token)
		headers = {"Authorization": authorize_token}

		response = requests.delete(URL_SERVEUR + "/v1/order", params=query, headers=headers)
		dict_response = json.loads(response.text)
		#print(dict_response)
			
		time.sleep(TEMPS_DORMIR)
		

def examiner_compte():
	payload = {
		'access_key': CLE_ACCES,
		'nonce': str(uuid.uuid4()),
	}

	jwt_token = jwt.encode(payload, CLE_SECRET)
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	while(True):
		try:
			response = requests.get(URL_SERVEUR + "/v1/accounts", headers=headers)
			dict_response = json.loads(response.text)
			time.sleep(TEMPS_DORMIR)

			#print(dict_response)
			return dict_response
		except:
			time.sleep(TEMPS_DORMIR)

def examiner_symbol_compte(_symbol):
	for mon_dict in examiner_compte():
		if(mon_dict.get('currency') == _symbol):
			balance = float(mon_dict.get('balance'))
			locked = float(mon_dict.get('locked'))
			avg_buy_price = float(mon_dict.get('avg_buy_price'))

			return balance, locked, avg_buy_price
	return -1, -1, -1

# flag_commande_vendre는 매도주문이 걸려 있는지 여부에 대한 플래그
PRIX_MINIMUM_VENDU = 5000
flag_commande_vendre = False
count_montant_insuffissant = 0

def est_commande_vente_complete(_symbol):
	global flag_commande_vendre
	global count_montant_insuffissant
	dict_response = examiner_compte()

	if(count_montant_insuffissant > 300):
		imprimer(Niveau.AVERTISSEMENT, "Annuler le vente car le reste de demande de vente n'est pas conclu.")
		count_montant_insuffissant = 0
		flag_commande_vendre = False
		return True

	for mon_dict in dict_response:
		try:
			currency = mon_dict.get('currency')
			balance = float(mon_dict.get('balance'))
			locked = float(mon_dict.get('locked'))
			avg_buy_price = float(mon_dict.get('avg_buy_price'))
			montant = (balance + locked) * avg_buy_price
		except:
			time.sleep(TEMPS_DORMIR)
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

	if(flag_commande_vendre == False):
		return False
	else:
		flag_commande_vendre = False
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
		'access_key': CLE_ACCES,
		'nonce': str(uuid.uuid4()),
		'query_hash': query_hash,
		'query_hash_alg': 'SHA512',
	}

	jwt_token = jwt.encode(payload, CLE_SECRET)
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	response = requests.post(URL_SERVEUR + "/v1/orders", params=query, headers=headers)
	dict_response = json.loads(response.text)
	time.sleep(TEMPS_DORMIR)

	global uuid_vente
	uuid_vente = dict_response.get('uuid')
	
	#print(dict_response)
	return dict_response

def controler_vente(_symbol, _somme_totale, _proportion_profit):
	global flag_commande_vendre
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
				Annuler().annuler_vente()
				time.sleep(TEMPS_DORMIR)

			time.sleep(TEMPS_DORMIR)
			balance, locked, avg_buy_price = examiner_symbol_compte(_symbol)

			if premier_prix_achete > 0:
				#proportion_supplement = (premier_prix_achete - avg_buy_price) / premier_prix_achete * 1
				proportion_supplement = 0
				proportion_vente = _proportion_profit + proportion_supplement
				imprimer(Niveau.INFORMATION, "prix de moyenne d'acaht : " + str(avg_buy_price) + ", position de vente : " + str(tailler(avg_buy_price, -1 * proportion_vente)))
				vendre_biens(_symbol, balance + locked, tailler(avg_buy_price, -1 * proportion_vente))
			else:
				imprimer(Niveau.AVERTISSEMENT,  "Le premier prix d'achat est 0.")
				vendre_biens(_symbol, balance + locked, tailler(avg_buy_price, -1 * _proportion_profit))

			flag_commande_vendre = True
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
		imprimer(Niveau.ERREUR, "Rate de recuperer la liste de symbols. (1)")
		raise Exception('')

	for dr in tqdm(dict_response1, desc = 'Initialisation'):
		market = dr.get('market')
		comte = 60
		if(market[:3] == "KRW" and market[4:] not in list_symbol_interdit):
			querystring = {"market" : market, "count" : str(comte)} # 3시간 기준

			try:
				response = requests.request("GET", URL_CANDLE, params=querystring)
				time.sleep(0.054)
				dict_response2 = json.loads(response.text)
			except:
				imprimer(Niveau.ERREUR, "Rate de recuperer la liste de symbols. (2)")
				raise Exception('')

			prix = obtenir_prix_courant(dict_response2)
			acc_trade_price = 0
			for i in range(comte):
				acc_trade_price += dict_response2[i].get('candle_acc_trade_price')

			if 0.045 < prix < 0.096 or 0.45 < prix < 0.96 or 4.5 < prix < 9.6 or \
				45 < prix < 96 or 450 < prix < 960 or 3600 < prix:
				if acc_trade_price > 300000000: #300백만
					list_symbol.append(market[4:])

	global DERNIER_SYMBOL
	DERNIER_SYMBOL = list_symbol[-1]
	imprimer(Niveau.INFORMATION, 
				"Monitorer la liste suivie de crypto monnaies qui suffit a la critere d'achat.\n" + \
				'[' + ', '.join(list_symbol) + ']')	

	return list_symbol

def obtenir_solde_KRW():
	for mon_dict in examiner_compte():
		if mon_dict.get('currency') == "KRW":
			return float(mon_dict.get('balance'))
	return 0

idx = 0
def animater(_s):
	global idx
	animation = "|/-\\"
	idx += 1
	print(_s + animation[idx % len(animation)], end="\r")


if __name__=="__main__":
	with open("key.txt", 'r') as f:
		CLE_ACCES = f.readline().strip()
		CLE_SECRET = f.readline().strip()
		imprimer(Niveau.INFORMATION, "CLE_ACCES : " + CLE_ACCES)
		imprimer(Niveau.INFORMATION, "CLE_SECRET : " + CLE_SECRET)

	T_TIMEOUT = 30
	TEMPS_REINITIAL = datetime.now()
	parser = argparse.ArgumentParser(description="T'es vraiment qu'un sale petit.")
	parser.add_argument('-s', type=int, required=False, help='-s : La somme mise.')
	args = parser.parse_args()
	
	Sp = S = obtenir_solde_KRW()
	imprimer(Niveau.INFORMATION, "KRW disponible : " + format(int(S), ','))
	list_symbol = obtenir_list_symbol()

	Commission = 0.9995
	if(args.s is not None):
		if(args.s < 5000000):
			imprimer(Niveau.ERREUR, "Vous devez saisir plus de 5,000,000 won.")
			exit()
		else:
			S = int(args.s * Commission)
	else:
		S = int(S * Commission)

	nom_symbol = ''
	while True:
		if datetime.now() - TEMPS_REINITIAL > timedelta(hours = 4): 
			TEMPS_REINITIAL = datetime.now()
			list_symbol = obtenir_list_symbol()

			if nom_symbol != '' and nom_symbol in list_symbol:
				list_symbol.remove(nom_symbol)
				list_symbol.insert(0, nom_symbol)
				DERNIER_SYMBOL = list_symbol[-1]
		else:
			breakable, flag_commande_vendre = False, False
			fault = 0

			while True:
				if breakable: 
					break
			
				for symbol in list_symbol:
					if breakable: 
						break
					animater("En train de monitorer... ")
					
					if controler_achats(symbol, S):
						nom_symbol = symbol
						breakable = True
					else:
						time.sleep(0.0515)

			list_symbol.remove(nom_symbol)
			list_symbol.insert(0, nom_symbol)
			DERNIER_SYMBOL = list_symbol[-1]

			while True:
				if est_commande_vente_complete(nom_symbol):
					imprimer(Niveau.SUCCES, "Vente achevee. Annuler le reste de demandes d'achat.")
					break
				elif fault >= T_TIMEOUT:
					imprimer(Niveau.AVERTISSEMENT, "Hors du temps.")
					break

				if controler_vente(nom_symbol, S, 0.34):
					fault = 0
				else:
					fault += 1

			Annuler().annuler_achats()

			S = int(obtenir_solde_KRW())
			interet = "Interet : " + '{0:+,}'.format(int(S - Sp)) + ' (' + str(datetime.now() - TEMPS_INITIAL) + ')'
			imprimer(Niveau.INFORMATION, interet)
			S = int(S * Commission)
