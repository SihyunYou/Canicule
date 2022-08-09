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
import traceback

init(autoreset = True)

UNIT = 3
TEMPS_DORMIR = 0.17
TEMPS_EXCEPTION = 0.25
URL_CANDLE = "https://api.upbit.com/v1/candles/minutes/" + str(UNIT)
CLE_ACCES = ''
CLE_SECRET = ''
URL_SERVEUR = 'https://api.upbit.com'

uuid_achat = []
uuid_vente = ''

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


class RecupererCodeMarche:
	def __init__(self):
		try:
			headers = {"Accept": "application/json"}
			response = requests.request("GET", "https://api.upbit.com/v1/market/all?isDetails=false", headers=headers)
			self.dict_response = json.loads(response.text)
		except:
			imprimer(Niveau.ERREUR, "Rate de recuperer la liste de symbols. (1)")
			raise Exception('Recuperer code de marche')


COMTE = 200
class RecupererInfoCandle:
	def __recuperer_array(self, _s, _n):
		arr = np.zeros(_n)
		for i in range(_n):
			arr[_n - i - 1] = self.dict_response[i].get(_s)
		return arr

	def __init__(self, _symbol):
		querystring = {
			"market" : "KRW-" + _symbol,
			"count" : str(COMTE)
		}

		try:
			response = requests.request("GET", URL_CANDLE, params=querystring)
			self.dict_response = json.loads(response.text)
			#print("심볼 : " + _symbol)
		except:
			imprimer(Niveau.EXCEPTION, "Rate de recuperer les donnes de prix.")
			raise Exception("RecupererInfoCandle")

		self.array_opening_price = self.__recuperer_array('opening_price', COMTE)
		self.array_trade_price = self.__recuperer_array('trade_price', COMTE)
		self.prix_courant = self.array_trade_price[-1]
		self.array_high_price = self.__recuperer_array('high_price', COMTE)
		self.array_low_price = self.__recuperer_array('low_price', COMTE)
		self.array_acc_trade_price = self.__recuperer_array('candle_acc_trade_price', COMTE)


class Verifier:
	def __init__(self, _symbol):
		self.candle = RecupererInfoCandle(_symbol)
		self.std20 = np.std(np.array(self.candle.array_trade_price)[-20 : -1])
		self.std20_regularise = self.std20 / self.candle.prix_courant
		self.mm20 = np.mean(np.array(self.candle.array_trade_price)[-20 : -1])

	##### Premiere verification #####
	def verfier_surete(self):
		p = self.candle.array_trade_price[-60]
		q = self.candle.prix_courant
		if - 0.2 < (q - p) / self.candle.prix_courant < 0.4 and \
			self.candle.prix_courant < self.mm20 - self.std20 * 0: # 0.2533(10%), 0.5243(20%)
			return True
		return False

	def verifier_prix(self):
		if 0.048 < self.candle.prix_courant < 0.0995 or 0.48 < self.candle.prix_courant < 0.995 or \
			4.8 < self.candle.prix_courant < 9.95 or 48 < self.candle.prix_courant < 99.5 or \
			480 < self.candle.prix_courant < 995 or 3600 < self.candle.prix_courant:
			return True
		return False


	##### Deuxieme verification negative #####
	def verifier_bb_variable(self, _n):
		# x = std_regularise, y = z-note
		# y <= 144x - 2.72

		z = (self.candle.prix_courant - self.mm20) / self.std20 
		if self.std20_regularise >= 0.003 and z <= 0:
			if z <= 144 * self.std20_regularise - 2.72:
				imprimer(Niveau.INFORMATION, 
							"Hors de bb_variable ! z : " + str(round(z, 3)) + 
							", std_regularise : " + str(round(self.std20_regularise, 5)))
				return True
		return False

	def verifier_vr(self, _n, _p):
		if self.std20_regularise >= 0.005:
			h, b, e = 0, 0, 0
			for i in range(-1 * _n, 0):
				p = self.candle.array_trade_price[i] - self.candle.array_opening_price[i]
				if p > 0:
					h += self.candle.array_acc_trade_price[i]
				elif p < 0:
					b += self.candle.array_acc_trade_price[i]
				else:
					e += self.candle.array_acc_trade_price[i]

			if b <= 0 and e <= 0:
				return False
			else:
				vr = (h + e * 0.5) / (b + e * 0.5) * 100
				if vr <= _p:
					imprimer(Niveau.INFORMATION, 
								"Hors de vr ! vr : " + str(round(vr, 2)))
					return True
		return False

	def verifier_decalage_mm(self, _n, _p):
		std_pondere = self.std20_regularise * 20
		decalage = _p * (1 + std_pondere)

		if self.candle.prix_courant < self.mm20 * (1 - decalage):
			imprimer(Niveau.INFORMATION, 
						"Hors d'envelope ! decalage : " + str(round(decalage, 3)))
			return True
		return False


	##### Deuxieme verification positive #####
	def verifier_tendance_positive(self):
		if self.std20_regularise >= 0.005:
			mm5 = np.mean(np.array(self.candle.array_trade_price)[-5 : -1])
			mm60 = np.mean(np.array(self.candle.array_trade_price)[-60 : -1])
			mm120 = np.mean(np.array(self.candle.array_trade_price)[-120 : -1])

			if (self.candle.prix_courant - self.mm20) / self.mm20 < 1.24:
				if mm5 > self.mm20 > mm60 > mm120:
					imprimer(Niveau.INFORMATION,
								"Tendance positive !")
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
		

class ExaminerCompte:
	def __init__(self):
		payload = {
			'access_key': CLE_ACCES,
			'nonce': str(uuid.uuid4()),
		}

		jwt_token = jwt.encode(payload, CLE_SECRET)
		authorize_token = 'Bearer {}'.format(jwt_token)
		headers = {"Authorization": authorize_token}

		while True:
			try:
				response = requests.get(URL_SERVEUR + "/v1/accounts", headers=headers)
				self.dict_response = json.loads(response.text)
				time.sleep(TEMPS_DORMIR)
				break
			except:
				time.sleep(TEMPS_DORMIR)

	def recuperer_solde_krw(self):
		for mon_dict in self.dict_response:
			if mon_dict.get('currency') == "KRW":
				return float(mon_dict.get('balance'))
		return 0

	def recuperer_symbols(self):
		symbols = []
		for mon_dict in self.dict_response:
			symbols.append(mon_dict.get('currency'))
		return symbols

	def recuperer_symbol_info(self, _symbol):
		for mon_dict in self.dict_response:
			if mon_dict.get('currency') == _symbol:
				balance = float(mon_dict.get('balance'))
				locked = float(mon_dict.get('locked'))
				avg_buy_price = float(mon_dict.get('avg_buy_price'))

				return balance, locked, avg_buy_price
		return -1, -1, -1


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


class Vendre:
	def __init__(self, _symbol, _volume, _prix):
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


class ControlerVente:
	def __init__(self):
		self.flag_commande_vendre = False
		self.count_montant_insuffissant = 0
	
	def est_commande_vente_complete(self, _symbol):
		ec = ExaminerCompte()
		symbols = ec.recuperer_symbols()

		if self.count_montant_insuffissant > 300:
			imprimer(Niveau.AVERTISSEMENT, "Annuler le vente car le reste de demande de vente n'est pas conclu.")
			self.count_montant_insuffissant = 0
			self.flag_commande_vendre = False
			return True

		for symbol in symbols:
			try:
				balance, locked, avg_buy_price = ec.recuperer_symbol_info(symbol)
				montant = (balance + locked) * avg_buy_price
			except:
				time.sleep(TEMPS_DORMIR)
				return False

			if symbol == _symbol:
				if montant < 5000:
					self.count_montant_insuffissant += 1
				else:
					self.count_montant_insuffissant = 0

				if balance + locked > 0.00001:
					return False
				else:
					break

		if self.flag_commande_vendre == False:
			return False
		else:
			self.flag_commande_vendre = False
			return True

	def vendre_a_plein(self, _symbol, _somme_totale, _proportion_profit):
		try:
			balance, locked, avg_buy_price = ExaminerCompte().recuperer_symbol_info(_symbol)
			if balance < 0:
				return False
		
			montant = (balance + locked) * avg_buy_price
			self.count_montant_insuffissant = 0

			if balance > 0.00001 and montant > 5000:
				if uuid_vente != "":
					Annuler().annuler_vente()
					time.sleep(TEMPS_DORMIR)
				time.sleep(TEMPS_DORMIR)

				balance, locked, avg_buy_price = ExaminerCompte().recuperer_symbol_info(_symbol)
				imprimer(Niveau.INFORMATION, 
							"prix de moyenne d'acaht : " + str(avg_buy_price) + ", position de vente : " + str(tailler(avg_buy_price, -1 * _proportion_profit)))
				Vendre(_symbol, balance + locked, tailler(avg_buy_price, -1 * _proportion_profit))

				self.flag_commande_vendre = True
				return True
			elif montant >= 5000:
				return True
			else:
				return False	
		except Exception as e:
			traceback.print_exc()
		return False


if __name__=="__main__":
	with open("key.txt", 'r') as f:
		CLE_ACCES = f.readline().strip()
		CLE_SECRET = f.readline().strip()
		imprimer(Niveau.INFORMATION, "CLE_ACCES : " + CLE_ACCES)
		imprimer(Niveau.INFORMATION, "CLE_SECRET : " + CLE_SECRET)

	T_TIMEOUT = 30
	TEMPS_INITIAL = datetime.now()
	TEMPS_REINITIAL = datetime.now() - timedelta(hours = 24)
	parser = argparse.ArgumentParser(description="T'es vraiment qu'un sale petit.")
	parser.add_argument('-s', type=int, required=False, help='-s : La somme mise.')
	args = parser.parse_args()
	
	Sp = S = ExaminerCompte().recuperer_solde_krw()
	imprimer(Niveau.INFORMATION, "KRW disponible : " + format(int(S), ','))

	Commission = 0.9995
	if args.s is not None:
		if args.s < 5000000:
			imprimer(Niveau.ERREUR, "Vous devez saisir plus de 5,000,000 won.")
			exit()
		else:
			S = int(args.s * Commission)
	else:
		S = int(S * Commission)
	
	nom_symbol = ''
	idx = 0
	animation = "|/-\\"

	while True:
		if datetime.now() - TEMPS_REINITIAL > timedelta(hours = 4):
			TEMPS_REINITIAL = datetime.now()
			list_symbol = []
			with open("ban.txt", 'r') as f:
				list_symbol_interdit = [line.strip() for line in f]

			for dr in tqdm(RecupererCodeMarche().dict_response, desc = 'Initialisation'):
				marche = dr.get('market')
				if marche[:3] == "KRW" and marche[4:] not in list_symbol_interdit:
					r = RecupererInfoCandle(marche[4:])
					time.sleep(0.054)

					if 0.04 < r.prix_courant < 0.102 or 0.4 < r.prix_courant < 1.02 or 4 < r.prix_courant < 10.2 or \
						40 < r.prix_courant < 102 or 400 < r.prix_courant < 1020 or 3200 < r.prix_courant:
						acc_trade_price = 0
						for i in range(80):
							acc_trade_price += r.array_acc_trade_price[i]

						if acc_trade_price > 300000000: #300백만
							list_symbol.append(marche[4:])

			imprimer(Niveau.INFORMATION, 
						"Monitorer la liste suivie de crypto monnaies qui suffit a la critere d'achat.\n" + \
						'[' + ', '.join(list_symbol) + ']')	

			if nom_symbol != '' and nom_symbol in list_symbol:
				list_symbol.remove(nom_symbol)
				list_symbol.insert(0, nom_symbol)
		else:
			breakable, flag_commande_vendre = False, False
			fault = 0

			while True:
				if breakable: 
					break
			
				for symbol in list_symbol:
					if breakable: 
						break
					
					idx += 1
					print("En train de monitorer..." + animation[idx % len(animation)], end="\r")
					
					try:
						v = Verifier(symbol)
						if v.verfier_surete() and v.verifier_prix():
							if v.verifier_bb_variable(20):
								Acheter(symbol, v.candle.prix_courant, S).diviser_lineaire(0.3333, 33, 10000000) # 선형 매집			
								verification_passable = True
							elif v.verifier_vr(20, 40) or v.verifier_decalage_mm(20, 0.6):
								Acheter(symbol, v.candle.prix_courant, S).diviser_parabolique2(0.3333, 27) # 제2형 포물선 매집
								verification_passable = True
							elif v.verifier_tendance_positive():
								Acheter(symbol, v.candle.prix_courant, S).diviser_parabolique(0.35, 26) # 제1형 포물선 매집
								verification_passable = True
							else:
								verification_passable = False

							#a.diviser_exposant(0.38, 29, 1.2) # 지수 매집
							#a.diviser_lapin(0.34, 16) # 토끼 매집

							if verification_passable:
								nom_symbol = symbol
								breakable = True
								imprimer(Niveau.INFORMATION, "Acheve de demander l'achat \'" + symbol + '\'')
							
								t = threading.Thread(target = winsound.Beep, args=(440, 500))
								t.start()
					except Exception as e:
						traceback.print_exc()
					time.sleep(0.0515)
			
			if nom_symbol != '' and nom_symbol in list_symbol:
				list_symbol.remove(nom_symbol)
				list_symbol.insert(0, nom_symbol)

			cv = ControlerVente()
			while True:
				if cv.est_commande_vente_complete(nom_symbol):
					imprimer(Niveau.SUCCES, "Vente achevee. Annuler le reste de demandes d'achat.")
					break
				elif fault >= T_TIMEOUT:
					imprimer(Niveau.AVERTISSEMENT, "Hors du temps.")
					break

				if cv.vendre_a_plein(nom_symbol, S, 0.35):
					fault = 0
				else:
					fault += 1

			Annuler().annuler_achats()
			S = int(ExaminerCompte().recuperer_solde_krw())
			imprimer(Niveau.INFORMATION,
						"Interet : " + '{0:+,}'.format(int(S - Sp)) + ' (' + str(datetime.now() - TEMPS_INITIAL) + ')')
			S = int(S * Commission)