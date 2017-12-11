from PyQt5.QtWidgets import (
	QWidget, 
	QPushButton,
	QHBoxLayout,
	QVBoxLayout,
	QGroupBox,
	QLabel,
)
from PyQt5.QtCore import (
	pyqtSignal,
)

from reactive import *


class BoxCounter(QGroupBox, Reactive):

	@update
	def __init__(box, name):
		Reactive.__init__(box)
		QGroupBox.__init__(box)

		box.setTitle(name)
		
		# state
		box.counter_num = 0

		vbox = QVBoxLayout()

		# dependent on state
		box.counter_display = QLabel()
		box.on_change_of('counter_num', chain(str, box.counter_display.setText))
		vbox.addWidget(box.counter_display)
		
		plus_1  = QPushButton('+')
		plus_1.clicked.connect(box.inc)
		# plus_1.clicked.connect(lambda: box.setTitle("Hmmmmmm"))
		vbox.addWidget(plus_1)

		minus_1 = QPushButton('-')
		minus_1.clicked.connect(box.dec)
		vbox.addWidget(minus_1)

		box.setLayout(vbox)
		box.setFixedWidth(150)

		# box.r_update()


	@update_0
	def inc(box):
		box.counter_num += 1

	@update_0
	def dec(box):
		box.counter_num -= 1

