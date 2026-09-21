class Card:
	def __init__(self, name, ability, card_id, card_text = ""):
		self._name = name
		self._ability = ability
		self._id = card_id
		self._text = card_text


	def get_data(self):
		return {"name" : self._name, "ability":self._ability, "id" : self._id}

	def get_text(self):
		return self._text