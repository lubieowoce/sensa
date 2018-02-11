import typing
from typing import (
	Any,
	Dict, Optional, List, Union, Fun
)
from types_util import (
	Id, SignalId,
	PMap_,
	IO_, IMGui, 
)
from pyrsistent import PMap, m

import imgui as im

from uniontype import union

from sensa_util import (chain, impossible, bad_action, Maybe, Nothing, Just)
from eff import (
	Eff, effectful,
	ID, EFFECTS, SIGNAL_ID, ACTIONS,
	eff_operation,
)
import node_graph as ng


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
													  ('filter_state',     FilterState)])


def eval_node(filter_box: FilterBoxState) -> Maybe[ Fun[[List[Signal]], List[Signal]] ]:
	return Just( chain(	lambda signals: signals[0],
						transformation(filter_box.filter_state),
						lambda signal: [signal]) )


def transformation(filter_state: FilterState) -> Signal:

	assert filter_state.is_Filter()
	filter_id  = filter_state .filter_id
	parameters = filter_state .params
	transformation = available_filters[filter_id]

	return lambda signal: transformation(signal, parameters)


def to_node(filter_box: FilterBoxState) -> ng.Node:
	return ng.Node(n_inputs=1, n_outputs=1)

FilterBoxState.eval_node = eval_node
FilterBoxState.to_node = to_node





FILTER_BOX_ACTION_TYPES = (FilterAction,)
# necessary, because  `type(3) != Union[int, str]`
# (union is just a `typing` construct. maybe there's a way to make it work?)
FilterBoxAction = Union[FILTER_BOX_ACTION_TYPES]

def is_filter_box_full(state: FilterBoxState) -> bool:
	return state .filter_state .is_Filter()

@effectful(ID, ACTIONS)
def initial_filter_box_state(filter_id: FilterId) -> Eff(ID, ACTIONS)[FilterBoxState]:
	get_id = eff_operation('get_id')
	emit = eff_operation('emit')

	id_ = get_id()
	state = FilterBoxState(
		id_=id_,
		filter_state=Filter(filter_id=filter_id, params=default_parameters[filter_id] )
	)
	emit(ng.AddNode(id_=id_, node=to_node(state)))

	return state




@effectful(ACTIONS)
def update_filter_box(filter_box_state: FilterBoxState, action: FilterBoxAction) -> Eff(ACTIONS)[FilterBoxState]:
	assert filter_box_state.id_ == action.id_
	old_state = filter_box_state
	new_state = None


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
		return new_state
	else:
		return old_state



@effectful(ACTIONS)
def filter_box_window(
	filter_box_state: FilterBoxState,
	ui_settings) -> Eff(ACTIONS)[IMGui[None]]:

	emit = eff_operation('emit')
	name = "Filter (id={id}, out={out})".format(id=filter_box_state.id_, out=filter_box_state.connection_state.output_id)
	with window(name=name):


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
		









	



