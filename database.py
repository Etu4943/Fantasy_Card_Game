import sqlite3

db = sqlite3.connect("fantasy.db", check_same_thread=False)
cursor = db.cursor()

def update_scoreboard(winner_id, winner_score, lorser_id, loser_score, is_even):
	is_even = 1 if is_even else 0
	try :
		db.execute("INSERT INTO scoreboard (winner_id, winner_score, loser_id, loser_score, is_even) VALUES (?, ?, ?, ?, ?)", (winner_id, winner_score, lorser_id, loser_score, is_even))
		db.commit()
	except sqlite3.Error as err :
		db.rollback()
		print(err)
		