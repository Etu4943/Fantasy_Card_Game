from state import hand
from extensions import socketio
import fsocket


def init_hand(room_code, user_id):
	hand[room_code][user_id].append("c1")
	hand[room_code][user_id].append("c2")
	hand[room_code][user_id].append("c3")

