from typing import (
	Any,
	Tuple, List, Dict,
	Generator,
	Generic, TypeVar,
	NamedTuple,
)
from utils.types import (
	Id, SignalId,
	Fun, 
)
import types
import inspect
from inspect import iscoroutinefunction as is_coroutine_function

from enum import Enum
# import flags

A = TypeVar('A')

class enable_class_getitem(type):
	def __getitem__(cls, item):
		return cls.__class_getitem__(cls, item)


# to enable Eff[[x, y, z], T] in signatures
class Eff(metaclass=enable_class_getitem):
	def __class_getitem__(cls, items: Tuple[List['EffId'], type]):
		return _Eff(*items)

EffId = str
_Eff = NamedTuple('_Eff', [('effects', List[EffId]), ('type', type)])



ID        = "ID"
EFFECTS   = "EFFECTS"
SIGNAL_ID = "SIGNAL_ID"
ACTIONS   = "ACTIONS"



eff_type_operation_name = {
	ID:        'get_id',
	EFFECTS:   'emit_effect',
	SIGNAL_ID: 'get_signal_id',
	ACTIONS:   'emit',
}

kwarg_to_eff_type = {
	'id': 		 ID,
	'effects':   EFFECTS,
	'signal_id': SIGNAL_ID,
	'actions':   ACTIONS,
}




# The generic type for annotating generators is: 
# Generator[yield_type, send_type, return_type]

# for an @effectful function, it's going to be
# Generator[msg_type, msg_result_type, return_type]
#	where msg_type can also be a union of the required effects.

def run_eff(comp: Eff[..., A], **initial_states) -> Tuple[A, Dict]:

	states = {kwarg_to_eff_type[name]: val for (name, val) in initial_states.items()}

	response = None
	while True:
		try:
			req = comp.send(response)
		except StopIteration as done:
			# `comp` finished
			return (done.value, states)

		if req == EffMsg.GetStates:
			response = states
		else:
			raise ValueError(
				"Invalid Eff request - {req} : {req.__class__.__qualname__}" \
					.format(req=req)
			)



def effectful(f):
	annotation_msg = (
		'@effectful function {f.__qualname__!r} must have return type annotation ' +
		'of the form Eff[[EFFECT_X, EFFECT_Y], A]'
	)

	try:
		ret_type = f.__annotations__['return']
	except KeyError:
		raise TypeError(annotation_msg.format(f=f)) from None

	if not isinstance(ret_type, _Eff):
		raise TypeError(annotation_msg.format(f=f))

	if not (is_coroutine_function(f) or is_decorated_generator_coroutine(f)):
		msg = '@effectful function {f.__qualname__!r} must be async or a @coroutine'
		raise TypeError(msg.format(f=f))


	f.__effect_types__ = ret_type.effects
	return f


def is_decorated_generator_coroutine(f: Fun) -> bool:
	return f.__code__.co_flags & inspect.CO_ITERABLE_COROUTINE


class EffMsg(Enum):
	GetStates = 0



@effectful
@types.coroutine
def get_id() -> Eff[[ID], Id]:
	states = yield EffMsg.GetStates
	res = states[ID]
	states[ID] += 1
	return res


@effectful
@types.coroutine
def get_signal_id() -> Eff[[SIGNAL_ID], SignalId]:
	states = yield EffMsg.GetStates
	res = states[SIGNAL_ID]
	states[SIGNAL_ID] += 1
	return res


@effectful
@types.coroutine
def emit(action: Any) -> Eff[[ACTIONS], None]:
	states = yield EffMsg.GetStates
	states[ACTIONS].append(action)


@effectful
@types.coroutine
def emit_effect(cmd: Any) -> Eff[[EFFECTS], None]:
	states = yield EffMsg.GetStates
	states[EFFECTS].append(cmd)



# -------------------

@effectful
async def get_ids(n: int) -> Eff[[ID], List[Id]]:
	ids = []
	for _ in range(n):
		ids.append(await get_id())
	return ids


@effectful
async def get_signal_ids(n: int) -> Eff[[SIGNAL_ID], List[SignalId]]:
	ids = []
	for _ in range(n):
		ids.append(await get_signal_id())
	return ids


