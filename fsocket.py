from extensions import socketio
from state import ROOMS, sid_to_room, hand, deck, board, player_round

from flask import request, session, redirect
from flask_socketio import join_room, leave_room, send, SocketIO, emit

from game import init_hand, add_card_to_hand, init_deck
from card import Card


from itertools import cycle
import threading

# user_id -> Timer en cours (déconnexion en attente)
_pending_disconnects: dict[str, threading.Timer] = {}
DISCONNECT_GRACE = 5  # secondes

_waiting_players: set[str] = set()

@socketio.on('message')
def handle_message(data):
    print('received message: ', data)

@socketio.on('join')
def handle_join(data):
    room_code = data.get('room_code')
    user_id = session.get('user_id')
    if room_code not in ROOMS.keys() :
        session['room'] = None
        return redirect("/")
    # Annule une déco en attente pour ce joueur (= refresh)
    if user_id in _pending_disconnects:
        _pending_disconnects.pop(user_id).cancel()
        print(f"{user_id} reconnected, disconnect cancelled")
        sid_to_room[request.sid] = (room_code, user_id)
        diffuse_hand()          # restitue sa main sans réinitialiser
        return

    join_room(room_code)

    ROOMS[room_code]["players"].add(user_id)
    sid_to_room[request.sid] = (room_code, user_id)



    # Quand tu rejoins une partie, il faut lui créer et lui attribuer une main
    
    if room_code not in hand.keys() :
        board[room_code] = dict()
        hand[room_code] = dict()

    player_round[room_code] = cycle(ROOMS[room_code]["players"])
    ROOMS[room_code]["current_player_id"] = next(player_round[room_code]) # Arbitrary. Maybe random later
    hand[room_code][user_id] = []
    board[room_code][user_id] = []
    if room_code not in deck.keys() :
        init_deck(room_code)
    init_hand(room_code, user_id)
    #socketio.emit('message', {'message':f'{session.get("username")} has entered the game !'}, room=room_code, include_self=False)
    diffuse_message({'message' : "has enter the chat"})

@socketio.on('disconnect')
def handle_disconnect():
    entry = sid_to_room.pop(request.sid, None)
    if entry is None:
        return

    room_code, user_id = entry

    if user_id in _waiting_players:        # ← simple transit, on ignore
        _waiting_players.discard(user_id)
        return

    # Déconnexion douce : on attend avant d'agir
    def _do_remove():
        _pending_disconnects.pop(user_id, None)
        remove_player(room_code, user_id)
        # Notifie la room que le joueur est vraiment parti
        socketio.emit(
            'recieve_message',
            {'user': 'System', 'message': f'{user_id} has left the game.'},
            room=room_code
        )
        print(f"{user_id} truly disconnected from {room_code}")
    timer = threading.Timer(DISCONNECT_GRACE, _do_remove)
    _pending_disconnects[user_id] = timer
    timer.start()

@socketio.on('leave')
def handle_leave():
    entry = sid_to_room.pop(request.sid, None)
    if entry is None :
        return
    room_code, user_id = entry
    #socketio.emit('message', {'message':f'{session.get("username")} has quit the game !'}, room=room_code, include_self=False)

    if user_id in _pending_disconnects:
        _pending_disconnects.pop(user_id).cancel()
    diffuse_message({'message': "has left the chat"}, room_code)
    remove_player(room_code, user_id)
    leave_room(room_code)
    emit('left_room')


def remove_player(room_code, user_id):
    if room_code in ROOMS:
        ROOMS[room_code]['players'].discard(user_id)
        if not ROOMS[room_code]['players']:
            print("No more players. Lets NUKE IT")
            del board[room_code]
            del hand[room_code]
            del player_round[room_code]
            del ROOMS[room_code]


@socketio.on('send_message')
def handle_send_message(data):
    diffuse_message(data)

def diffuse_message(data, def_room_code=None):
    entry = sid_to_room.get(request.sid, None)
    if entry is None :
        room_code = def_room_code # Au cas où le message vient du fait qu'il est parti, on peut plus récupérer entry
    else :
        room_code, user_id = entry
    if "user" in data.keys() :
        sender = data["user"]
    else :
        sender = session.get("username")
    emit('recieve_message', {'user': sender,'message' : data['message']}, room=room_code)

@socketio.on("ask_hand")
def handle_ask_hand():
    diffuse_hand()

def diffuse_board(rsid=None):
    if rsid is None :
        entry = sid_to_room.get(request.sid, None)
        rsid = request.sid
    else :
        entry = sid_to_room.get(rsid, None)
    if entry is None :
        return
    room_code, user_id = entry

    # print(board[room_code][user_id])

    board[room_code][user_id] = sorted(board[room_code][user_id], key=lambda d: d['name'])

    emit("board", board[room_code][user_id], to=rsid)
    # board_to_opponent = board_for_opponent(room_code, user_id)
    emit("opponent_board", sorted(board[room_code][user_id], key=lambda d: d['name'], reverse=True), room=room_code, include_self=False)

def diffuse_hand(rsid=None):
    if rsid is None : # If i call diffuse_hand from this code like hand_play
        entry = sid_to_room.get(request.sid, None)
    else :
        entry = sid_to_room.get(rsid, None)

    if entry is None :
        return
    room_code, user_id = entry
    
    emit("hand", hand[room_code][user_id], to=request.sid) # Envoit uniquement les cartes au joueur concerné

    """"
        I need to display the opponent card, with the ability to steal them (so I have to be able to identify them, so I need ID)
    """
    hand_to_opponent = hand_for_opponent(room_code, user_id)
    # print(hand_to_opponent)
    emit("opponent_hand", hand[room_code][user_id], room=room_code, include_self=False)


"""
    This function is for the first connection of the second player.
    Sinc we display the opponent's hand everytime he displeys its own, 
    at the connection of the second user, it didn't display the first pzerson's hand.
    So when the page is fully charged, it asked for the opponent's hand.
"""
@socketio.on("ask_opponent_hand")
def handle_ask_opponent_hand():
    entry = sid_to_room.get(request.sid, None)

    if entry is None :
        return

    room_code, user_id = entry
    players_id_left_set = (ROOMS[room_code]["players"] - {user_id})
    if players_id_left_set ==  0:
        return
    opponent_id = (ROOMS[room_code]["players"] - {user_id}).pop()

    hand_to_opponent = hand_for_opponent(room_code, opponent_id)
    emit("opponent_hand", hand_to_opponent, to=request.sid)
    # print(opponent_id) #Works !


def hand_for_opponent(room_code, user_id):
    hand_to_opponent = []
    for card in hand[room_code][user_id] :
        hand_to_opponent.append({"id":card["id"]})
    return hand_to_opponent

def board_for_opponent(room_code, user_id):
    board_to_opponent = []
    for card in board[room_code][user_id] :
        board_to_opponent.append({"id":card["id"]})
    return board_to_opponent






@socketio.on("draw_a_card")
def handle_draw_a_card():

    room_code, user_id = (session.get("room"), session.get("user_id"))
    add_card_to_hand(room_code, user_id)
    draw_card(room_code, user_id)
    if len(deck[room_code]) == 0 :
        emit("empty_deck", room=room_code)


def draw_card(room_code, user_id):
    diffuse_hand()


@socketio.on("play")
def hand_play(card_id):
    
    entry = sid_to_room.get(request.sid, None)
    if entry is None :
        return

    room_code, user_id = entry

    if card_id not in [card["id"] for card in hand[room_code][user_id]] :
        diffuse_message({"user": "system", "message":"CAUGHT CHEATING !"})
        return

    if ROOMS[room_code]["current_player_id"] != user_id :
        print(f"Current player : {ROOMS[room_code]["current_player_id"]}")
        return
    ROOMS[room_code]["current_player_id"] = next(player_round[room_code])
    selected_card = [card for card in hand[room_code][user_id] if card["id"] == card_id][0]

    hand[room_code][user_id].remove(selected_card)
    board[room_code][user_id].append(selected_card)

    if selected_card["name"] == "lutin" :
        opponent_id = get_opponent_id(room_code, user_id)
        hand[room_code][user_id], hand[room_code][opponent_id] = hand[room_code][opponent_id],hand[room_code][user_id]
    diffuse_hand(request.sid)
    diffuse_board(request.sid)
    

def get_opponent_id(room_code, user_id):
    return (ROOMS[room_code]["players"] - {user_id}).pop()





