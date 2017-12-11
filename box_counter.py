from PyQt5.QtWidgets import (
	QWidget, 
	QPushButton,
	QHBoxLayout,
	QVBoxLayout,
	QGroupBox,
	QLabel,
)
from types_util import *
from pyrsistent import m

class BoxCounter(QGroupBox):

	def __init__(box, name, state, store):
		QGroupBox.__init__(box)

		# m(counter=...)
		box.state = state
		box.store = store
		store.subscribe(box.update_this_state)
		
		box.setTitle(name)

		vbox = QVBoxLayout()

		# dependent on state
		box.counter_display = QLabel()
		vbox.addWidget(box.counter_display)
		
		plus_1  = QPushButton('+')
		plus_1.clicked.connect(box.increment)
		vbox.addWidget(plus_1)

		minus_1 = QPushButton('-')
		minus_1.clicked.connect(box.decrement)
		vbox.addWidget(minus_1)

		box.setLayout(vbox)
		box.setFixedWidth(150)

		box.r_render()

		# box.r_update()


	def increment(box):
		act = increment(n=1, id=box.state.id) 
		print("sending", act)
		box.store.dispatch(act)

	def decrement(box):
		act = decrement(n=1, id=box.state.id)
		print("sending", act)
		box.store.dispatch(act)


	# def set_state(box, new_props):
	# 	box.state = new_props

	def r_render(box):
		# 'counter_display', 'str .> setText', 'counter'
		print("rendering")
		box.counter_display.setText( str(box.state.counter) )

	def update_this_state(box):
		# dependent on the store layout
		box.state = box.store.get_state().counters[box.state.id]
		box.r_render()


INCREMENT = "INCREMENT"
DECREMENT = "DECREMENT"
# counter_actions = \
# 	v( m(type=INCREMENT, n=..., id=...) ,
# 	   m(type=DECREMENT, n=..., id=...) )
increment = lambda n, id: m(type=INCREMENT, n=n, id=id)
decrement = lambda n, id: m(type=DECREMENT, n=n, id=id)

def counter(id) -> WidgetState:
	return m(id=id, counter=0)
	#TODO: id should be a prop, not state?

# reducer
def update_counter(state: WidgetState, action: Action) -> WidgetState:
	if action.id != state.id:
		# action targets another widget
		return state

	if action.type == INCREMENT:
		new_counter = state.counter + action.n
		return state.set('counter', new_counter)

	elif action.type == DECREMENT:
		new_counter = state.counter - action.n
		return state.set('counter', new_counter)
	else:
		err_unsupported_action(action, state)
		return state
