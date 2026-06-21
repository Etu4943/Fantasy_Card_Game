from flask import Flask, render_template, request, redirect, session, url_for, g
from extensions import socketio
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import fsocket

import json
import os

from state import ROOMS
from random import randint

from functools import wraps



app = Flask(__name__)
app.config["SECRET_KEY"] = "SuperSecretKeyOMG"
app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
AVAILABLE_LANGUAGES = ["fr", "en"]
socketio.init_app(app)

db = sqlite3.connect("fantasy.db", check_same_thread=False)
cursor = db.cursor()


NB_LETTERS_ROOM_SEQUENCE = 5
MAX_PLAYERS = 2


def login_required(f):
    """
    From cs50 finance project
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
	return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "GET" :
		if session.get('username',False) :
			return redirect("/")
		return render_template("login.html")
	if request.method == "POST" :
		email = request.form.get("email")
		password = request.form.get("password")

		user = db.execute("SELECT id, username, hash FROM users WHERE email = ?", (email,)).fetchone()

		if user == None :
			return render_template("error.html", err="Cet utilisateur n'existe pas.")
		elif not check_password_hash(user[2], password) :
			return render_template("error.html", err="Mauvais mot de passe.")
		else :
			session["user_id"] = user[0]
			session["username"] = user[1]
		return redirect("/")

@app.route("/register", methods=["POST"])
def register():
	username = request.form.get("username")
	email = request.form.get("email")
	password = request.form.get("password")
	hashed = generate_password_hash(password)

	try :
		db.execute("INSERT INTO users (username, email, hash) VALUES (?, ?, ?)", (username, email, hashed))
		db.commit()
		return redirect("/login")
	except sqlite3.Error as err :
		db.rollback()
		return render_template("error.html", err=err)

@app.route("/logout", methods=["GET"])
def logout():
	session.clear()
	return redirect("/login")

@app.route('/room/<room_code>')
@login_required
def room(room_code):
	session['room'] = room_code
	return render_template("room.html", room_code=room_code)

@app.route("/game", methods=["POST", "GET"])
@login_required
def game():
	return render_template("game.html")

@app.route("/chat", methods=["POST", "GET"])
@login_required
def chat():
	return render_template("chat.html")

@app.route("/join", methods=["POST", "GET"])
@login_required
def join():
	if request.method == "GET" :
		return render_template("join.html")
	elif request.method == "POST" :
		room_sequence = request.form.get("room_sequence")
		if room_sequence not in ROOMS.keys() :
			return render_template("error.html", err=f"This room doesn't exists yet !")
		elif len(ROOMS[room_sequence]['players']) == MAX_PLAYERS :
			return render_template("error.html", err=f"This room is already full !")
		else :

			return join_a_room(room_sequence)

@app.route("/create_room", methods=["POST"])
@login_required
def create_room():
	room_sequence = create_room_sequence(NB_LETTERS_ROOM_SEQUENCE)
	ROOMS[room_sequence] = {'players' : set(), 'messages' : []}
	return join_a_room(room_sequence)

def join_a_room(room_sequence): # join_room is in socketio
	return redirect(url_for('room', room_code=room_sequence))

@app.route("/quit_room")
@login_required
def quit_room():
	session.pop("room", None)
	return redirect("/join")

def create_room_sequence(nb_letter):
	room_sequence = ""
	for _ in range(nb_letter) :
		room_sequence += chr(ord('A') + randint(0,25))

	return room_sequence

@app.before_request
def set_language():
    g.lang = session.get('lang', 'fr')  # ← lit la session à chaque requête

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in AVAILABLE_LANGUAGES:
    	session['lang'] = lang
    return redirect(request.referrer or '/')

def get_translations(lang):
    path = os.path.join(app.root_path, 'locales', lang, 'translation.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)

@app.context_processor
def inject_translations():
    lang = g.get('lang', 'fr') # Try to get the language, fr by default
    session["lang"] = lang
    return dict(t=get_translations(lang))


if __name__ == "__main__" :
	socketio.run(app)