

ROOMS = dict()

sid_to_room = dict()
user_to_sid = dict()

hand = dict()
""""
	{
		room_code {
			player_id_1 {
	
			},
			player_id_2 {
	
			}
		}
	}
"""

player_round = dict()

cards = dict()

deck = dict()

board = dict()
"""
	room_code {
		player_id {
			
		}
	}
"""

card_to_steal = dict()

last_action = dict()

game_state = dict()
"""
	{
		room_code {
			players {
				player_id_1 {
					hand[]
					board[]
					card_to_steal(INT) // Equivaut au nombre de carte qu'on peut voler (décrémente lors d'un korrigan)
				}
				player_id_2 {
					hand[]
					board[]
					card_to_steal(INT) // Equivaut au nombre de carte qu'on peut voler (décrémente lors d'un korrigan)
				}
			}
			
			deck {
				
			}
			last_action {
				cards[]
				name(STR)
			}
			player_round (CYCLE)
		}
	}
"""
