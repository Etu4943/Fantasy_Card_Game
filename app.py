from flask import Flask, render_template, request, redirect, session
from flask_socketio import join_room, leave_room, send, SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

from random import randint

from functools import wraps


app = Flask(__name__)
app.config["SECRET_KEY"] = "SuperSecretKeyOMG"
socketio = SocketIO(app)

db = sqlite3.connect("fantasy.db", check_same_thread=False)
cursor = db.cursor()

ROOMS = dict()

NB_LETTERS_ROOM_SEQUENCE = 4


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
		return render_template("temp.html", message="OK, so the post method works so far !")

@app.route("/create_room", methods=["POST"])
@login_required
def create_room():
	room_sequence = create_room_sequence(NB_LETTERS_ROOM_SEQUENCE)
	return render_template("temp.html", message=room_sequence)


def create_room_sequence(nb_letter):
	room_sequence = ""
	for _ in range(nb_letter) :
		room_sequence += chr(ord('A') + randint(0,26))

	return room_sequence