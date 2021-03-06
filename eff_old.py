from typing import (
	Any,
	Tuple, List, Dict,
	Generic,
)
from utils.types import (
	Id, SignalId,
	A,
	Fun, 
)
import functools
from utils import identity

import flags

import builtins
# Only way to make a function visible to all modules.
# https://stackoverflow.com/a/15959638

# EffType = str

class EffVal(Generic[A]):
	pass
	# def __init__(self, *eff_types: Tuple[EffType]):
	# 	self.eff_types = eff_types

Eff = lambda *args: EffVal


ID        = "ID"
EFFECTS   = "EFFECTS"
SIGNAL_ID = "SIGNAL_ID"
ACTIONS   = "ACTIONS"





def mk_get_id(state_dict):
	def _get_id() -> Eff(ID)[int]:
		cur_id = state_dict[ID]
		state_dict[ID] += 1
		return cur_id
	return _get_id

def mk_emit_effect(state_dict):
	def _emit_effect(effect) -> Eff(EFFECTS)[None]:
		state_dict[EFFECTS].append(effect)

	return _emit_effect


def mk_get_signal_id(state_dict):
	def _get_signal_id() -> Eff(SIGNAL_ID)[int]:
		cur_sig_id = state_dict[SIGNAL_ID]
		state_dict[SIGNAL_ID] += 1
		return cur_sig_id
	return _get_signal_id

def mk_emit(state_dict):
	def _emit(action) -> Eff(ACTIONS)[None]:
		state_dict[ACTIONS].append(action)
	return _emit


mk_eff_type_operation = {
	ID:        mk_get_id,
	EFFECTS:   mk_emit_effect,
	SIGNAL_ID: mk_get_signal_id,
	ACTIONS:   mk_emit,
}

eff_type_operation_name = {
	ID:        'get_id',
	EFFECTS:   'emit_effect',
	SIGNAL_ID: 'get_signal_id',
	ACTIONS:   'emit',
}



# Eff(ID, EFFECTS)[A] -> gets ids, emits effects, returns A
# Eff(ACTIONS)[A] -> emits actions, returns A


kwarg_to_eff_type = {
	'id': 		 ID,
	'effects':   EFFECTS,
	'signal_id': SIGNAL_ID,
	'actions':   ACTIONS,
}

# --------------

BUILTINS_EXECUTING_EFF_FLAG = '__EXECUTING_EFF'

def builtins_flag_for_effect_type(eff_t) -> str:
	return '__EXECUTING_EFF_TYPE_' + eff_t

# --------------

def run_eff(f: Fun[..., Eff(...)[A]],
			**initial_states_kw: Dict[str, Any]) \
			-> Fun[..., Tuple[A, Dict[str, Any]]]:

	effect_types_used = [kwarg_to_eff_type[name] for name in initial_states_kw.keys()]
	initial_states = {kwarg_to_eff_type[name]: val for (name, val) in initial_states_kw.items()}

	if flags.DEBUG:
		assert set(f.__effect_types__) <= set(initial_states.keys()), \
			"Not enough initial_states in initial_states_kw for specified effect types:" + str(f.__effect_types__) +", initial_states: " + str(initial_states)

	def result_fn(*args, **kwargs) -> Fun[..., Tuple[A, ...]]:

		# set the main flag
		setattr(builtins, BUILTINS_EXECUTING_EFF_FLAG, True)

		# inject all required operations (and their flags) into builtins
		for EFF_T in effect_types_used:
			operation_name = eff_type_operation_name[EFF_T]
			operation      = mk_eff_type_operation[EFF_T](initial_states)
			setattr(builtins, operation_name, operation)
			setattr(builtins, builtins_flag_for_effect_type(EFF_T), True)

		result = f(*args, **kwargs)

		# remove the operations from builtins
		for EFF_T in effect_types_used:
			operation_name = eff_type_operation_name[EFF_T]
			delattr(builtins, operation_name)
			delattr(builtins, builtins_flag_for_effect_type(EFF_T))

		# remove the main flag
		delattr(builtins, BUILTINS_EXECUTING_EFF_FLAG)

		return result, initial_states

	return result_fn

# ----------------

if flags.DEBUG:
	def effectful(*effect_types):

		def effectful_decorator(f):

			@functools.wraps(f) # preserve function name, signature, module name etc
			def wrapped(*args, **kwargs):
				assert is_in_eff(), "`is_in_eff()` failed. This computation is meant to be run using `run_eff`"
				assert all_eff_operations_present(*effect_types), "Some eff operations are missing, (or their flags aren't set - `eff` bug)"

				return f(*args, **kwargs)

			wrapped.__effect_types__ = effect_types
			return wrapped

		return effectful_decorator

else: # not flags.DEBUG -> no runtime check
	effectful = lambda *effect_types: (
					lambda f: f 
				) 

# -----------------

def is_in_eff() -> bool:
	return BUILTINS_EXECUTING_EFF_FLAG in dir(builtins)

def all_eff_operations_present(*effect_types) -> bool:
	return (     all(builtins_flag_for_effect_type(eff_t) in dir(builtins) for eff_t in effect_types)
			and  all(      eff_type_operation_name[eff_t] in dir(builtins) for eff_t in effect_types))
# --------------------------



@effectful()
def eff_operation(name: str) -> Fun[..., Any]:
	"""
	Convenience - Add `emit = get_eff_operation('emit')`
	to get linters to stop complaining about undefined operations.
	(Actually just retrieves stuff from builtins)
	"""

	assert name in dir(builtins), "Operation '" + name +"' not available"
	return getattr(builtins, name)



# -------------------

@effectful(SIGNAL_ID)
def get_signal_ids(n: int) -> Eff(SIGNAL_ID)[List[SignalId]]:
	get_signal_id = eff_operation('get_signal_id')

	ids = []
	for _ in range(n):
		ids.append(get_signal_id())
	return ids



@effectful(ID)
def get_ids(n: int) -> Eff(ID)[List[Id]]:
	get_id = eff_operation('get_id')
	
	ids = []
	for _ in range(n):
		ids.append(get_id())
	return ids


# ============================

@effectful(ID, EFFECTS)
def f() -> Eff(ID, EFFECTS)[Dict[str, Id]]:
	xi = get_id()
	yi = get_id()
	emit_effect('print 1')
	return {'x': xi, 'y': yi}

@effectful(SIGNAL_ID, ACTIONS)
def f2() -> Eff(SIGNAL_ID, ACTIONS)[Dict[str, Id]]:
	xi = get_signal_id()
	yi = get_signal_id()
	emit('print 1')
	return {'x': xi, 'y': yi}

@effectful(ID, EFFECTS)
def g(key):
	emit_effect("jump")
	d = f()
	zi = get_id()
	d[key] = zi
	return d












