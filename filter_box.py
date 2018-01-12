from types_util import *

import imgui as im

from eeg_signal import Signal
from imgui_widget import window
from better_combo import str_combo_with_none, str_combo

FILTER_BOX_OUTPUT_SIGNAL_ID = 'filter_box_output'


def is_filter_box_connected(filter_box_state: Dict[str, Any]) -> bool:
			return filter_box_state['input_signal_id'] != None

def is_filter_box_disconnected(filter_box_state: Dict[str, Any]) -> bool:
	return filter_box_state['input_signal_id'] == None

def should_filter_box_regenerate_signal(filter_box_state: Dict[str, Any]) -> bool:
	return filter_box_state['input_signal_id_changed'] \
		   or filter_box_state['param_value_changed']


def set_filter_box_input_signal_id(filter_box_state: Dict[str, Any], signal_id: str) -> IO_[None]:
	filter_box_state['input_signal_id'] = signal_id
	filter_box_state['input_signal_id_changed'] = True


def filter_box(filter_box_state: Dict[str, Any], signal_data: Dict[str, Signal]) -> IMGui[None]:
	with window(name="lowpass"):

		# signal selection combo
		if len(signal_data) > 0:
			signal_ids =  sorted(signal_data.keys())
			changed, o_input_signal_id = str_combo_with_none("signal", filter_box_state['input_signal_id'], signal_ids)
			if changed:
				set_filter_box_input_signal_id(filter_box_state, o_input_signal_id)
			else:
				filter_box_state['input_signal_id_changed'] = filter_box_state['input_signal_id_changed'] or False
		else:
			im.text("No signals available")

		# param inputs
		params = filter_box_state['trans'].params
		for param_name in params.keys():
			changed, new_param_val = im.slider_float(param_name, params[param_name],
													 min_value=0.05, max_value=95.,
													 power=1.)
			if changed:
				params[param_name] = new_param_val
				filter_box_state['param_value_changed'] = True
			else:
				filter_box_state['param_value_changed'] = filter_box_state['param_value_changed'] or False
		

def update_filter_box(filter_box_state: Dict[str, Any], signal_data: Dict[str, Signal]) -> IO_[None]:
	if is_filter_box_connected(filter_box_state):
		if should_filter_box_regenerate_signal(filter_box_state):
			output_signal = generate_output_signal(filter_box_state, signal_data)
			signal_data[FILTER_BOX_OUTPUT_SIGNAL_ID] = output_signal




def generate_output_signal(filter_box_state, signal_data: Dict[str, Signal]) -> Signal:
	input_signal_id = filter_box_state['input_signal_id']
	input_signal = signal_data[input_signal_id]
	transformation = filter_box_state['trans']
	assert transformation.has_all_parameters()
	output_signal = transformation(input_signal)
	return output_signal



