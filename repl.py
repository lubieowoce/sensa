from functools import partial as part
from utils import chain as ch

from importlib import reload as rl
from pprint import pprint as pp
from app import *


def init_state():
	if flags.DEBUG:
		debug_initialize()
		
	current_id = 0
	current_signal_id = 0
	
	# create the initial state	
	state, eff_res = run_eff(initial_state, id=current_id, signal_id=current_signal_id, effects=[])()
	current_id        = eff_res[ID]
	current_signal_id = eff_res[SIGNAL_ID]
	for command in eff_res[EFFECTS]:
			state, eff_res = run_eff(handle, signal_id=current_signal_id)(state, command)
			current_signal_id = eff_res[SIGNAL_ID]

	assert state != None

	# run the initial actions
	for act in INITIAL_ACTIONS:

		state, eff_res = run_eff(update, actions=[], effects=[])(state, act)

		INITIAL_ACTIONS.extend(eff_res[ACTIONS]) # so we can process actions emitted during updating, if any

		for command in eff_res[EFFECTS]:
			state, eff_res = run_eff(handle, signal_id=current_signal_id)(state, command)
			current_signal_id = eff_res[SIGNAL_ID]

	return state



from debug_util import varied_dict_to_str as dts
s = lambda f, g: lambda x: g(f(x))
pd = ch(dts, print)

np = ch(part(map, str),  part(str.join, '\n'),  print)
nps = ch(sorted, np)

from typing import NamedTuple
from collections import OrderedDict
# from sumtype import sumtype

NodeId = NamedTuple('NodeId', [('id_', int)])

InputSlotId  = NamedTuple('InputSlotId',  [('node_id', NodeId), ('ix', int)])
OutputSlotId = NamedTuple('OutputSlotId', [('node_id', NodeId), ('ix', int)])

node_names   = {
	NodeId(0): 'x',
	NodeId(1): 'y',
	NodeId(2): 'z'
}

node_slot_ns = {
	NodeId(0): (1, 2),
	NodeId(1): (2, 0),
	NodeId(2): (0, 1)
}

# links: Set[ Tuple[InputSlotId, OutputSlotId] ] 
links = {
	(OutputSlotId(NodeId(0), ix=0), InputSlotId(NodeId(1), ix=0)),
	(OutputSlotId(NodeId(2), ix=0), InputSlotId(NodeId(0), ix=0)),
	(OutputSlotId(NodeId(0), ix=1), InputSlotId(NodeId(1), ix=1))
}

graph_repr = \
	["{s_val}@[{s_slot_ix}] -> {d_val}#[{d_slot_ix}]"\
	  .format(s_val=node_names[s.node_id], d_val=node_names[d.node_id],
		  	  s_slot_ix=s.ix, d_slot_ix=d.ix)
	 for (s, d) in links]

# graph = {name: {name+'['+_+']'}}

def group_by(xs, key):
	res = OrderedDict()
	for x in xs:
		kx = key(x)
		if kx not in res.keys():
			res[kx] = [ x ]
		else:
			res[kx].append(x)
	return res


# import read as r

# import signal as s
# from eeg_signal import Signal

# import multisignal as m
# from multisignal import MultiSignal

# import main as m

# import biosppy.signals.eeg as e 
