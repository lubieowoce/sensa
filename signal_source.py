import typing
from typing import (
	Any, List, Dict, Optional, Union, 
)
from types_util import (
	Id, SignalId,
	PMap_,
	Fun, IO_, IMGui, 
)
from sensa_util import impossible, Maybe, Nothing, Just
import sensa_util as util

from eff import (
	Eff, effectful,
	ID, EFFECTS, SIGNAL_ID, ACTIONS,
	eff_operation,
)
from uniontype import union

import node_graph as ng

from eeg_signal import Signal

from imgui_widget import window
from better_combo import str_combo_with_none
import imgui as im

# Actualy a kind of Node - Source




SourceState, \
	Empty, \
	Full, \
= union(
'SourceState', [
	('Empty', [('id_', Id)]),
	('Full',  [('id_', Id), ('signal_id', SignalId)])
	#                        ^ the source signal
]
)

def eval_node(src) -> Fun[ [Dict[SignalId, Signal]], Maybe[List[Signal]] ]:
	return  lambda signals: Just([signals[src.signal_id]]) if src.is_Full() else Nothing()

def to_node(src) -> ng.Node:
	return ng.Node(n_inputs=0, n_outputs=1)

SourceState.eval_node = eval_node
SourceState.to_node   = to_node



SourceAction, \
	SetEmpty, \
	SelectSignal, \
= union(
'SourceAction', [
	('SetEmpty',     [('id_', Id)]), \
	('SelectSignal', [('id_', Id), ('signal_id', SignalId)]), \
]
)


@effectful(ID, ACTIONS)
def initial_source_state():
	get_id = eff_operation('get_id')
	emit = eff_operation('emit')

	id_ = get_id()
	state = SourceState.Empty(id_=id_)
	emit(ng.AddNode(id_=id_, node=to_node(state)))
	return state




@effectful(ACTIONS)
def update_source(source_state: SourceState, action: SourceAction) -> Eff(ACTIONS)[SourceState]:
	assert source_state.id_ == action.id_
	old_state = source_state

	if action.is_SetEmpty():
		return Empty(id_=old_state.id_)

	elif action.is_SelectSignal():
		return Full(id_=old_state.id_, signal_id=action.signal_id)
	else:
		impossible("Unsupported action: "+action)
		return old_state



@effectful(ACTIONS)
def signal_source_window(
	source_state: SourceState,
	signal_data:  PMap_[SignalId, Signal],
	signal_names: PMap_[SignalId, str]) -> Eff(ACTIONS)[IMGui[None]]:

	emit = eff_operation('emit')


	source_name = "Source (id={id})###{id}".format(id=source_state.id_)

	with window(name=source_name):

		# signal selector

		if len(signal_data) > 0:
			signal_ids = signal_data.keys()
			visible_signal_names = {sig_id: signal_names[sig_id] for sig_id in signal_ids}

			# disambiguate signals with duplicate names
			duplicated_signal_names = 	{sig_id: sig_name
										 for (sig_id, sig_name) in visible_signal_names.items()
										 if list(visible_signal_names.values()).count(sig_name) > 1
									  	}
			disambiguated_signal_names = 	{sig_id: "{name} ({id})".format(name=sig_name, id=sig_id)
											 for (sig_id, sig_name) in duplicated_signal_names.items()
										 	}
			visible_signal_names.update(disambiguated_signal_names)
			# now `visible_signal_names` is an invertible mapping
			labels = sorted(visible_signal_names.values()) 
			prev_o_selected_signal_name = None if source_state.is_Empty() else visible_signal_names[source_state.signal_id]

			changed, o_selected_signal_name = str_combo_with_none("signal", prev_o_selected_signal_name, labels)
			if changed:
				if o_selected_signal_name != None:
					# invert `visible_signal_names` to find the signal id
					signal_name_to_id = {sig_name: sig_id for (sig_id, sig_name) in visible_signal_names.items()}
					selected_signal_id = signal_name_to_id[o_selected_signal_name]
					emit( SelectSignal(id_=source_state.id_, signal_id=selected_signal_id) )
				else:
					emit( SetEmpty(id_=source_state.id_) )
		else:
			im.text("No signals available")

		return util.get_window_rect()
