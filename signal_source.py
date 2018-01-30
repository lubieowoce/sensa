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
from sensa_util import impossible

from eff import (
	Eff, effectful,
	ID, EFFECTS, SIGNAL_ID, ACTIONS,
	eff_operation,
)
from uniontype import union

from node import (
	SignalOutput, OutputNodeEffect
)

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
	('Empty', [('id_', Id), ('output_id', SignalId)]),
	('Full',  [('id_', Id), ('signal_id', SignalId), ('output_id', SignalId)])
	#                        ^ the source signal
]
)

SourceAction, \
	SetEmpty, \
	SelectSignal, \
= union(
'SourceAction', [
	('SetEmpty',     [('id_', Id)]), \
	('SelectSignal', [('id_', Id), ('signal_id', SignalId)]), \
]
)

SourceEffect, \
	AddOutput, \
	NoOutput, \
= union(
'SourceEffect', [
	('AddOutput', [('id_', Id)]),
	('NoOutput',  [('id_', Id)]),
]
)

@effectful(ID, SIGNAL_ID, EFFECTS)
def initial_source_state():
	get_id = eff_operation('get_id')
	get_signal_id = eff_operation('get_signal_id')
	emit_effect = eff_operation('emit_effect')

	id_ = get_id()
	output_id = get_signal_id()
	emit_effect( OutputNodeEffect.CreateBlankOutput(output_id=output_id) )
	return SourceState.Empty(id_=id_, output_id=output_id)


@effectful(EFFECTS)
def update_source(source_state: SourceState, action: SourceAction) -> Eff(EFFECTS)[SourceState]:
	assert source_state.id_ == action.id_
	emit_effect = eff_operation('emit_effect')
	old_state = source_state

	if action.is_SetEmpty():
		emit_effect( NoOutput(id_=old_state.id_) )
		return Empty(id_=old_state.id_, output_id=old_state.output_id)

	elif action.is_SelectSignal():
		emit_effect( AddOutput(id_=old_state.id_) )
		return Full(id_=old_state.id_, signal_id=action.signal_id, output_id=old_state.output_id)
	else:
		impossible("Unsupported action: "+action)
		return old_state



@effectful(ACTIONS)
def signal_source_window(
	source_state: SourceState,
	signal_data:  PMap_[SignalId, Signal],
	signal_names: PMap_[SignalId, str]) -> Eff(ACTIONS)[IMGui[None]]:

	emit = eff_operation('emit')


	source_name = "Source (id={id}, out={out})".format(id=source_state.id_, out=source_state.output_id)

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


def handle_source_effect(
	state: SourceState,
	signal_data: PMap_[SignalId, Signal],
	command: SourceEffect) -> SignalOutput:

	assert state.id_ == command.id_

	if   command.is_NoOutput():
		return SignalOutput.NotReady()

	elif command.is_AddOutput():
		assert state.is_Full()

		signal_id = state.signal_id
		signal = signal_data[signal_id]
		return SignalOutput.Ready(signal=signal)

	else:
		impossible("Invalid command: "+command)