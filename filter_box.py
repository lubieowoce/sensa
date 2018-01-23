import typing
from typing import (
	Any,
	Dict, Optional,
)
from types_util import (
	Id,
	PMap_,
	IO_, IMGui, 
)
from pyrsistent import PMap

import imgui as im

from uniontype import union

from sensa_util import (impossible, bad_action)
from eff import (
	Eff, effectful,
	EFFECTS, SIGNAL_ID, ACTIONS,
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



SignalId = str
FilterId = str


ConnectionState, \
	Disconnected, \
	Connected, \
= union(
'ConnectionState', [
	('Disconnected', []),
	('Connected', 	 [('signal_id', SignalId)]),
]
)


FilterState, \
	NoFilter, \
	Filter, \
= union(
'FilterState', [
	('NoFilter', []),
	('Filter',	 [('filter_id', FilterId),
				  ('params',    PMap)]),
				  # ('params',    PMap_[str, float])]),
]
)


FilterBoxState = typing.NamedTuple('FilterBoxState', [('id_', Id),
													  ('connection_state', ConnectionState),
													  ('filter_state',     FilterState)])

def is_filter_box_full(state: FilterBoxState) -> bool:
	return (    state .filter_state .is_Filter()
			and state .connection_state .is_Connected() )


def initial_filter_box_state(id_: Id) -> FilterBoxState:
	return \
		FilterBoxState(
			id_=id_,
			connection_state=Disconnected(),
			filter_state=NoFilter()
		)




FilterBoxAction, \
	Disconnect, \
	Connect, \
	UnsetFilter, \
	SetFilter, \
	SetFilterParam, \
= union(
'FilterBoxAction', [
	('Disconnect',  [('id_', Id)]),
	('Connect',     [('id_', Id), ('signal_id', SignalId)]),

	('UnsetFilter', [('id_', Id)]),
	('SetFilter',   [('id_', Id), ('filter_id', FilterId)]),

	('SetFilterParam', [('id_', Id),
						('name',  str),
						('value', float)])
]
)



FilterBoxEffect, \
	ComputeOutput, \
	RemoveOutput, \
= union(
'FilerBoxEffect', [
	('ComputeOutput', [('id_', Id)]),
	('RemoveOutput',  [('id_', Id)]),
]
)


@effectful(EFFECTS)
def update_filter_box(filter_box_state: FilterBoxState, action: FilterBoxAction) -> Eff(EFFECTS)[FilterBoxState]:
	assert filter_box_state.id_ == action.id_
	old_state = filter_box_state
	new_state = None

	if   action.is_Disconnect():
		new_state = old_state._replace(connection_state=Disconnected())

	elif action.is_Connect():
		signal_id = action.signal_id
		new_state = old_state._replace(connection_state=Connected(signal_id=signal_id))

	elif action.is_UnsetFilter():
		new_state = old_state._replace(filter_state=NoFilter())

	elif action.is_SetFilter():
		filter_id = action.filter_id
		new_state = old_state._replace(filter_state=Filter(filter_id=filter_id,
														   params=default_parameters[filter_id] ))

	elif action.is_SetFilterParam():
		filter_state = old_state .filter_state
		if   filter_state .is_NoFilter():
			bad_action("Cannot set a param, no filter selected")
			pass
		elif filter_state .is_Filter():
			param_name = action.name
			param_val  = action.value
			old_params = filter_state.params
			new_filter_state = filter_state.set(params=old_params.set(param_name, param_val))
			new_state = old_state._replace(filter_state=new_filter_state)
		else:
			impossible("Invalid filter state: "+filter_state)

	else:
		impossible("Invalid filter box state: "+old_state)


	if new_state != None:
		# something changed!
		# we have to recompute the output
		if is_filter_box_full(new_state):
			emit_effect( ComputeOutput(id_=new_state.id_) )
		else:
			emit_effect( RemoveOutput(id_=new_state.id_)  )

		return new_state

	else:
		return old_state




def filter_box_window(filter_box_state: FilterBoxState, signal_data: PMap_[str, Signal], ui_settings, emit) -> IMGui[None]:
	with window(name="filter (id={id_})".format(id_=filter_box_state.id_)):

		# signal selection combo
		if len(signal_data) > 0:
			signal_ids =  sorted(signal_data.keys())
			o_signal_id = None if filter_box_state.connection_state.is_Disconnected() else  filter_box_state.connection_state.signal_id
			changed, o_input_signal_id = str_combo_with_none("signal", o_signal_id , signal_ids)
			if changed:
				if o_input_signal_id != None:
					emit( Connect(id_=filter_box_state.id_, signal_id=o_input_signal_id) )
				else:
					emit( Disconnect(id_=filter_box_state.id_) )

		else:
			im.text("No signals available")

		# filter type combo
		filter_ids = sorted(available_filters.keys())
		o_filter_id = None if filter_box_state.filter_state.is_NoFilter() else  filter_box_state.filter_state.filter_id

		changed, o_filter_id = str_combo_with_none("filter", o_filter_id, filter_ids)
		if changed:
			if o_filter_id != None:
				emit( SetFilter(id_=filter_box_state.id_, filter_id=o_filter_id) )
			else:
				emit( UnsetFilter(id_=filter_box_state.id_) )


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
					emit( SetFilterParam(id_=filter_box_state.id_, name=param_name, value=new_param_val) )


			
		else:
			im.text("No filter selected")
		

# def update_filter_box(filter_box_state: Dict[str, Any], signal_data: Dict[str, Signal]) -> IO_[None]:
# 	if is_filter_box_full(filter_box_state):
# 		if should_filter_box_regenerate_signal(filter_box_state):
# 			output_signal = generate_output_signal(filter_box_state, signal_data)
# 			signal_data[FILTER_BOX_OUTPUT_SIGNAL_ID] = output_signal
# 	elif (not is_filter_box_filter_set(filter_box_state) or is_filter_box_disconnected(filter_box_state)) \
# 		   and FILTER_BOX_OUTPUT_SIGNAL_ID in signal_data:
# 		del signal_data[FILTER_BOX_OUTPUT_SIGNAL_ID]



def handle_filter_box_effect(
	state: FilterBoxState,
	signal_data: Dict[str, Signal],
	command: FilterBoxEffect) -> Optional[Signal]:

	assert state.id_ == command.id_

	if   command.is_RemoveOutput():
		return None

	elif command.is_ComputeOutput():
		assert is_filter_box_full(state)

		signal_id = state .connection_state .signal_id
		input_signal = signal_data[signal_id]

		filter_id  = state .filter_state .filter_id
		parameters = state .filter_state .params
		transformation = available_filters[filter_id]

		output_signal = transformation(input_signal, parameters)
		assert output_signal != None
		return output_signal

	else:
		impossible("Invalid command: "+command)



	



