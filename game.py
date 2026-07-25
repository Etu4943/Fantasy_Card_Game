from state import hand, deck
from state import game_state as GS
from extensions import socketio
import fsocket
from card import Card
import random
import uuid

NB_PEOPLE = 3
NB_CARD_BY_HAND = 7

CARDS = [
	["farfadet", "Pouvoir 1"],
	["dryade", "Pouvoir 2"],
	["elfe", "Pouvoir 3"],
	# Fee disabled until I found a better architecture 
	# Like I need to be able to play it while the opponent is playing
	# ["fee", "Pouvoir 4"],
	["gnome", "Pouvoir 5"],
	["korrigan", "Pouvoir 6"],
	["lutin", "Pouvoir 7"]
]

def init_hand(room_code, user_id): # 7 cartes de chaque !
	for _ in range(NB_CARD_BY_HAND):
		add_card_to_hand(room_code, user_id)

def add_card_to_hand(room_code, user_id):
	if len(GS[room_code]["deck"]) > 0 :
		# hand[room_code][user_id].append(deck[room_code].pop(0).get_data())
		GS[room_code]["players"][user_id]["hand"].append(GS[room_code]["deck"].pop(0).get_data())

def init_deck(room_code):
	# deck[room_code] = []
	GS[room_code]["deck"] = []
	for card in CARDS :
		for _ in range(NB_PEOPLE) :
			GS[room_code]["deck"].append(Card(card[0], card[1], str(uuid.uuid4())))
			# deck[room_code].append(Card(card[0], card[1], str(uuid.uuid4())))
	random.shuffle(GS[room_code]["deck"])

	

