from extensions import socketio
from state import ROOMS, sid_to_room, hand, deck, board, player_round, card_to_steal, last_action

from flask import request, session, redirect
from flask_socketio import join_room, leave_room, send, SocketIO, emit

from game import init_hand, add_card_to_hand, init_deck
from card import Card


from itertools import cycle
import threading
import random

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
        card_to_steal[room_code] = dict()
        last_action[room_code] = dict()
        last_action[room_code]["cards"] = []
        last_action[room_code]["name"] = ""
    card_to_steal[room_code][user_id] = 0

    if len(ROOMS[room_code]["players"]) == 1 :
        player_round[room_code] = cycle([-2,-1]) # can't play while there isn't a second player
    else :
        player_round[room_code] = cycle(ROOMS[room_code]["players"])
        for _ in range(random.randint(1, 10)) :
            ROOMS[room_code]["current_player_id"] = next(player_round[room_code]) # Here is the randomization
        # Here is the beginning of the game.
        emit("deblur", room=room_code)
        if ROOMS[room_code]["current_player_id"] == user_id :
            emit("highlight_deck", to=request.sid)
        else :
            emit("highlight_deck", room=room_code, include_self=False)
        toggle_round_player(room_code, user_id)

    hand[room_code][user_id] = []
    board[room_code][user_id] = []
    if room_code not in deck.keys() :
        init_deck(room_code)
    init_hand(room_code, user_id)
    #socketio.emit('message', {'message':f'{session.get("username")} has entered the game !'}, room=room_code, include_self=False)
    diffuse_message({'message' : "has enter the chat"})

def toggle_round_player(room_code, user_id):
    emit("set_round", ROOMS[room_code]["current_player_id"], room=room_code)




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
        # print(f"{user_id} truly disconnected from {room_code}")
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

@socketio.on("ask_board")
def handle_ask_board():
    diffuse_board()

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
    
    # print(f"Room_code : {room_code} - user_id : {user_id}")
    emit("hand", hand[room_code][user_id], to=request.sid) # Envoit uniquement les cartes au joueur concerné

    """"
        I need to display the opponent card, with the ability to steal them (so I have to be able to identify them, so I need ID)
    """
    if len(ROOMS[room_code]["players"]) > 1 :
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
    
    if len(ROOMS[room_code]["players"]) ==  1:
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
    print("Want to draw a card")
    room_code, user_id = (session.get("room"), session.get("user_id"))
    add_card_to_hand(room_code, user_id)
    draw_card(room_code, user_id)
    if len(deck[room_code]) == 0 :
        emit("empty_deck", room=room_code)


def draw_card(room_code, user_id):
    diffuse_hand()

def highlight_board(rsid):
    emit("highlight_board",to=rsid)

def highlight_opponent_board(rsid):
    emit("highlight_opponent_board",to=rsid)

def highlight_opponent_hand(rsid):
    emit("highlight_opponent_hand",to=rsid)



@socketio.on("play")
def hand_play(data):
    card_id = data["card_id"]
    is_from_elfe = data["is_from_elfe"]

    entry = sid_to_room.get(request.sid, None)
    if entry is None :
        return

    room_code, user_id = entry
    opponent_id = get_opponent_id(room_code, user_id)
    if is_from_elfe :
        if data["card_id"] not in [card["id"] for card in board[room_code][user_id]] :
            diffuse_message({"user": "system", "message":"CAUGHT CHEATING !"})
            return
    else :
        if data["card_id"] not in [card["id"] for card in hand[room_code][user_id]] :
            diffuse_message({"user": "system", "message":"CAUGHT CHEATING !"})
            return

    if ROOMS[room_code]["current_player_id"] != user_id :
        # print(f"Current player : {ROOMS[room_code]["current_player_id"]}")
        print("Not your turn !")
        return
    
    if is_from_elfe :
        selected_card = [card for card in board[room_code][user_id] if card["id"] == card_id][0]
    else :
        selected_card = [card for card in hand[room_code][user_id] if card["id"] == card_id][0]

    if not data["is_from_elfe"] :
        hand[room_code][user_id].remove(selected_card)
        board[room_code][user_id].append(selected_card)

    if selected_card["name"] == "lutin" :
        last_action[room_code]["name"] = "lutin"
        hand[room_code][user_id], hand[room_code][opponent_id] = hand[room_code][opponent_id],hand[room_code][user_id]

    elif selected_card["name"] == "farfadet" :
        last_action[room_code]["name"] = "farfadet"
        board[room_code][user_id],board[room_code][opponent_id] = board[room_code][opponent_id],board[room_code][user_id]
        last_action[room_code]["name"] = "farfadet"

    elif selected_card["name"] == "gnome" :
        last_action[room_code]["name"] = "gnome"
        for _ in range(2) :
            handle_draw_a_card()



    elif selected_card["name"] == "elfe" :
        if len([ card for card in board[room_code][user_id] if card["name"] != "elfe"]) != 0 :
            # If there is no card on board to replay
            # 1 because the elfe card is already "played" on backend 
            highlight_board(request.sid)
            return
        else :
            pass

    elif selected_card["name"] == "dryade":
        if len(board[room_code][opponent_id]) != 0 :
            last_action[room_code]["name"] = "dryade"
            highlight_opponent_board(request.sid)
            return
        else :
            pass

    elif selected_card["name"] == "fee":
        name = last_action[room_code]["name"]

        if name == "farfadet" :
            board[room_code][user_id].remove(selected_card)
            board[room_code][user_id], board[room_code][opponent_id] = board[room_code][opponent_id], board[room_code][user_id]
            board[room_code][user_id].append(selected_card) # Because in real life, you "refuse" the action by putting this in your board
        elif name == "lutin" :
            hand[room_code][user_id], hand[room_code][opponent_id] = hand[room_code][opponent_id], hand[room_code][user_id]
        elif name == "dryade" :
            for card in last_action[room_code]["cards"] :
                board[room_code][opponent_id].remove(card) 
                board[room_code][user_id].append(card)
        elif name == "korrigan" :
            for card in last_action[room_code]["cards"] :
                hand[room_code][opponent_id].remove(card)
                hand[room_code][user_id].append(card)
        last_action[room_code] = dict()
        last_action[room_code]["name"] = []
        last_action[room_code]["cards"] = []


            

    elif selected_card["name"] == "korrigan":
        last_action[room_code]["name"] = "korrigan"
        card_to_steal[room_code][user_id] = 2

        # For current user's visual :
        diffuse_hand(request.sid)
        diffuse_board(request.sid)
        
        # For opponent's visual :
        emit("redraw_hand", room=room_code, include_self=False)
        emit("redraw_board", room=room_code, include_self=False)

        highlight_opponent_hand(request.sid)
        return

    # For current user's visual :
    diffuse_hand(request.sid)
    diffuse_board(request.sid)
    
    # For opponent's visual :
    emit("redraw_hand", room=room_code, include_self=False)
    emit("redraw_board", room=room_code, include_self=False)

    ROOMS[room_code]["current_player_id"] = next(player_round[room_code])
    toggle_round_player(room_code, user_id)

    if len(deck[room_code]) > 0 :
        emit("highlight_deck", room=room_code, include_self=False)

    if len(deck[room_code]) == 0 and len(hand[room_code][opponent_id]) == 0 :
        finish(room_code, user_id, opponent_id)

def finish(room_code, user_id, opponent_id) :
    opponent_score = len(board[room_code][opponent_id])
    user_score = len(board[room_code][user_id])

    if user_score > opponent_score :
        winner_id = user_id
    elif user_score < opponent_score :
        winner_id = opponent_id
    else :
        winner_id = None
    emit("game_over", {"winner_id":winner_id, "scores":f"You: {user_score} pts &nbsp;|&nbsp; Opponent: {opponent_score} pts", "is_even": winner_id==None}, room=room_code)
@socketio.on("steal_card_from_board")
def steal_card_from_board(data):
    card_id = data["card_id"]

    entry = sid_to_room.get(request.sid)
    if entry is None :
        return

    room_code, user_id = entry
    opponent_id = get_opponent_id(room_code, user_id)

    if card_id not in [card["id"] for card in board[room_code][opponent_id]]:
        diffuse_message({"user": "system", "message":"CAUGHT CHEATING !"})
        return

    selected_card = [card for card in board[room_code][opponent_id] if card["id"] == card_id][0]

    board[room_code][opponent_id].remove(selected_card)
    board[room_code][user_id].append(selected_card)

    last_action[room_code]["cards"].append(selected_card)

    """
        Maybe try to encapsulate the "refresh" system ?
    """
    # For current user's visual :
    diffuse_hand(request.sid)
    diffuse_board(request.sid)
    
    # For opponent's visual :
    emit("redraw_hand", room=room_code, include_self=False)
    emit("redraw_board", room=room_code, include_self=False)

    ROOMS[room_code]["current_player_id"] = next(player_round[room_code])
    toggle_round_player(room_code, user_id)

    if len(deck[room_code]) > 0 :
        emit("highlight_deck", room=room_code, include_self=False)

    if len(deck[room_code]) == 0 and len(hand[room_code][opponent_id]) == 0 :
        finish(room_code, user_id, opponent_id)
@socketio.on("steal_card_from_hand")
def steal_card_from_hand(data):
    card_id = data["card_id"]

    entry = sid_to_room.get(request.sid)

    if entry is None :
        return

    room_code, user_id = entry

    opponent_id = get_opponent_id(room_code, user_id)
    if card_id not in [card["id"] for card in hand[room_code][opponent_id]]:
        print("Cheating !")
        print(f"Card id : {card_id}")
        diffuse_message({"user": "system", "message":"CAUGHT CHEATING !"})
        return

    selected_card = [card for card in hand[room_code][opponent_id] if card["id"] == card_id][0]

    hand[room_code][opponent_id].remove(selected_card)
    hand[room_code][user_id].append(selected_card)

    last_action[room_code]["cards"].append(selected_card)

    card_to_steal[room_code][user_id] -= 1

    if card_to_steal[room_code][user_id] == 0 or len(hand[room_code][opponent_id]) == 0:

        diffuse_hand(request.sid)
        diffuse_board(request.sid)
        
        # For opponent's visual :
        emit("redraw_hand", room=room_code, include_self=False)
        emit("redraw_board", room=room_code, include_self=False)

        if len(deck[room_code]) > 0 :
            emit("highlight_deck", room=room_code, include_self=False)

        ROOMS[room_code]["current_player_id"] = next(player_round[room_code])
        toggle_round_player(room_code, user_id)
        emit("disable_opponent_hand_steal", to=request.sid)
        return

    diffuse_hand(request.sid)
    diffuse_board(request.sid)
    
    # For opponent's visual :
    emit("redraw_hand", room=room_code, include_self=False)
    emit("redraw_board", room=room_code, include_self=False)
    # highlight_opponent_hand(request.sid)
        
    

    if len(deck[room_code]) == 0 and len(hand[room_code][opponent_id]) == 0 :
        finish(room_code, user_id, opponent_id)
    # " CAUGHT CHEATING ?????"

    # """
    #     Maybe try to encapsulate the "refresh" system ?
    # """
    # # For current user's visual :
    # diffuse_hand(request.sid)
    # diffuse_board(request.sid)
    
    # # For opponent's visual :
    # emit("redraw_hand", room=room_code, include_self=False)
    # emit("redraw_board", room=room_code, include_self=False)

    # if card_to_steal[room_code][user_id] == 0 :
    #     ROOMS[room_code]["current_player_id"] = next(player_round[room_code])
    #     toggle_round_player(room_code, user_id)
    # highlight_opponent_hand(request.sid)

def get_opponent_id(room_code, user_id):
    return (ROOMS[room_code]["players"] - {user_id}).pop()





