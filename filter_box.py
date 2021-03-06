import typing
from typing import (
	Any,
	Dict, Optional, List, Union
)
from utils.types import (
	Id, SignalId,
	PMap_,
	Fun, IO_, IMGui, 
)
from pyrsistent import PMap, m

import imgui as im

from sumtype import sumtype

from utils import (chain, impossible, bad_action, Maybe, Nothing, Just)
import utils as util

from eff import (
	Eff, effectful,
	ID, ACTIONS,
	emit, get_id, 
)
import node_graph as ng


from eeg_signal import Signal
from components.grouped import window
from components.str_combo import str_combo_with_none

# from trans import Trans

from filters import (
    available_filters,
    default_parameters,
)




FilterId = str





class FilterState(sumtype):
	# ('NoFilter', []),
	def Filter(filter_id: FilterId, params: PMap): ...



class FilterAction(sumtype):
	# def UnsetFilter(id_: Id): ...
	# def SetFilter(id_: Id, filter_id: FilterId): ...
	def SetParam(id_: Id, name:  str, value: float): ...


FilterBoxState = typing.NamedTuple('FilterBoxState', [('id_', Id),
													  ('filter_state', FilterState)])


def eval_node(filter_box: FilterBoxState) -> Fun[[List[Signal]], Maybe[List[Signal]]] :
	return chain(lambda signals: signals[0],
				transformation(filter_box.filter_state),
				lambda signal: Just([signal])) 


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

@effectful
async def initial_filter_box_state(filter_id: FilterId) -> Eff[[ID, ACTIONS], FilterBoxState]:
	id_ = await get_id()
	state = FilterBoxState(
		id_=id_,
		filter_state=FilterState.Filter(filter_id=filter_id, params=default_parameters[filter_id] )
	)
	await emit(ng.GraphAction.AddNode(id_=id_, node=to_node(state))) # TODO: Shouldn't be here

	return state




def update_filter_box(
		filter_box_state: FilterBoxState,
		action: FilterBoxAction
	) -> FilterBoxState:

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



@effectful
async def filter_box_window(
		filter_box_state: FilterBoxState,
		ui_settings
	) -> Eff[[ACTIONS], IMGui[None]]:

	name = None
	if filter_box_state .filter_state .is_Filter():
		filter_id     = filter_box_state .filter_state .filter_id
		filter = available_filters[filter_id]
		name = "{f_name} (id={id})###{id}".format(f_name=filter.name, id=filter_box_state.id_)
	else:
		name = "Filter###{id}".format(id=filter_box_state.id_)

	with window(name=name):


		# # filter type combo
		# filter_ids = sorted(available_filters.keys())
		# o_filter_id = None if filter_box_state.filter_state.is_NoFilter() else  filter_box_state.filter_state.filter_id

		# changed, o_filter_id = str_combo_with_none("filter", o_filter_id, filter_ids)
		# if changed:
		# 	if o_filter_id != None:
		# 		await emit( SetFilter(id_=filter_box_state.id_, filter_id=o_filter_id) )
		# 	else:
		# 		await emit( UnsetFilter(id_=filter_box_state.id_) )


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
					await emit( FilterAction.SetParam(id_=filter_box_state.id_, name=param_name, value=new_param_val) )


			
		else:
			im.text("No filter selected")

		return util.get_window_rect()
		









	



