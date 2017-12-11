from types_util import *

from functools import partial
from itertools import islice

def chain(*fs):
	def chained(x):
		res = x
		for f in fs:
			res = f(res)
		return res
	return chained


def sequence(*fs):
	""" fs: [() -> None] -> (() -> None) """
	def chained():
		for f in fs:
			f()
	return chained


def put(x, fn):
	return fn(x)

def dict_set_all(target, source):
	for key, value in source.items():
		target[key] = value


K = TypeVar('K');   A = TypeVar('A')


def setitem(d: Dict[K, A], key: K, value: A):
	d[key] = value


def err_unsupported_action(action, state):
	raise ValueError("action " + str(action)+ " not supported in state " + str(state) )


def matches(map: PMap_[K, A], *keys, **pairs) -> bool:
	assert len(keys) > 0 or len(pairs) > 0, \
		   "tried to match " + str(map) + " with empty key list and pair dict - probably a bug"
	return \
		all( map.get(key) != None  for key in keys ) and \
		all( map.get(key) == val   for key, val in pairs.items() )


def iterate(f, seed: A) -> Iterable[A]:
	res = seed
	while True:
		yield res
		res = f(res)


def take(n: int, iterable: Iterable[A]) -> List[A]:

    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))