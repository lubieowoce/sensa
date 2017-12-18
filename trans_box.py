from PyQt5.QtWidgets import (
	QWidget, 
	QPushButton,
	QHBoxLayout,
	QVBoxLayout,
	QFormLayout,
	QGroupBox,
	QLabel,
	QLineEdit,
)
from PyQt5.QtCore import (
	pyqtSignal,
)

from reactive import *

from trans import Trans, TransChain
from signal import Signal
from util import chain, dict_set_all, setitem
from operator import itemgetter


raise NotImplementedError()


class TransBox(QGroupBox, Reactive):
	param_changed = pyqtSignal(name='param_changed')

	@update
	def __init__(box, name: str, trans: Trans):
		Reactive.__init__(box)
		QGroupBox.__init__(box)

		box.setTitle(name)

		box.trans = trans # state
		# the trans stores its parameters, so its params can change
		# box.params = trans.params # state
		box.params = {} # state
		dict_set_all(box.params, trans.params)

		box_layout = QVBoxLayout()

		params_form = QWidget()
		params_form_layout = QFormLayout() # dependent on box.trans.params : Dict[str, Any]

		# create a form with a field for each of box.params
		# and bind its fields to box.params
		for param_name, param_value in box.trans.params.items():
			input_box = QLineEdit()
			params_form_layout.addRow(param_name, input_box)
			
			box.on_change_of('params',
						     chain(itemgetter(param_name), str, input_box.setText))
			# the form's text depend on the box's params dict
			# it might change programatically, for example by undo
			# TODO: sort of circular with setting params by user input
			#		(an input changes params, which needlessly triggers setting the input's text)

			input_box.editingFinished.connect(
				lambda: box.update_param( param_name, float(input_box.text()) )
			)
			# TODO: only supports float parameters for now and no error handling

		# bind the underlying trans's params to the box's params
		box.on_change_of('params', lambda _: dict_set_all(box.trans.params, box.params))
		box.setFixedWidth(150)
		params_form.setLayout(params_form_layout)



		trans_debug_view = QLabel()
		box.on_change_of('params',
			lambda _: trans_debug_view.setText(str(box.trans))
		)



		box_layout.addWidget(params_form)
		box_layout.addWidget(trans_debug_view)
		box.setLayout(box_layout)



	def update_trans_params(box):
		dict_set_all(box.trans.params, box.params)

	@update
	def update_param(box, key, value):
		box.params[key] = value





