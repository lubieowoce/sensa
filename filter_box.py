from types_util import *

import imgui as im

from eeg_signal import Signal
from imgui_widget import window
from better_combo import str_combo_with_none, str_combo

from trans import Trans

from filters import (
    available_filters
)
    # highpass_filter, make_highpass_tr

FILTER_BOX_OUTPUT_SIGNAL_ID = 'filter_box_output'





def is_filter_box_connected(filter_box_state: Dict[str, Any]) -> bool:
	return filter_box_state['input_signal_id'] != None

def is_filter_box_disconnected(filter_box_state: Dict[str, Any]) -> bool:
	return filter_box_state['input_signal_id'] == None

def is_filter_box_filter_set(filter_box_state: Dict[str, Any]) -> bool:
	return filter_box_state['filter_id'] != None \
		   and filter_box_state['filter'] != None


def is_filter_box_full(filter_box_state: Dict[str, Any]) -> bool:
	return is_filter_box_connected(filter_box_state) \
		   and is_filter_box_filter_set(filter_box_state) \
		   and filter_box_state['filter'].has_all_parameters()


def should_filter_box_regenerate_signal(filter_box_state: Dict[str, Any]) -> bool:
	return filter_box_state['input_signal_id_changed'] \
		   or filter_box_state['param_value_changed'] \
		   or filter_box_state['filter_id_changed']



initial_filter_box_state = lambda:  {
										'input_signal_id': None,
										'input_signal_id_changed': True,
										'filter_id': None,
										'filter_id_changed': False,
										'filter': None,
										'param_value_changed': False,
									}

assert is_filter_box_disconnected(initial_filter_box_state())


def disconnect_filter_box(filter_box_state):
	filter_box_state['input_signal_id'] = None
	filter_box_state['input_signal_id_changed'] = True

def set_filter_box_input_signal_id(filter_box_state: Dict[str, Any], signal_id: str) -> IO_[None]:
	filter_box_state['input_signal_id'] = signal_id
	filter_box_state['input_signal_id_changed'] = True


def set_filter_box_filter(filter_box_state: Dict[str, Any], o_filter_id: str) -> IO_[None]:
	filter_box_state['filter_id'] = o_filter_id
	filter_box_state['filter_id_changed'] = True
	if o_filter_id != None:
		filter_id = o_filter_id
		filter_box_state['filter'] = available_filters[filter_id]()
	else:
		filter_box_state['filter'] = None



def filter_box(filter_box_state: Dict[str, Any], signal_data: Dict[str, Signal], ui_settings) -> IMGui[None]:
	with window(name="filter"):

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

		# filter type combo
		filter_ids = sorted(available_filters.keys())
		changed, o_filter_id = str_combo_with_none("filter", filter_box_state['filter_id'], filter_ids)
		if changed:
			set_filter_box_filter(filter_box_state, o_filter_id)
		else:
			filter_box_state['filter_id_changed'] = filter_box_state['filter_id_changed'] or False

		# param inputs
		slider_power = ui_settings['filter_slider_power']

		o_filter = filter_box_state.get('filter', None)
		if o_filter != None:
			filter = o_filter
			for param_name in sorted(filter.func_sig):
				changed, new_param_val = im.slider_float(param_name, filter.params[param_name],
														 min_value=0.001, max_value=95.,
														 power=slider_power)
				if changed:
					filter.params[param_name] = new_param_val
					filter_box_state['param_value_changed'] = True
				else:
					filter_box_state['param_value_changed'] = filter_box_state['param_value_changed'] or False
		else:
			im.text("No filter selected")
		

def update_filter_box(filter_box_state: Dict[str, Any], signal_data: Dict[str, Signal]) -> IO_[None]:
	if is_filter_box_full(filter_box_state):
		if should_filter_box_regenerate_signal(filter_box_state):
			output_signal = generate_output_signal(filter_box_state, signal_data)
			signal_data[FILTER_BOX_OUTPUT_SIGNAL_ID] = output_signal
	elif (not is_filter_box_filter_set(filter_box_state) or is_filter_box_disconnected(filter_box_state)) \
		   and FILTER_BOX_OUTPUT_SIGNAL_ID in signal_data:
		del signal_data[FILTER_BOX_OUTPUT_SIGNAL_ID]





def generate_output_signal(filter_box_state, signal_data: Dict[str, Signal]) -> Signal:
	assert is_filter_box_full(filter_box_state)

	input_signal_id = filter_box_state['input_signal_id']
	input_signal = signal_data[input_signal_id]
	transformation = filter_box_state['filter']
	output_signal = transformation(input_signal)
	return output_signal



