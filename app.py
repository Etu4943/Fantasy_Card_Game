from flask import Flask, render_template, request, redirect, session
from flask_socketio import join_room, leave_room, send, SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

from functools import wraps


app = Flask(__name__)
app.config["SECRET_KEY"] = "SuperSecretKeyOMG"
socketio = SocketIO(app)

db = sqlite3.connect("fantasy.db", check_same_thread=False)
cursor = db.cursor()

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
