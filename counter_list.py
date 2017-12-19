from util import get_id, err_unsupported_action

from types_util import *
from pyrsistent import (m, pmap, v, pvector)

from counter import counter

counter_list = lambda id: m(id=id, items=v())

ADD_COUNTER    = "ADD_COUNTER"
REMOVE_COUNTER = "REMOVE_COUNTER"

add_counter    = lambda: m(type=ADD_COUNTER)
remove_counter    = lambda: m(type=REMOVE_COUNTER)
# remove_widget = lambda id: m(type=REMOVE_COUNTER, id=id)

def update_counter_list(counters, action):
	if action.type == ADD_COUNTER:
		id = get_id()
		return counters.set(id, counter(id))
	elif action.type == REMOVE_COUNTER:
		if len(counters) > 0:
			max_id = max(counters.keys())
			return counters.remove(max_id)
		else: # len(counters) <= 0
			return counters
	else:
		err_unsupported_action(counters, action)
		return counters



# from PyQt5.QtWidgets import (
# 	QWidget, 
# 	QPushButton,
# 	QHBoxLayout,
# 	QVBoxLayout,
# 	QGroupBox,
# 	QLabel,
# )
# class CounterList(QWidget):
# 	def __init__(clist, state, store, path):

# 		super().__init__(clist)

# 		clist.state = state
# 		clist.store = store
# 		clist.path  = path

# 		hbox = QHBoxLayout()

# 		counters = QWidget()
# 		counters_h = QHBoxLayout()
# 		counters_h.addStretch(1)
# 		counters.setLayout(counters_h)


# 		add_btn = QPushButton('+')
# 		add_btn.resize(add_btn.sizeHint())
# 		add_btn.clicked.connect( store.dispatch(add_widget(clist.state.id)) )

# 		remove_btn = QPushButton('-')
# 		remove_btn.resize(remove_btn.sizeHint())
# 		remove_btn.clicked.connect( store.dispatch(remove_widget(clist.state.id)) )

# 		# TODO: implement state passing.
# 		# Counterlist should handle subscribing to the store
# 		# and then passing the state to the counters. (its children, like in React!)
# 		# Also Would work elegantly with that StateUpdater / Provider thing!








# 		def remove_last_filter():
# 			if filters_h.count() >= 2: # [filter] ... [spacer]
# 				item = filters_h.takeAt( filters_h.count()-2 ) # last item is a spacer
# 				item.widget().deleteLater()
		
# 		remove_filter_btn.clicked.connect(
# 			sequence(
# 				remove_last_filter,
# 				lambda: win.statusBar().showMessage('Removed a filter'))
# 		)

# 		# test_btn = QPushButton('test')
# 		# def test(ch):
# 		# 	raise Exception('checked: ' + str(ch))
# 		# test_btn.clicked.connect(test)


# 		buttons_v = QVBoxLayout()
# 		buttons_v.addWidget(add_lowpass_btn)
# 		buttons_v.addWidget(add_highpass_btn)
# 		buttons_v.addWidget(remove_filter_btn)
# 		# buttons_v.addWidget(test_btn)
# 		buttons = QWidget()
# 		buttons.setLayout(buttons_v)
# 		buttons.setFixedWidth(150)

# 		hbox.addWidget(buttons)
# 		hbox.addWidget(filters)







