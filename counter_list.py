from PyQt5.QtWidgets import (
	QWidget, 
	QPushButton,
	QHBoxLayout,
	QVBoxLayout,
	QGroupBox,
	QLabel,
)

from types_util import *
from pyrsistent import (m, pmap, v, pvector)

class CounterList(QWidget):
	def __init__(clist, state, store, path):

		super().__init__(clist)

		clist.state = state
		clist.store = store
		clist.path  = path

		hbox = QHBoxLayout()

		counters = QWidget()
		counters_h = QHBoxLayout()
		counters_h.addStretch(1)
		counters.setLayout(counters_h)


		add_btn = QPushButton('+')
		add_btn.resize(add_btn.sizeHint())
		add_btn.clicked.connect( store.dispatch(add_widget(clist.state.id)) )

		remove_btn = QPushButton('-')
		remove_btn.resize(remove_btn.sizeHint())
		remove_btn.clicked.connect( store.dispatch(remove_widget(clist.state.id)) )

		# TODO: implement state passing.
		# Counterlist should handle subscribing to the store
		# and then passing the state to the counters. (its children, like in React!)
		# Also Would work elegantly with that StateUpdater / Provider thing!




counter_list = lambda id: m(id=id, items=v())

ADD_WIDGET    = "ADD_WIDGET"
REMOVE_WIDGET = "REMOVE_WIDGET"

add_widget    = lambda id: m(type=ADD_WIDGET,    id=id)
remove_widget = lambda id: m(type=REMOVE_WIDGET, id=id)




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






	def insert_widget(widget: QWidget):

