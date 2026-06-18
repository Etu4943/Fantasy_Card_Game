from state import hand, deck
from extensions import socketio
import fsocket
from card import Card
import random

def init_hand(room_code, user_id): # 7 cartes de chaque !
	for _ in range(7):
		if len(deck) > 0 :
			add_card_to_hand(room_code, user_id)

def add_card_to_hand(room_code, user_id):
	hand[room_code][user_id].append(deck[room_code].pop(0).get_data())

def init_deck(room_code):
	deck[room_code] = []
	for _ in range(7):
		deck[room_code].append(Card("farfadet", "Pouvoir 1"))
	for _ in range(7):
		deck[room_code].append(Card("dryade", "Pouvoir 2"))
	for _ in range(7):
		deck[room_code].append(Card("elfe", "Pouvoir 3"))
	for _ in range(7):
		deck[room_code].append(Card("fee", "Pouvoir 4"))
	for _ in range(7):
		deck[room_code].append(Card("gnome", "Pouvoir 5"))
	for _ in range(7):
		deck[room_code].append(Card("korrigan", "Pouvoir 6"))
	for _ in range(7):
		deck[room_code].append(Card("lutin", "Pouvoir 7"))
	random.shuffle(deck[room_code])

	

