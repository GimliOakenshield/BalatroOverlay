print("Loading lib : BalaConfFile ... ", end='')

# Imports
import os
import ast
import sys
import zlib

##########################################################################
# Chemins d'accès
##########################################################################
APPDATA_PATH = os.getenv('APPDATA')
# BALATRO_SAVE_DIR = os.path.join(APPDATA_PATH, "Balatro", "1")
BALATRO_SAVE_DIR = os.path.join(APPDATA_PATH, "Balatro", "3")

##########################################################################
# Classe BalaConfFile gérant l'extraction des données depuis un fichier de config de BAlatro
##########################################################################
class BalaConfFile(object):
	def __init__(self, filePath = None):
		self.dataDict = {}
		self.filePath = filePath if filePath else None
		
		if self.filePath:
			self.loadFile()
	
	def loadFile(self, debug = True):
		# if debug : print(f"\nCharger les données depuis : {self.filePath}")
		try:
			with open(self.filePath, 'rb') as saveFile:
				decompData = zlib.decompress(saveFile.read(), wbits=-zlib.MAX_WBITS)
				obj_str = (decompData[7:].decode("utf-8").replace("[", "").replace("]", "").replace("=", ":").replace(":true", ":True").replace(":false", ":False"))
				
				tempData = ast.literal_eval(obj_str)
		except Exception as e:
			tempData = -1
		return tempData
	
	def getUpdatedData(self):
		# Garder en mémoire les données d'avant
		changes = {}
		oldData = self.dataDict.copy()
		
		# Charger les nouvelles données
		res = self.loadFile()
		if res == -1:
			return {"deleted": True}
		
		# Comparer les dictionnaires
		allKeys = set(oldData.keys()) | set(self.dataDict.keys())
		diffDict = {}
		
		# print(f"Chips présent dans OldData : {'chips' in oldData}")
		# print(f"Chips présent dans allKeys : {'chips' in allKeys}")
		
		for key in allKeys:
			if oldData.get(key) != self.dataDict.get(key):
				changes[key] = (oldData.get(key), self.dataDict.get(key))
				# if key == 'chips':
					# print(f"{key} : {oldData.get(key)} => {self.dataDict.get(key)}")
		# if changes:
			# print("_____\n")
		return changes

##########################################################################
# Classe BalaProfile gérant l'extraction des données depuis un fichier de config de BAlatro
##########################################################################
class BalaProfile(BalaConfFile):
	DECK_LIST = ['b_red', 'b_blue', 'b_yellow', 'b_green', 'b_black', 'b_magic', 'b_nebula', 'b_ghost', 'b_abandoned', 'b_checkered', 'b_zodiac', 'b_painted', 'b_anaglyph', 'b_plasma', 'b_erratic']
	
	STAKE_LIST = ['none', 'white', 'red', 'green', 'black', 'blue', 'violet', 'orange', 'gold']
	
	def __init__(self, dirPath):
		self.filePath = os.path.join(dirPath, "profile.jkr")
		super().__init__(self.filePath)
	
	def loadFile(self, debug = False):
		tempData = super().loadFile(debug)
		if tempData == -1:
			return -1
		
		# Extraire uniquement les données utiles
		self.dataDict = {}
		for deckName in BalaProfile.DECK_LIST:
			try:
				self.dataDict[deckName] = max(tempData['deck_usage'][deckName]['wins'].keys())
			except:
				self.dataDict[deckName] = None
		
		self.dataDict['Challenge']	=	tempData['progress']['challenges']['tally'] if tempData else None
		self.dataDict['TotalRounds']=	tempData['career_stats']['c_rounds'] if tempData else None
		
		# print(f"Données chargées :\n")
		# for key, value in self.dataDict.items():
			# print(f"\t{key} : {value}")
		
		# deck_stakes - Clés dispos : dict_keys([])
		# deck_usage - Clés dispos : dict_keys(['b_nebula', 'b_abandoned', 'b_anaglyph', 'b_black', 'b_ghost', 'b_plasma', 'b_erratic', 'b_magic', 'b_red', 'b_painted', 'b_blue', 'b_checkered', 'b_green', 'b_yellow', 'b_zodiac'])
		# progress - Clés dispos : dict_keys(['challenges', 'overall_of', 'joker_stickers', 'deck_stakes', 'overall_tally', 'discovered'])
		# challenge_progress - Clés dispos : dict_keys(['unlocked', 'completed'])
			# career_stats - Clés dispos : dict_keys(['c_cards_discarded', 'c_round_interest_cap_streak', 'c_jokers_sold', 'c_vouchers_bought', 'c_planetarium_used', 'c_wins', 'c_shop_rerolls', 'c_dollars_earned', 'c_playing_cards_bought', 'c_single_hand_round_streak', 'c_shop_dollars_spent', 'c_face_cards_played', 'c_planets_bought', 'c_tarots_bought', 'c_tarot_reading_used', 'c_rounds', 'c_hands_played', 'c_cards_played', 'c_losses', 'c_cards_sold'])

##########################################################################
# Classe BalaSave gérant l'extraction des données depuis un fichier de config de BAlatro
##########################################################################
class BalaSave(BalaConfFile):
	def __init__(self, dirPath):
		self.filePath = os.path.join(dirPath, "save.jkr")
		super().__init__(self.filePath)
	
	def loadFile(self, debug = False):
		tempData = super().loadFile(debug)
		if tempData == -1:
			return -1
		
		# print(f"{tempData}")
		# Extraire uniquement les données utiles
		self.dataDict = {}
		self.dataDict['seed'] = tempData['GAME']['pseudorandom']['seed'] if tempData else None
		self.dataDict['round'] = tempData['GAME']['round'] if tempData else -1
		self.dataDict['chips'] = tempData['GAME']['chips'] if tempData else False
		self.dataDict['won'] = tempData['GAME']['won'] if tempData else False
		self.dataDict['deckName'] = tempData['BACK']['name'] if tempData else None
		self.dataDict['stake'] = tempData['GAME']['stake'] if tempData else None
		
		# print(f"Chips {self.dataDict['chips']}")
		# print(f"Stake {self.dataDict['stake']}")
		
		# self.dataDict['chips_text'] = tempData['GAME']['chips_text'] if tempData else False
		# self.dataDict['selected_back'] = tempData['GAME']['selected_back'] if tempData else False
		# # self.dataDict['hands'] = tempData['GAME']['hands'] if tempData else False
		# # self.dataDict['hand_usage'] = tempData['GAME']['hand_usage'] if tempData else False
		# self.dataDict['sort'] = tempData['GAME']['sort'] if tempData else False
		# # self.dataDict['cards_played'] = tempData['GAME']['cards_played'] if tempData else False
		# self.dataDict['pack_size'] = tempData['GAME']['pack_size'] if tempData else False
		# self.dataDict['previous_round'] = tempData['GAME']['previous_round'] if tempData else False
		# self.dataDict['last_blind'] = tempData['GAME']['last_blind'] if tempData else False
		# self.dataDict['modifiers'] = tempData['GAME']['modifiers'] if tempData else False
		# self.dataDict['shop'] = tempData['GAME']['shop'] if tempData else False
		# self.dataDict['skips'] = tempData['GAME']['skips'] if tempData else False
		# self.dataDict['selected_back_key'] = tempData['GAME']['selected_back_key'] if tempData else False
		# self.dataDict['unused_discards'] = tempData['GAME']['unused_discards'] if tempData else False
		# self.dataDict['hands_played'] = tempData['GAME']['hands_played'] if tempData else False
		# self.dataDict['round_resets'] = tempData['GAME']['round_resets'] if tempData else False
		# self.dataDict['blind'] = tempData['GAME']['blind'] if tempData else False
		# self.dataDict['joker_usage'] = tempData['GAME']['joker_usage'] if tempData else False
		# self.dataDict['ecto_minus'] = tempData['GAME']['ecto_minus'] if tempData else False
		
		# self.dataDict['current_round'] = tempData['GAME']['current_round'] if tempData else -1
		# self.dataDict['current_hand'] = tempData['GAME']['current_round']['current_hand'] if tempData else -1
		# self.dataDict['chip_total'] = tempData['GAME']['current_round']['current_hand']['chip_total'] if tempData else -1
		# self.dataDict['mult'] = tempData['GAME']['current_round']['current_hand']['mult'] if tempData else -1
		# self.dataDict['chips_current_round'] = tempData['GAME']['current_round']['current_hand']['chips'] if tempData else -1
		# self.dataDict['mult_text'] = tempData['GAME']['current_round']['current_hand']['mult_text'] if tempData else -1
		# self.dataDict['chip_total_text'] = tempData['GAME']['current_round']['current_hand']['chip_total_text'] if tempData else -1
		
		# self.dataDict['round_scores'] = tempData['GAME']['round_scores'] if tempData else False
		# self.dataDict['cards_discarded'] = tempData['GAME']['round_scores']['cards_discarded'] if tempData else False
		
		# self.dataDict['deck'] = tempData['cardAreas']['deck'] if tempData else False
		# self.dataDict['hand'] = tempData['cardAreas']['hand'] if tempData else False
		# for key, value in tempData['cardAreas']['deck']['cards'][1].items():
		# # for key, value in tempData['cardAreas']['deck']['cards'].items():
			# # print(f"\t{key} : {value.keys()}")
			# print(f"\t{key} : {value}")
		
		# print(f"Données chargées :\n")
		# for key, value in tempData.items():
			# try:
				# print(f"\t{key} : ")
				# for subkey, subvalue in value.items():
					# print(f"\t\t{subkey} : {subvalue.keys()}")
			# except:
				# print(f"\t{key} : {value}")
		
		# ['BACK', 'cardAreas', 'BLIND', 'tags', 'STATE', 'GAME', 'VERSION']
	
			# cardAreas : 
			# jokers : dict_keys(['cards', 'config'])
			# consumeables : dict_keys(['cards', 'config'])
			# deck : dict_keys(['cards', 'config'])
			# hand : dict_keys(['cards', 'config'])
				# 'deck' / cards : 
				# 2 : dict_keys(['base_cost', 'sprite_facing', 'cost', 'params', 'rank', 'extra_cost', 'playing_card', 'sort_id', 'facing', 'label', 'debuff', 'base', 'save_fields', 'sell_cost', 'ability'])
				
					# base_cost : 1
				# sprite_facing : back
				# cost : 1
				# params : {}
				# rank : 1
				# extra_cost : 0
				# playing_card : 50
				# sort_id : 32
				# facing : back
				# label : Base Card
				# debuff : False
				# base : {'nominal': 7, 'suit': 'Diamonds', 'id': 7, 'colour': {4: 1, 1: 0.88627450980392, 2: 0.56470588235294, 3: 0}, 'suit_nominal_original': 0.001, 'face_nominal': 0, 'value': '7', 'original_value': '7', 'suit_nominal': 0.01, 'name': '7 of Diamonds', 'times_played': 1}
				# save_fields : {'card': 'D_7', 'center': 'c_base'}
				# sell_cost : 1
				# ability : {'bonus': 0, 'h_mult': 0, 'hands_played_at_create': 0
		
		# ['GAME']['pseudorandom']['seed']
		# ['GAME']['round']
		# GAME - Clés dispos : dict_keys(['round_scores', 'edition_rate', 'tarot_rate', 'rental_rate', 'previous_round', 'used_jokers', 'round', 'current_round', 'round_bonus', 'consumeable_usage', 'tag_tally', 'voucher_text', 'last_blind', 'planet_rate', 'starting_deck_size', 'selected_back', 'hands', 'tags', 'stake', 'win_ante', 'inflation', 'perishable_rounds', 'base_reroll_cost', 'interest_amount', 'spectral_rate', 'banned_keys', 'joker_rate', 'used_vouchers', 'modifiers', 'shop', 'skips', 'current_boss_streak', 'won', 'bankrupt_at', 'selected_back_key', 'chips_text', 'unused_discards', 'hands_played', 'discount_percent', 'STOP_USE', 'chips', 'round_resets', 'max_jokers', 'dollars', 'perscribed_bosses', 'sort', 'consumeable_buffer', 'pool_flags', 'blind', 'joker_usage', 'cards_played', 'pseudorandom', 'interest_cap', 'pack_size', 'hand_usage', 'ecto_minus', 'probabilities', 'playing_card_rate', 'bosses_used', 'joker_buffer', 'starting_params'])
		
		# round_scores : {'furthest_round': {'label': 'Round', 'amt': 1}, 'cards_played': {'label': 'Cards Played', 'amt': 10}, 'hand': {'label': 'Best Hand', 'amt': 280}, 'cards_discarded': {'label': 'Cards Discarded', 'amt': 8}, 'furthest_ante': {'label': 'Ante', 'amt': 1}, 'times_rerolled': {'label': 'Times Rerolled', 'amt': 0}, 'poker_hand': {'label': 'Most Played Hand', 'amt': 0}, 'cards_purchased': {'label': 'Cards Purchased', 'amt': 0}, 'new_collection': {'label': 'New Discoveries', 'amt': 0}} 
		
		# current_round : {'reroll_cost_increase': 0, 'jokers_purchased': 0, 'reroll_cost': 5, 'discards_left': 2, 'dollars_to_be_earned': '', 'discards_used': 2, 'hands_played': 2, 'dollars': 4, 'voucher': 'v_directors_cut', 'round_dollars': 0, 'mail_card': {'id': 12, 'rank': 'Queen'}, 'cards_flipped': 0, 'current_hand': {'chip_text': '0', 'handname_text': '', 'handname': '', 'chip_total': 0, 'mult': 0, 'mult_text': '0', 'chip_total_text': '', 'hand_level': '', 'chips': 0}, 'idol_card': {'suit': 'Diamonds', 'rank': 'Ace', 'id': 14}, 'most_played_poker_hand': 'High Card', 'ancient_card': {'suit': 'Clubs'}, 'round_text': 'Round ', 'free_rerolls': 0, 'used_packs': {2: 'p_buffoon_normal_1', 1: 'p_buffoon_normal_1'}, 'hands_left': 4, 'castle_card': {'suit': 'Hearts'}}

print("OK")

if __name__ == "__main__":
	##########################################################################
	# Exécution
	##########################################################################
	saveFile = BalaSave(BalaSave.filePath)
	print(f"Save : {saveFile.dataDict}")

	proFile = BalaProfile(BalaProfile.filePath)
	print(f"Profil : {proFile.dataDict}")































