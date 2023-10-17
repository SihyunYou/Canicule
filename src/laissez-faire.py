import requests
import json
import math
import time
import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode, unquote
import winsound
import argparse
import numpy as np
import threading
from tqdm import tqdm
import datetime
from datetime import datetime, timedelta
from colorama import init, Fore, Back, Style
import traceback
from enum import Enum, IntEnum
import functools
import talib
from talib import MA_Type

init(autoreset = True)

UNIT = 5
TEMPS_DORMIR = 0.17
TEMPS_EXCEPTION = 0.25
URL_CANDLE = "https://api.upbit.com/v1/candles/minutes/" + str(UNIT)
CLE_ACCES = ''
CLE_SECRET = ''
URL_SERVEUR = 'https://api.upbit.com'
Sp = 0
uuid_achat = []
uuid_vente = ''
Commission = 0.9995

class Niveau:
	INFORMATION = Fore.GREEN + Style.BRIGHT
	SUCCES = Fore.LIGHTWHITE_EX + Back.LIGHTCYAN_EX + Style.BRIGHT
	AVERTISSEMENT = Fore.LIGHTWHITE_EX + Back.LIGHTMAGENTA_EX + Style.BRIGHT
	EXCEPTION = Fore.LIGHTYELLOW_EX + Style.BRIGHT
	ERREUR = Fore.LIGHTWHITE_EX + Back.LIGHTRED_EX + Style.BRIGHT


if not os.path.exists('log'):
	os.makedirs('log')
NOM_FICHE_LOG = 'log\\' + datetime.now().strftime('%m.%d.%X').replace(':', '') + '.txt'

def imprimer(_niveau, _s):
	niveau_datetime = Fore.MAGENTA + Style.NORMAL
	t = '[' + datetime.now().strftime('%m/%d %X') + '] '
	print(niveau_datetime + t + _niveau + _s)
	
	with open(NOM_FICHE_LOG, 'a') as f:
		f.write(t + _s + '\n')

def logger_masse(_n):
	try:
		with open("log/masse.txt", 'w') as f:
			f.write(str(int(_n)) + ',' + str(int(Sp)))
	except PermissionError:
		pass

class LOG_ETAT(IntEnum):
	ERREUR = 0
	ATTENDRE = 1
	INITIALISER = 2
	ACHETER = 3
	INVESTIR = 4
	HORS_DU_TEMPS = 5
	ACCOMPLIR = 6

def logger_etat(_n, _s = ''):
	try:
		with open("log/etat.txt", 'w') as f:
			f.write('#' + str(int(_n)))
			if _s != '':
				f.write(',' + _s)
	except PermissionError:
		pass

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
		t = math.ceil(t, 0)
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
			imprimer(Niveau.ERREUR, "Failed to return list of symbols. (1)")
			raise Exception('RecupererCodeMarche')


class RecupererInfoCandle:
	def __renverser_array(self, _s : str, _n : int):
		arr = [0] * _n
		for i in range(_n):
			arr[_n - i - 1] = self.dict_response[i].get(_s)
		return arr

	def __init__(self, _symbol : str):
		c = 20
		querystring = {
			"market" : "KRW-" + _symbol,
			"count" : str(c)
		}

		try:
			response = requests.request("GET", URL_CANDLE, params=querystring)
			self.dict_response = json.loads(response.text)

			time.sleep(0.051)
		except:
			imprimer(Niveau.EXCEPTION, "Failed to return price data.")
			raise Exception("RecupererInfoCandle")

		self.list_opening_price = self.__renverser_array('opening_price', c)
		self.list_trade_price = self.__renverser_array('trade_price', c)
		self.prix_courant = self.list_trade_price[-1]
		self.list_high_price = self.__renverser_array('high_price', c)
		self.list_low_price = self.__renverser_array('low_price', c)
		self.list_acc_trade_price = self.__renverser_array('candle_acc_trade_price', c)


class Verifier:
	def __init__(self, _symbol):
		self.candle = RecupererInfoCandle(_symbol)
		self.prix_maximum = max(self.candle.list_high_price)
		self.prix_minimum = min(self.candle.list_low_price)
		self.mm20 = talib.MA(np.array(self.candle.list_trade_price), timeperiod = 20)[-1]
		self.ecart_type20 = talib.STDDEV(np.array(self.candle.list_trade_price), timeperiod = 20)[-1]
		self.ecart_type20_regularise = self.ecart_type20 / self.candle.prix_courant
		self.indice_ecart_relative = (self.candle.prix_courant - self.mm20) / self.ecart_type20

	def trouver_rsi(self):
		return talib.RSI(np.array(self.candle.list_trade_price), timeperiod = 14)[0]

	def trouver_williams_r(self):
		return talib.WILLR(
				np.array(self.candle.list_high_price),
				np.array(self.candle.list_low_price),
				np.array(self.candle.list_trade_price),
				timeperiod = 14)[0]

	def trouver_mfi(self):
		return talib.MFI(
				np.array(self.candle.list_high_price),
				np.array(self.candle.list_low_price),
				np.array(self.candle.list_trade_price),
				np.array(self.candle.list_acc_trade_price),
				timeperiod = 14)[0]


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
				imprimer(Niveau.EXCEPTION, "Failed to cancel buy orders.")
				time.sleep(TEMPS_EXCEPTION)
			
	def annuler_vente(self):
		global uuid_vente
		
		while True:
			try:
				self.annuler_commande(uuid_vente)
				uuid_vente = ''
				return
			except:
				imprimer(Niveau.EXCEPTION, "Failed to cancel sell order.")
				time.sleep(TEMPS_EXCEPTION)

	# @ _type
	# 1 : Annuler tous les commandes d'achat
	# 2 : Annuler tous les commandes de vente
	# 3 : Annuler tous les commandes d'achat et de vente
	def annuler_precommandes(self, _type : int):
		params = {
			'state': 'wait'
		}
		query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")

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
		authorization = 'Bearer {}'.format(jwt_token)
		headers = {
		  'Authorization': authorization,
		}

		response = requests.get(URL_SERVEUR + '/v1/orders', params=params, headers=headers)
		dict_response = json.loads(response.text)
		#print(dict_response)
			
		time.sleep(TEMPS_DORMIR)

		if 1 == _type:
			for mon_dict in dict_response:
				if mon_dict.get('side') == 'bid':
					self.annuler_commande(mon_dict.get('uuid'))
		elif 2 == _type:
			for mon_dict in dict_response:
				if mon_dict.get('side') == 'ask':
					self.annuler_commande(mon_dict.get('uuid'))
		elif 3 == _type:
			for mon_dict in dict_response:
				self.annuler_commande(mon_dict.get('uuid'))

	def annuler_commande(self, _uuid):
		global CLE_ACCES
		params = {
			'uuid': _uuid,
		}
		query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")

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

		response = requests.delete(URL_SERVEUR + "/v1/order", params=params, headers=headers)
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

	# @ _type -> int
	# 1 : solde(disponible)
	# 2 : ferme
	# 3 : solde + ferme
	def recuperer_solde_krw(self, _type = 1):
		for mon_dict in self.dict_response:
			if mon_dict.get('currency') == "KRW":
				if 1 == _type:
					return float(mon_dict.get('balance'))
				elif 2 == _type:
					return float(mon_dict.get('locked'))
				elif 3 == _type:
					return float(mon_dict.get('balance')) + float(mon_dict.get('locked'))
		return 0

	def recuperer_symbols(self):
		symbols = []
		for mon_dict in self.dict_response:
			symbols.append(mon_dict.get('currency'))
		return symbols

	def recuperer_symbol_info(self, _symbol):
		for mon_dict in self.dict_response:
			if mon_dict.get('currency') == _symbol:
				solde = float(mon_dict.get('balance'))
				ferme = float(mon_dict.get('locked'))
				prix_moyenne_achat = float(mon_dict.get('avg_buy_price'))

				return solde, ferme, prix_moyenne_achat
		return -1, -1, -1


class Acheter:
	def __init__(self, _symbol, _prix_courant, _somme_totale, _poids):
		self.symbol = _symbol
		self.prix_courant = _prix_courant
		self.S = _somme_totale
		self.poids = _poids

	class Diviser(Enum):
		LINEAIRE = 1
		LOG_LINEAIRE_II = 2
		LOG_LINEAIRE_I = 3
		PARABOLIQUE_II = 4
		PARABOLIQUE_I = 5
		EXPOSANT = 6
		LAPIN = 7

	def diviser(self, _pourcent_descente : float, _fois_decente : int, _facon : int):
		if self.Diviser.LINEAIRE == _facon: # n
			self.diviser_lineaire(_pourcent_descente, _fois_decente, 16777216)
		elif self.Diviser.LOG_LINEAIRE_II == _facon: # n * log(n + 3)
			self.diviser_log_lineaire(_pourcent_descente, _fois_decente, 3)
		elif self.Diviser.LOG_LINEAIRE_I == _facon: # n * log(n + 2)
			self.diviser_log_lineaire(_pourcent_descente, _fois_decente, 2)
		elif self.Diviser.PARABOLIQUE_II == _facon: # 2.5n^2 + 2.5n + 5
			self.diviser_parabolique2(_pourcent_descente, _fois_decente)
		elif self.Diviser.PARABOLIQUE_I == _facon: # n^2 - 0.5n + 1
			self.diviser_parabolique(_pourcent_descente, _fois_decente)
		elif self.Diviser.EXPOSANT == _facon: # 1.2^n
			self.diviser_exposant(_pourcent_descente, _fois_decente, 1.2)
		elif self.Diviser.LAPIN == _facon: # fibonacci varie
			self.diviser_lapin(_pourcent_descente, _fois_decente)

	def diviser_lineaire(self, _pourcent_descente, _fois_decente, _difference):
		r = _fois_decente
		h = _difference
		a = self.S / (r * ((r + 1) * h / 200 + 1))

		for n in range(1, _fois_decente + 1):
			poids_hauteur = 1 + self.poids * (n - 1)
			pn = tailler(coller(self.prix_courant), (n - 1) * (_pourcent_descente * poids_hauteur))
			qn = a * h * n / 100 + a
			self.acheter(pn, qn)

	def diviser_log_lineaire(self, _pourcent_descente, _fois_decente, _poids):
		s = 0
		for n in range(1, _fois_decente + 1):
			s += n * math.log(n + _poids)
		
		for n in range(1, _fois_decente + 1):
			poids_hauteur = 1 + self.poids * (n - 1)
			pn = tailler(coller(self.prix_courant), (n - 1) * (_pourcent_descente * poids_hauteur))
			qn = self.S * (n * math.log(n + _poids)) / s
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

	def diviser_exposant(self, _pourcent_descente, _fois_decente, _exposant): # non-recommande
		h = _fois_decente
		r = _exposant
		a = self.S * (r - 1) / (pow(r, h) - 1)

		for n in range(1, _fois_decente + 1):
			poids_hauteur = 1 + self.poids * (n - 1)
			pn = tailler(coller(self.prix_courant), (n - 1) * (_pourcent_descente * poids_hauteur))
			qn = a * pow(r, n - 1)
			self.acheter(pn, qn)

	def diviser_lapin(self, _pourcent_descente, _fois_decente): # non-recommande
		lapin = [1, 1, 2, 2, 3, 3, 5, 5, 8, 8, 13, 13, 21, 21, 34, 34, 55, 55, 89, 89, 144, 144, 233, 233, 377, 377, 810, 810, 1187, 1187] # 30
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
	def __init__(self, _symbol : str, _volume : float, _prix : float):
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
		self.t = 0

	def est_commande_vente_complete(self, _symbol : str):
		ec = ExaminerCompte()
		symbols = ec.recuperer_symbols()

		if self.count_montant_insuffissant > 300:
			imprimer(Niveau.AVERTISSEMENT,
						"Cancel the sale because the remaining sale request is not completed.")
			self.count_montant_insuffissant = 0
			self.flag_commande_vendre = False
			return True

		for symbol in symbols:
			try:
				solde, ferme, prix_moyenne_achat = ec.recuperer_symbol_info(symbol)
				montant = (solde + ferme) * prix_moyenne_achat
			except:
				time.sleep(TEMPS_DORMIR)
				return False

			if symbol == _symbol:
				if montant < 5000:
					self.count_montant_insuffissant += 1
				else:
					self.count_montant_insuffissant = 0

				if solde + ferme > 0.00001:
					return False
				else:
					break

		if self.flag_commande_vendre == False:
			return False
		else:
			self.flag_commande_vendre = False
			return True

	def vendre_a_plein(self, _symbol : str, _proportion_profit : float):
		try:
			# solde, ferme <- volume
			solde, ferme, prix_moyenne_achat = ExaminerCompte().recuperer_symbol_info(_symbol)
			if solde < 0:
				return False

			montant = (solde + ferme) * prix_moyenne_achat
			self.count_montant_insuffissant = 0

			if solde > 1000 / prix_moyenne_achat and montant > 5000: # Yay, ca pourra reperer la derniere erreur !
				if uuid_vente != '':
					Annuler().annuler_vente()
					time.sleep(TEMPS_DORMIR)
				time.sleep(TEMPS_DORMIR)

				solde, ferme, prix_moyenne_achat = ExaminerCompte().recuperer_symbol_info(_symbol)
				imprimer(Niveau.INFORMATION, 
							"Average buy price : " + str(prix_moyenne_achat) + ", sell position : " + str(tailler(prix_moyenne_achat, -1 * _proportion_profit)))
				Vendre(_symbol, solde + ferme, tailler(prix_moyenne_achat, -1 * _proportion_profit))

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
	try:
		with open("../key.txt", 'r') as f:
			CLE_ACCES = f.readline().strip()
			CLE_SECRET = f.readline().strip()
			imprimer(Niveau.INFORMATION, "CLE_ACCES : " + CLE_ACCES)
			#imprimer(Niveau.INFORMATION, "CLE_SECRET : " + CLE_SECRET)
		
		symbol = "META"
		TEMPS_INITIAL = datetime.now()

		parser = argparse.ArgumentParser(description="foo")
		parser.add_argument('-a', type=int, required=False)
		parser.add_argument('-d', type=float, required=False)
		parser.add_argument('-f', type=int, required=False)
		parser.add_argument('-p', type=float, required=False)
		parser.add_argument('-s', type=int, required=False)
		parser.add_argument('-t', type=int, required=False)
		parser.add_argument('-v', type=float, required=False)
		args = parser.parse_args()
	
		if args.a is not None:
			Annuler().annuler_precommandes(args.a)
		else:
			Annuler().annuler_precommandes(1)

		if args.d is not None:
			__proportion_divise = args.d
		else:
			__proportion_divise = 0.25

		if args.f is not None:
			__facon_achat = args.f
		else:
			__facon_achat = Acheter.Diviser.PARABOLIQUE_II

		if args.p is not None:
			__poids_divise = args.p
		else:
			__poids_divise = 0.035

		Sp = S = ExaminerCompte().recuperer_solde_krw()
		imprimer(Niveau.INFORMATION, "Available KRW : " + format(int(S), ','))
		logger_masse(S)

		if args.s is not None:
			if args.s < 30000000:
				imprimer(Niveau.ERREUR, "You have to put more than 30,000,000 won.")
				exit()
			else:
				S = int(args.s * Commission)
		else:
			S = int(S * Commission)
	
		if args.t is not None:
			__temps_timeout = args.t
		else:
			__temps_timeout = 30

		if args.v is not None:
			__position_vente = args.v
		else:
			__position_vente = 0.36


		while True:
			breakable = False
			flag_commande_vendre = False
			fault = 0

			while True:
				if breakable: 
					break

				try:
					v = Verifier(symbol)
					t = 30 + int(v.indice_ecart_relative * 1.25)
					rsi = v.trouver_rsi()
					if rsi >= 70:
						t += int((rsi - 70) / 6) + 1
					elif rsi <= 30:
						t += int((rsi - 30) / 6) - 1

					a = Acheter(symbol, v.candle.prix_courant, S, __poids_divise)
					a.diviser(__proportion_divise, t, __facon_achat)

					logger_etat(LOG_ETAT.ACHETER, symbol)
					imprimer(Niveau.INFORMATION, 
								"Relative Deviation Index : " + str(round(v.indice_ecart_relative, 2)) +
								", t = " + str(t))
					imprimer(Niveau.INFORMATION, "Buy order completed : \'" + symbol + '\'')
					
					breakable = True
					threading.Thread(target = winsound.Beep, args=(440, 500)).start()
				except Exception:
					traceback.print_exc()

			cv = ControlerVente()
			while True:
				if cv.est_commande_vente_complete(symbol):
					logger_etat(LOG_ETAT.ACCOMPLIR)
					imprimer(Niveau.SUCCES, "Sell complete. Cancel remaining buy orders.")
					break
				elif fault >= __temps_timeout:
					logger_etat(LOG_ETAT.HORS_DU_TEMPS)
					imprimer(Niveau.AVERTISSEMENT, "Timeout.")
					break

				if cv.vendre_a_plein(symbol, __position_vente):
					logger_etat(LOG_ETAT.INVESTIR, symbol)
					fault = 0
				else:
					fault += 1

			Annuler().annuler_achats()
			S = int(ExaminerCompte().recuperer_solde_krw())
			imprimer(Niveau.INFORMATION,
						"Profit : " + '{0:+,}'.format(int(S - Sp)) + ' (' + str(datetime.now() - TEMPS_INITIAL) + ')')
			logger_masse(S)
			S = int(S * Commission)
	except Exception:
		logger_etat(LOG_ETAT.ERREUR)
		traceback.print_exc()
		time.sleep(999999)