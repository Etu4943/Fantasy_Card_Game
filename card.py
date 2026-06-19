class Card:
	def __init__(self, name, ability, card_id):
		self._name = name
		self._ability = ability
		self._id = card_id


	def get_data(self):
		return {"name" : self._name, "ability":self._ability, "id" : self._id}