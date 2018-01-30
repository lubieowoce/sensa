from uniontype import union
from types_util import (
	Id, SignalId,
	PMap_,
)

from eeg_signal import Signal
# Source, Trans, Sink?

NodeId = int

# SourceState, \
# 	Disconnected, \
# 	Connected, \
# = union(
# 'TransState', [
# 	('Disconnected', [('id_', NodeId) ]),

# 	('Connected', 	 [('id_', NodeId),
# 					  ('input_id', SignalId),
# 					  ('output_id', SignalId)]),
# ]
# )


TransState, \
	Disconnected, \
	Connected, \
= union(
'TransState', [
	('Disconnected', [('id_', NodeId),
					  ('output_id', SignalId) ]),

	('Connected', 	 [('id_', NodeId),
					  ('input_id', SignalId),
					  ('output_id', SignalId)]),
]
)

TransAction, \
	Disconnect, \
	Connect, \
= union(
'TransAction', [
	('Disconnect',  [('id_', NodeId)]),
	('Connect',     [('id_', NodeId), ('input_id', SignalId)]),
]
)


SignalOutput, \
	NotReady, \
	Ready, \
= union(
'SignalOutput', [
	('NotReady', []), 
	('Ready', 	 [('signal', Signal)]), 
]
)





def update_trans_node(node_state: TransState, action: TransAction) -> TransState:
	assert action.id_ == node_state.id_

	if action.is_Connect():
		return Connected(id_=node_state.id_, input_id=action.input_id, output_id=node_state.output_id)

	elif action.is_Disconnect():
		if node_state.is_Connected():
			return Disconnected(id_=node_state.id_, output_id=node_state.output_id)
		elif node_state.is_Disconnected():
			return node_state


# OutputNodeAction

OutputNodeEffect, \
	CreateBlankOutput, \
	RemoveOutput, \
= union(
'OutputNodeEffect', [
	('CreateBlankOutput', [('output_id', SignalId)]), # when a node is created
	('RemoveOutput',      [('output_id', SignalId)]), # when a node is removed
]
)

def handle_output_node_effect(
	output_signals: PMap_[SignalId, Signal],
	command: OutputNodeEffect) ->  PMap_[SignalId, Signal]:

	return output_signals.set(command.output_id, SignalOutput.NotReady())