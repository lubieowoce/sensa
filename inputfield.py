from PyQt5.QtWidgets import (
	QLineEdit,
)
from types_util import *
from sensa_util import id_
from pyrsistent import m

class InputField(QLineEdit):
	def __init__(input, from_str=id_, state, store):
		"""
		`from_str`: str -> a   for some type a.
		It will be used to decode the input text.
		Defaults to sensa_util.id_ = lambda x: x
		"""
		super().__init__(input)

		# m(text=..., id=...)
		input.state = state
		input.store = store

		input.store.subscribe(input.update_state)
		input.editingFinished.connect(input.got_input)

		input.update_widget()

	def got_input(input):
		val = input.from_str(input.text())
		act = got_input(val=val, id=input.state.id)
		input.store.dispatch(act)

	def update_state(input):
		input.state = store.get_state().inputs[input.state.id]

	def update_widget(input):
		""" Updates all the Qt widgets with the values from .state """
		input.setText(input.state.text)




GOT_INPUT = "GOT_INPUT"
# m(type=GOT_INPUT, val=..., id=..., in_type=...)
got_input = lambda val, id: m(type=GOT_INPUT, val=val, id=id, in_type=float)