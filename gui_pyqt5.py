import sys

from PyQt5.QtGui import (
	QIcon,
)
from PyQt5.QtWidgets import (
	QApplication,
	QMainWindow,
	QWidget, 
	QAction,
	QPushButton,
	QDesktopWidget,
	# QMessageBox,
	QHBoxLayout,
	QVBoxLayout,
	QGroupBox,
	QLabel,
	QLineEdit,
)
from PyQt5.QtCore import (
	QCoreApplication,
	QObject,
	pyqtSignal,
)

from types_util import *
from sensa_util import *

from pyrsistent import (m, pmap, v, pvector, ny)
from store import Store

from counter import (Counter, counter, update_counter)
import counter as bc

# from counter_list import (CounterList, counter_list, update_counter_list)


current_id = [0]

def get_id() -> Id:
	global current_id

	id = current_id[0]
	current_id[0] += 1

	return id

def get_ids(n: int) -> List[Id]:
	ids = []
	for _ in range(n):
		ids.append(get_id())
	return ids


# A useful guide:
# https://redux.js.org/docs/recipes/reducers/BasicReducerStructure.html#basic-state-shape
# "Because the store represents the core of your application,
# you should define your state shape in terms of your domain data and app state,
# not your UI component tree"




def update_child_with(child_update):
	"""
	Returns a function which will forward actions targeted at an id
	to the child with that id using the `child_update` reducer
	"""
	def update_child(states: PMap_[Id, WidgetState], action: Action) -> PMap_[Id, WidgetState]:
		""" Forwards an action targeted at an id to the child with that id """
		id = action.id
		return states.transform([id], lambda state: child_update(state, action))
	return update_child



def update(state: PMap_[str, Any], action: Action):
	if action.type in [bc.INCREMENT, bc.DECREMENT]:
		return state.transform(['counters'],
							   lambda counters: update_child_with(update_counter)(counters, action))
	else:
		return state


cos = [counter(id) for id in get_ids(10)]
state = m(counters=pmap({co.id: co for co in cos}))
store = Store(state, update)



class App(QMainWindow):

	def __init__(win):
		super().__init__()
		win.init_ui()

	def init_ui(win):
		# win.setGeometry(300, 300, # window location
		#                  300, 220) # window size
		win.resize(300, 200)
		win.center_window()

		win.setWindowTitle('Sensa')
		win.setWindowIcon(QIcon('graphics/icon/icon.png'))

		app = QWidget(win) # needed because we can't set layouts on the window directly
		win.app = app
		win.setCentralWidget(app)

		counters_h = QHBoxLayout()
		counters_h.addStretch(1)
		# counters = QWidget() 
		# counters.setLayout(counters_h)

		for counter_s_id, counter_s in store.get_state().counters.items():
			counters_h.insertWidget(counters_h.count() - 1,
									Counter(name="counter "+str(counter_s_id), 
									        state=counter_s,
									        store=store,
									        path=v('counters', counter_s_id)) )
		app.setLayout(counters_h)
		win.show()


	def center_window(win):
		window_rect = win.frameGeometry() # rectangle specified by position
					# ^ QRect(top_left_x, top_left_y, bottom_right_x, bottom_right_y)
		center_point = QDesktopWidget().availableGeometry().center()
		window_rect.moveCenter(center_point)
		win.move(window_rect.topLeft())




if __name__ == '__main__':
	main_thread = QApplication(sys.argv)
	win = App()
	sys.exit(main_thread.exec_())





# class App(QMainWindow):

# 	def __init__(win):
# 		super().__init__()
# 		win.init_ui()

# 	def init_ui(win):
# 		# win.setGeometry(300, 300, # window location
# 		#                  300, 220) # window size
# 		win.resize(800, 200)
# 		win.center_window()

# 		win.setWindowTitle('Sensa')
# 		win.setWindowIcon(QIcon('graphics/icon/icon.png'))

# 		win.statusBar() # first call creates a status bar, next calls return it


# 		app = QWidget(win) # needed because we can't set layouts on the window directly
# 		win.app = app
# 		win.setCentralWidget(app)

# 		hbox = QHBoxLayout(app)
# 		win.hbox = hbox

# 		filters_h = QHBoxLayout()
# 		filters_h.addStretch(1)
# 		filters = QWidget()
# 		filters.setLayout(filters_h)


# 		add_lowpass_btn = QPushButton('+ lowpass')
# 		add_lowpass_btn.resize(add_lowpass_btn.sizeHint())

# 		# 1  2  3  4  5
# 		# [] --
# 		# 0  1  2  3  4
# 		add_lowpass_btn.clicked.connect(
# 			sequence(
# 				lambda: filters_h.insertWidget(
# 									filters_h.count() - 1,
# 									TransBox('Lowpass', make_lowpass_tr()) ),
# 				lambda: win.statusBar().showMessage('Added a lowpass'))
# 		)

# 		add_highpass_btn = QPushButton('+ highpass')
# 		add_highpass_btn.resize(add_highpass_btn.sizeHint())

# 		add_highpass_btn.clicked.connect(
# 			sequence(
# 				lambda: filters_h.insertWidget(
# 									filters_h.count() - 1,
# 									TransBox('Highpass', make_highpass_tr()) ),
# 				lambda: win.statusBar().showMessage('Added a highpass'))
# 		)


# 		remove_filter_btn = QPushButton('-')
# 		remove_filter_btn.resize(remove_filter_btn.sizeHint())

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




# 		win.statusBar().showMessage('Ready')

# 		win.show()

# 	def center_window(win):
# 		window_rect = win.frameGeometry() # rectangle specified by position
# 					# ^ QRect(top_left_x, top_left_y, bottom_right_x, bottom_right_y)
# 		center_point = QDesktopWidget().availableGeometry().center()
# 		window_rect.moveCenter(center_point)
# 		win.move(window_rect.topLeft())


# 	# def closeEvent(win, close_event):
# 	#     """
# 	#     QCloseEvent handler.
# 	#     That event fires when the [ X ] button is clicked.
# 	#     """
# 	#     reply = \
# 	#         QMessageBox.question(win, 'Closing Sensa',
# 	#                              'Are you sure you want to quit?',
# 	#                              QMessageBox.Yes | QMessageBox.No,
# 	#                              QMessageBox.No) # default button
# 	#     if reply == QMessageBox.Yes:
# 	#         close_event.accept()
# 	#     else:
# 	#         close_event.ignore()






# def run():
#     """For repl use. Doesn't work, because Qt blocks the thread :/"""
#     main_thread = QApplication(sys.argv)
#     win = App()
#     main_thread.exec_()
#     # sys.exit(main_thread.exec_())
#     return win



