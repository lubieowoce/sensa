

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

# import read as r

# import signal as s
# from eeg_signal import Signal

# import multisignal as m
# from multisignal import MultiSignal

# import main as m

# import biosppy.signals.eeg as e 
