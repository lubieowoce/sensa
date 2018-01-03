from util import (err_unsupported_action)

from types_util import *
from pyrsistent import (m, pmap, v, pvector, thaw, freeze)
from id_eff import id_and_effects, is_in_id_eff
from counter import counter

# counter_list = lambda id: m(id=id, items=v())

ADD_COUNTER    = "ADD_COUNTER"
REMOVE_COUNTER = "REMOVE_COUNTER"
CLEAR_COUNTERS = "CLEAR_COUNTERS"

add_counter    = lambda: m(type=ADD_COUNTER)
remove_counter = lambda: m(type=REMOVE_COUNTER)
clear_counters = lambda: m(type=CLEAR_COUNTERS)

@id_and_effects
def update_counter_list(state, action) -> IdEff[PMap_[str, Any]]:
	# state = { counters: {id: co}, counter_list: [id]}


	if action.type == ADD_COUNTER:
		id = get_id()
		# return \
		# 	state.transform(
		# 		   ['counters'], lambda counters: counters.set(id, counter(id)),
		# 		   ['counter_list'], lambda list: list.append(id) )
		st = thaw(state)
		st['counters'][id] = counter(id)
		st['counter_list'].append(id)
		return freeze(st)

	elif action.type == REMOVE_COUNTER:
		if len(state.counter_list) > 0:
			list = state.counter_list
			id = list[len(list)-1]
			# return \
			# 	state.transform(
			# 		['counters'], lambda counters: counters.delete(id)
			# 		['counter_list'], lambda list: list.delete(len(list)-1) )
			st = thaw(state)
			st['counters'].pop(id)
			st['counter_list'].pop()
			return freeze(st)

		else: # len(counters) <= 0
			return state

	elif action.type == CLEAR_COUNTERS:
		return \
		 	state.set('counters', m()).set('counter_list', v())
	else:
		err_unsupported_action(counters, action)
		return counters

# def uuu(state, action) -> IdEff[PMap_[str, Any]]:
# 	# state = { counters: {id: co}, counter_list: [id]}
# 	# assert is_in_id_eff(), "is_in_id_eff failed."
# 	assert "get_id" in globals(), "get_id not in globals in update. globals:" + str(dict(globals()))
# 	# print("is_in_id_eff:", is_in_id_eff())
# 	# print("get_id(g):", globals()['get_id'])
# 	# print("get_id(n):", get_id)

# 	if action.type == ADD_COUNTER:
# 		id = get_id()

# def g(key):
# 	emit_effect("jump")
# 	d = f()
# 	zi = get_id()
# 	d[key] = zi
# 	return d

# def f() -> IdEff[None]:
# 	xi = get_id()
# 	yi = get_id()
# 	emit_effect('print 1')
# 	return {'x': xi, 'y': yi}

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







