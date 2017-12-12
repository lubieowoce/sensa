from types_util import *

from functools import partial
from itertools import islice


K = TypeVar('K'); A = TypeVar('A')



def err_unsupported_action(action, state):
	raise ValueError("action " + str(action)+ " is not supported in state " + str(state) )


def get(x, path: Iterable[Any]):
	"""
	For exctracting elements out of nested data structures. 
	d = {'xs':[3,5,7], 'ys':['foo', 'bar'] }
	get(d, ['xs', 0]) == 3
	get(d, ['xs', 1]) == 5
	get(d, ['ys', 0]) == 'foo'
	get(d, ['ys', 1]) == 'bar'

	get(d, []) == d
	"""
	res = x
	for index in path:
		res = res[index]
	return res



def id_(x): return x



def chain(*fs):
	"""
	returns a function that applies `fs` left to right.
	chain(f, g, h) == lambda x: h(g(f(x)))
	(reverse order than standard function composition)
	"""
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





def iterate(f, seed: A) -> Iterable[A]:
	res = seed
	while True:
		yield res
		res = f(res)


def take(n: int, iterable: Iterable[A]) -> List[A]:

    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))



def matches(map: PMap_[K, A], *keys, **pairs) -> bool:
	assert len(keys) > 0 or len(pairs) > 0, \
		   "tried to match " + str(map) + " with empty key list and pair dict - probably a bug"
	return \
		all( map.get(key) != None  for key in keys ) and \
		all( map.get(key) == val   for key, val in pairs.items() )