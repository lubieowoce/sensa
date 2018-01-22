from typing import (
	Tuple, List,
	Generic,
)
from types_util import (
	Id, Effect,
	A,
	Fun, Anys,
)

from sensa_util import identity

from flags import DEBUG

import builtins
# Only way to make a function visible to all modules.
# https://stackoverflow.com/a/15959638


class IdEff(Generic[A]):
	""" A computation of type A that uses `get_id` and `emit_effect` """
	pass


def run_id_eff(f: Fun[Anys, IdEff[A]], id: Id) -> Fun[ Anys,  Tuple[A, Id, List[Effect]] ]:
	"""
	Takes a starting id state.
	Wraps `f` in an isolated environment where
	`f` can use these effectful operations:
	- get_id() -> Id
	- emit_effect(effect) -> ()
	```
	x = f()
	x, id, effects = run_id_eff(f, id=0)() 
	```
	"""  
	def result_fn(*args, **kwargs) -> Tuple[A, Id, List[Effect]]:

		__current_id = id
		def _get_id() -> IdEff[Id]:
			nonlocal __current_id

			the_id = __current_id
			__current_id += 1

			return the_id

		__effects = []
		def _emit_effect(effect) -> IdEff[None]:
			nonlocal __effects
			__effects.append(effect)

		builtins.executing_in_id_eff = True # for debug purposes
		builtins.get_id = _get_id
		builtins.emit_effect = _emit_effect

		# assert is_in_id_eff(), "is_in_id_eff failed."
		# assert "get_id" in globals(), "get_id not in globals in result_fn. globals:" + str(dict(globals()))
		# print("args", args)
		# print("kwargs", kwargs)

		result = f(*args, **kwargs)

		del builtins.executing_in_id_eff
		del builtins.get_id
		del builtins.emit_effect

		return result, __current_id, __effects
	return result_fn

with_id_and_effects = run_id_eff
rie = run_id_eff


def is_in_id_eff():
	return \
		'executing_in_id_eff' in dir(builtins) \
		and 'get_id'          in dir(builtins) \
		and 'emit_effect'     in dir(builtins)

if DEBUG:
	def id_and_effects(f):
		"""
		Decorator that adds a runtime check to `f`.
		It checks if, when f is executed, it is executed within `run_id_eff`.
		"""
		def wrapped(*args, **kwargs):
			assert is_in_id_eff(), "`is_in_id_eff` failed. This computation is meant to be run using `run_id_eff`.."
			return f(*args, **kwargs)
		return wrapped

else: # not DEBUG
	id_and_effects = identity  # no runtime check




@id_and_effects
def f() -> IdEff[None]:
	xi = get_id()
	yi = get_id()
	emit_effect('print 1')
	return {'x': xi, 'y': yi}

@id_and_effects
def g(key):
	emit_effect("jump")
	d = f()
	zi = get_id()
	d[key] = zi
	return d

@id_and_effects
def get_ids(n: int) -> IdEff[List[Id]]:
    ids = []
    for _ in range(n):
        ids.append(get_id())
    return ids

	
