print("\n_____\nDébut du script")

##########################################################################
# Imports
##########################################################################
import os
import sys
import time
import json

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from dataclasses import dataclass, asdict, field

from BalaConfFile import BalaSave
from BalaConfFile import BalaProfile
from BalatroFileObserver import BalatroFileObserver

##########################################################################
# Chemins d'accès
##########################################################################
APPDATA_PATH = os.getenv('APPDATA')
BALATRO_SAVE_DIR = os.path.join(APPDATA_PATH, "Balatro", "1")
# BALATRO_SAVE_DIR = os.path.join(APPDATA_PATH, "Balatro", "3")
JSON_SAVE_DIR = os.path.join(os.getcwd(), "data")
JSON_SAVE_PATH = os.path.join(JSON_SAVE_DIR, "save.json")

##########################################################################
# App pour le serveur flask
##########################################################################
app = Flask(__name__)

##########################################################################
# Constantes
##########################################################################
deckList = ['b_red', 'b_blue', 'b_yellow', 'b_green', 'b_black', 'b_magic', 'b_nebula', 'b_ghost', 'b_abandoned', 'b_checkered', 'b_zodiac', 'b_painted', 'b_anaglyph', 'b_plasma', 'b_erratic']

##########################################################################
# Classes
##########################################################################
@dataclass
class GameState:
	won: int = 0
	curTry: int = 0
	curChips: int = 0
	curStake: int = 0
	curReset: int = 0
	Challenge: int = 0
	TotalRounds: int = 0
	curMaxScore: int = 0
	deck: dict = field(default_factory=dict)

	def to_dict(self):
		return asdict(self)

class BalaMain():
	def __init__(self):
		# Démarrage du serveur Flask
		self.socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
		
		# Création des instances de fichiers de config Balatro
		self.saveFile = BalaSave(BALATRO_SAVE_DIR)
		self.proFile = BalaProfile(BALATRO_SAVE_DIR)
		self.filesList = [self.saveFile, self.proFile]
		
		# Variables d'instances pour track les resets/try
		self.state = GameState()
		self.loadJson(JSON_SAVE_PATH)
		
		# Création de l'instance du watchddog
		self.balaFileHandler = BalatroFileObserver(BALATRO_SAVE_DIR)
		self.balaFileHandler.start()
		
		# Gestionnaires d'événements WebSocket : Envoyer les infos en cours quand une page se connecte
		@self.socketio.on('connect')
		def handle_connect():
			self.sendUpdtCounters()
		
		@self.socketio.on('resetCounters')
		def handle_resetCounters():
			result = self.resetCounters()
			self.socketio.emit('counters_updated', result)
		
		@self.socketio.on('request_initial_data')
		def handle_requestData():
			self.sendInitDeck()
	
	######################################################################
	# Gestion du serveur
	######################################################################
	def start(self):
		# Démarrer le serveur Flask et la surveillance des fichiers
		self.socketio.start_background_task(self.getUpdatesOnEvent)
		self.socketio.run(app, debug=False, allow_unsafe_werkzeug=True)
	
	def sendInitDeck(self):
		for deckName in BalaProfile.DECK_LIST:
			stakeLevel = self.state.deck[deckName]
			self.sendUpdtDeck(deckName, stakeLevel)
		self.sendUpdtDeck('b_challenge', self.proFile.dataDict['Challenge'])
	
	def sendUpdtMaxScore(self):
		if self.state.curMaxScore < 1e12:
			dispScore = f"{self.state.curMaxScore:,}"
		else:
			dispScore = f"{self.state.curMaxScore:.3E}".replace("+", "").replace("E", "e")
		print(f"Update max score : {dispScore} - {self.state.curStake =}")
		print(f"Update max score : {dispScore} - {BalaProfile.STAKE_LIST[self.state.curStake]}")
		self.socketio.emit('new_max_score', {'score': dispScore, 'stake': BalaProfile.STAKE_LIST[self.state.curStake]}, namespace='/')
	
	def sendUpdtDeck(self, deckName, stakeLevel):
		print(f"Update deck : {deckName} - {stakeLevel}")
		try:
			self.socketio.emit('new_deck', {'deck': deckName, 'stake': stakeLevel, 'stakeName': BalaProfile.STAKE_LIST[stakeLevel]}, namespace='/')
		except:
			self.socketio.emit('new_deck', {'deck': deckName, 'stake': stakeLevel}, namespace='/')
	
	def sendUpdtCounters(self):
		self.socketio.emit('new_try', {'value': self.state.curTry}, namespace='/')
		self.socketio.emit('new_data', {'value': self.state.curReset}, namespace='/')
	
	######################################################################
	# Gestion du fichier de config
	######################################################################
	def loadJson(self, saveFilePath):
		# Charger les données depuis un fichier JSON
		# Valeurs par défaut pour chaque champ
		default_values = {
			'won': False,
			'curTry': 0,
			'curChips': 0,
			'curStake': 0,
			'curReset': 0,
			'curMaxScore': 0,
		}
		
		# Charger les données depuis le JSON
		with open(saveFilePath, 'r') as saveDataFile:
			res = json.load(saveDataFile)
			
			# Lire les données si elles existent, sinon garder la valeur par défaut.
			for key, default in default_values.items():
				setattr(self.state, key, res.get(key, default))
			
			self.state.deck = {deckName: res['deck'].get(deckName, 0) for deckName in deckList}
			print(f"{self.state.deck =}")
			print(f"{res.keys() =}")
		
		# Si on a aucune donnée pour les decks, il faut aller les chercher
		if all(value is None for value in self.state.deck.values()):
			for key, value in {k: v for k, v in self.proFile.dataDict.items() if k.startswith('b_')}.items():
				self.state.deck[key] = value
	
	######################################################################
	# Méthodes de classe
	######################################################################
	def saveCounters(self):
		with open(JSON_SAVE_PATH, 'w') as saveDataFile:
			json.dump(self.state.to_dict(), saveDataFile, indent = 4)
	
	def resetCounters(self):
		self.state.won = False
		self.state.curTry = 0
		self.state.curChips = 0
		self.state.curReset = 0
		self.state.curStake = 1
		self.state.curMaxScore = 0
		self.saveCounters()
		self.sendUpdtMaxScore()
		self.sendUpdtCounters()
	
	def newStake(self, stake):
		print(f"\nC'est une nouvelle difficulté !\n{stake =}")
		self.state.curStake = stake
	
	def newRound(self, prevRound, curRound):
		self.state.curChips = 0
		if curRound == 1:
			print("On vient d'entrer dans le premier combat !\nJ'incrément le compteur d'essais.")
			self.state.curTry += 1
		
		# Envoyer les infos vers la page web
		self.sendUpdtCounters()
	
	def newGame(self, seed):
		print(f"\nC'est une nouvelle partie !\n{seed =}")
		# Si la partie précédente a été gagnée : On remet les compteurs à Zéro
		if self.state.won:
			self.resetCounters()
		else:
			# Sinon on incrémente le compteur de resets et on reset les compteurs de chips
			self.state.curChips = 0
			self.state.curReset += 1
			self.state.curMaxScore = 0
			self.sendUpdtMaxScore()
		
		# Envoyer les infos vers la page web
		self.sendUpdtCounters()
	
	def gameWon(self):
		print(f"\nC'est une Victoire !")
		self.state.won = True
	
	def gameEnd(self):
		print(f"\nC'est une fin de partie ! {self.state.won =}")
	
	def chipsScored(self, prevChips, newChips):
		curScore = newChips - self.state.curChips
		self.state.curChips = newChips
		if curScore > self.state.curMaxScore:
			self.state.curMaxScore = curScore
			self.sendUpdtMaxScore()
	
	######################################################################
	# Boucle de traitement des infos en continu
	######################################################################
	def getUpdatesOnEvent(self):
		while True:
			# On attend que la classe secondaire ait fini son traitement
			self.balaFileHandler.event.wait()

			# On récupère les données de la classe secondaire
			filePath = self.balaFileHandler.queue.get()
			confFile = next((x for x in self.filesList if x.filePath == filePath), None)
			# print(f"{filePath =}")
			# print(f"\n-----\n{confFile =}")
			# for x in self.filesList:
				# print(f"{x.filePath =}")
			
			# Check si c'est un fichier qu'on traque, sinon on attend à nouveau une mise à jour de fichier
			if confFile:
				self.extractData(confFile)
	
	def extractData(self, file):
		# Extraction des données du fichier mis à jour
		# S'il s'agit d'un des fichiers qu'on surveille, on interroge les classes concernées
		# print(f"Extraire les données de {file}")
		res = file.getUpdatedData()
		
		# En fonction de ce que l'on a trouvé dans le fichier => Exécuter les bonnes fonctions
		if 'deleted' in res:
			self.gameEnd()
		
		if 'stake' in res:
			self.newStake(stake = res['stake'][1])
		
		if 'seed' in res:
			self.newGame(seed = res['seed'][1])
		
		if 'round' in res:
			self.newRound(res['round'][0], res['round'][1])
		
		if 'won' in res and res['won'][1]:
			self.gameWon()
		
		if 'chips' in res:
			self.chipsScored(res['chips'][0], res['chips'][1])
		
		# Chercher si l'on vient de trouver un Deck "mis à jour"
		deckNames = BalaProfile.DECK_LIST & res.keys()
		if deckNames:
			if len(deckNames) != 1:
				print(f"Je ne suis pas sensé trouver plusieurs decks en même temps !")
				raise
			deckName = next(iter(deckNames))
			self.sendUpdtDeck(deckName, res[deckName][1])
		
		# Chercher si l'on vient de gagner un challenge
		if 'Challenge' in res:
			self.sendUpdtDeck('b_challenge', res['Challenge'])
		
		# Enregistrer dans le JSON et l'envoyer à la page
		self.saveCounters()

##########################################################################
# Servir le template au nevigateur
##########################################################################
@app.route('/')
def index():
	return render_template('index.html')

##########################################################################
# Route pour l'interface administrateur
##########################################################################
@app.route('/admin')
def admin():
	return render_template('admin.html')

##########################################################################
# Route pour l'interface max score
##########################################################################
@app.route('/maxScore')
def maxScore():
	return render_template('maxScore.html')

##########################################################################
# Route pour l'affichage des decks
##########################################################################
@app.route('/decks')
def decks():
	decl_list = BalaProfile.DECK_LIST.copy()
	decl_list.append('b_challenge')
	return render_template('decks.html', deck_list = decl_list, stake_list = BalaProfile.STAKE_LIST)

# if __name__ == "__main__":
main = BalaMain()

main.start()
main.balaFileHandler.join()

print(f"\n_____\nFin !")






























