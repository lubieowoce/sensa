import typing
from typing import (
	Any,
	Dict, Optional, Union,
)
from types_util import (
	Id, SignalId,
	PMap_,
	IO_, IMGui, 
)
from pyrsistent import PMap, m

import imgui as im

from uniontype import union

from sensa_util import (impossible, bad_action)
from eff import (
	Eff, effectful,
	ID, EFFECTS, SIGNAL_ID, ACTIONS,
	eff_operation,
)
from node import (
	TransState,
	TransAction, 
	update_trans_node,
	SignalOutput, OutputNodeEffect,
)

from eeg_signal import Signal
from imgui_widget import window
from better_combo import str_combo_with_none

# from trans import Trans

from filters import (
    available_filters,
    default_parameters,
)



FILTER_BOX_OUTPUT_SIGNAL_ID = 'filter_box_output'



FilterId = str





FilterState, \
	Filter, \
= union(
'FilterState', [
	# ('NoFilter', []),
	('Filter',	 [('filter_id', FilterId),
				  ('params',    PMap)]),
				  # ('params',    PMap_[str, float])]),
]
)



FilterAction, \
	SetParam, \
= union(
'FilterAction', [
	# ('UnsetFilter', [('id_', Id)]),
	# ('SetFilter',   [('id_', Id), ('filter_id', FilterId)]),

	('SetParam', [('id_', Id),
				  ('name',  str),
				  ('value', float)])
]
)


FilterBoxState = typing.NamedTuple('FilterBoxState', [('id_', Id),
													  ('connection_state', TransState),
													  ('filter_state',     FilterState)])

FILTER_BOX_ACTION_TYPES = (TransAction, FilterAction)
# necessary, because  `type(3) != Union[int, str]`
# (union is just a `typing` construct. maybe there's a way to make it work?)
FilterBoxAction = Union[FILTER_BOX_ACTION_TYPES]

def is_filter_box_full(state: FilterBoxState) -> bool:
	return (    state .filter_state .is_Filter()
			and state .connection_state .is_Connected() )

@effectful(ID, SIGNAL_ID, EFFECTS)
def initial_filter_box_state(filter_id: FilterId) -> Eff(ID, SIGNAL_ID, EFFECTS)[FilterBoxState]:
	get_id = eff_operation('get_id')
	get_signal_id = eff_operation('get_signal_id')
	emit_effect = eff_operation('emit_effect')

	id_ = get_id()
	output_id = get_signal_id()
	emit_effect( OutputNodeEffect.CreateBlankOutput(output_id=output_id) )

	state = FilterBoxState(
		id_=id_,
		connection_state=TransState.Disconnected(id_=id_, output_id=output_id), # should initialize the inputs/outputs based on the filters sig
		filter_state=Filter(filter_id=filter_id, params=default_parameters[filter_id] )
	)

	return state








FilterBoxEffect, \
	ComputeOutput, \
	NoOutput, \
= union(
'FilerBoxEffect', [
	('ComputeOutput', [('id_', Id)]),
	('NoOutput',  [('id_', Id)]),
]
)


@effectful(EFFECTS)
def update_filter_box(filter_box_state: FilterBoxState, action: FilterBoxAction) -> Eff(EFFECTS)[FilterBoxState]:
	emit_effect = eff_operation('emit_effect')
	assert filter_box_state.id_ == action.id_
	old_state = filter_box_state
	new_state = None

	if type(action) == TransAction:
		connection_state = old_state.connection_state
		new_connection_state = update_trans_node(connection_state, action)
		if not(connection_state is new_connection_state):
			new_state = old_state._replace(connection_state=new_connection_state)


	elif type(action) == FilterAction:
		filter_state = old_state.filter_state
		if action.is_SetParam() and filter_state.is_Filter():
			param_name = action.name
			param_val  = action.value
			old_params = filter_state.params
			new_filter_state = filter_state.set(params=old_params.set(param_name, param_val))
			new_state = old_state._replace(filter_state=new_filter_state)



	if new_state != None:
		# something changed!
		# we have to recompute the output
		if is_filter_box_full(new_state):
			emit_effect( ComputeOutput(id_=new_state.id_) )
		else:
			emit_effect( NoOutput(id_=new_state.id_)  )

		return new_state

	else:
		return old_state



@effectful(ACTIONS)
def filter_box_window(
	filter_box_state: FilterBoxState,
	signals:  Dict[SignalId, Signal],
	ui_settings) -> Eff(ACTIONS)[IMGui[None]]:

	emit = eff_operation('emit')
	name = "Filter (id={id}, out={out})".format(id=filter_box_state.id_, out=filter_box_state.connection_state.output_id)
	with window(name=name):


		# signal selector

		if len(signals) > 0:
			available_signal_names = {sig_id: str(sig_id) for sig_id in signals.keys()}
			labels = sorted(available_signal_names.values()) 
			prev_o_selected_signal_name = (None if filter_box_state.connection_state.is_Disconnected()
										   else available_signal_names[filter_box_state.connection_state.input_id])

			changed, o_selected_signal_name = str_combo_with_none("signal", prev_o_selected_signal_name, labels)
			if changed:
				if o_selected_signal_name != None:
					# invert `available_signal_names` to find the signal id
					# signal_name_to_id = {sig_name: sig_id for (sig_id, sig_name) in available_signal_names.items()}
					# selected_signal_id = signal_name_to_id[o_selected_signal_name]
					selected_signal_id = int(o_selected_signal_name)
					emit( TransAction.Connect(id_=filter_box_state.id_, input_id=selected_signal_id) )
				else:
					emit( TransAction.Disconnect(id_=filter_box_state.id_) )
		else:
			im.text("No inputs available")




		# # filter type combo
		# filter_ids = sorted(available_filters.keys())
		# o_filter_id = None if filter_box_state.filter_state.is_NoFilter() else  filter_box_state.filter_state.filter_id

		# changed, o_filter_id = str_combo_with_none("filter", o_filter_id, filter_ids)
		# if changed:
		# 	if o_filter_id != None:
		# 		emit( SetFilter(id_=filter_box_state.id_, filter_id=o_filter_id) )
		# 	else:
		# 		emit( UnsetFilter(id_=filter_box_state.id_) )


		# param inputs
		slider_power = ui_settings['filter_slider_power']

		if filter_box_state .filter_state .is_Filter():

			filter_id     = filter_box_state .filter_state .filter_id
			filter_params = filter_box_state .filter_state .params
			filter = available_filters[filter_id]

			for param_name in sorted(filter.func_sig):
				changed, new_param_val = im.slider_float(param_name, filter_params[param_name],
														 min_value=0.001, max_value=95.,
														 power=slider_power)
				if changed:
					emit( SetParam(id_=filter_box_state.id_, name=param_name, value=new_param_val) )


			
		else:
			im.text("No filter selected")
		


def transform_signal(
	state: FilterBoxState,
	signal: Signal) -> Signal:

	assert state.filter_state.is_Filter()
	filter_id  = state .filter_state .filter_id
	parameters = state .filter_state .params
	transformation = available_filters[filter_id]

	return transformation(signal, parameters)



def handle_filter_box_effect(
	state: FilterBoxState,
	signals: PMap_[SignalId, SignalOutput], # output of another box
	command: FilterBoxEffect) -> SignalOutput:

	assert state.id_ == command.id_

	if   command.is_NoOutput():
		return SignalOutput.NotReady()

	elif command.is_ComputeOutput():
		if state.connection_state.is_Disconnected():
			return SignalOutput.NotReady()

		elif state.connection_state.is_Connected():
			input_signal_id  = state.connection_state.input_id
			m_input_signal   = signals[input_signal_id]

			if m_input_signal.is_NotReady():
				return SignalOutput.NotReady()

			elif m_input_signal.is_Ready():
				input_signal = m_input_signal.signal
				output_signal = transform_signal(state, input_signal)
				return SignalOutput.Ready(signal=output_signal)

			else:
				impossible("Invalid input signal state: "+input_signal)
		else:
			impossible("Invalid connection_state: "+state.connection_state)

	else:
		impossible("Invalid command: "+command)



	



