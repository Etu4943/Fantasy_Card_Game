class Card:
	def __init__(self, name, ability, ):
		self._name = name
		self._ability = ability


	def get_data(self):
		return {"name" : self._name, "ability":self._ability}