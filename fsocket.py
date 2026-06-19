from extensions import socketio
from state import ROOMS, sid_to_room, hand, deck

from flask import request, session, redirect
from flask_socketio import join_room, leave_room, send, SocketIO, emit

from game import init_hand, add_card_to_hand, init_deck
from card import Card



import threading

# user_id -> Timer en cours (déconnexion en attente)
_pending_disconnects: dict[str, threading.Timer] = {}
DISCONNECT_GRACE = 5  # secondes

@socketio.on('message')
def handle_message(data):
    print('received message: ', data)

@socketio.on('join')
def handle_join(data):
    room_code = data.get('room_code')
    user_id = session.get('user_id')
    if room_code not in ROOMS.keys() :
        session['room'] = None
        redirect("/")
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
        hand[room_code] = dict()
    hand[room_code][user_id] = []
    
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
    emit('recieve_message', {'user': session.get('username'),'message' : data['message']}, room=room_code)

@socketio.on("ask_hand")
def handle_ask_hand():
    diffuse_hand()

def diffuse_hand():
    entry = sid_to_room.get(request.sid, None)
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






@socketio.on("draw_a_card")
def handle_draw_a_card():

    room_code, user_id = (session.get("room"), session.get("user_id"))
    add_card_to_hand(room_code, user_id)
    draw_card(room_code, user_id)
    if len(deck[room_code]) == 0 :
        emit("empty_deck", room=room_code)


def draw_card(room_code, user_id):
    diffuse_hand()