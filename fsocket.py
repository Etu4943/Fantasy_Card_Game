from extensions import socketio
from state import ROOMS, sid_to_room

from flask import request, session
from flask_socketio import join_room, leave_room, send, SocketIO, emit

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

    print('A user has enter the game !')

@socketio.on('disconnect')
def handle_disconnect():
    remove_player(request.sid)

@socketio.on('leave')
def handle_leave():
    room_code = remove_player(request.sid)
    if room_code:
        leave_room(room_code)  # désabonne ce socket du canal de diffusion
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