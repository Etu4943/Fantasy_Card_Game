from extensions import socketio
from state import ROOMS, sid_to_room, hand

from flask import request, session
from flask_socketio import join_room, leave_room, send, SocketIO, emit

from game import init_hand

@socketio.on('message')
def handle_message(data):
    print('received message: ', data)

@socketio.on('join')
def handle_join(data):
    room_code = data.get('room_code')
    user_id = session.get('user_id')

    join_room(room_code)

    ROOMS[room_code]["players"].add(user_id)
    sid_to_room[request.sid] = (room_code, user_id)

    # Quand tu rejoins une partie, il faut lui créer et lui attribuer une main
    
    hand[room_code] = dict()
    hand[room_code][user_id] = []
    init_hand(room_code, user_id)
    #socketio.emit('message', {'message':f'{session.get("username")} has entered the game !'}, room=room_code, include_self=False)
    diffuse_message({'message' : "has enter the chat"})

@socketio.on('disconnect')
def handle_disconnect():
    remove_player(request.sid)

@socketio.on('leave')
def handle_leave():
    room_code = remove_player(request.sid)
    if room_code:
        #socketio.emit('message', {'message':f'{session.get("username")} has quit the game !'}, room=room_code, include_self=False)
        diffuse_message({'message' : "has left the chat"}, room_code)
        leave_room(room_code)  
    emit('left_room')


def remove_player(sid):
    entry = sid_to_room.pop(sid, None)
    if entry is None:
        return None

    room_code, user_id = entry

    if room_code in ROOMS:
        ROOMS[room_code]['players'].discard(user_id)
        if not ROOMS[room_code]['players']:
            print("No more players. Lets NUKE IT")
            del ROOMS[room_code]


    return room_code

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
    room_code, user_id = entry

    emit("hand", hand[room_code][user_id], to=request.sid) # Envoit uniquement les cartes au joueur concerné
    # J'enverrai le nombre de carte uniquement à l'autre joueur.

@socketio.on("draw_a_card")
def handle_draw_a_card():
    entry = sid_to_room.get(request.sid, None)
    room_code, user_id = entry

    draw_card(room_code, user_id)


def draw_card(room_code, user_id):
    hand[room_code][user_id].append("c4")
    diffuse_hand()