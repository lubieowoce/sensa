from types_util import *

from functools import partial
from itertools import islice
import imgui as im

def point_delta(a: im.Vec2, b: im.Vec2) -> im.Vec2:
    return im.Vec2(b.x-a.x, b.y-a.y)

def point_offset(a: im.Vec2, b: im.Vec2) -> im.Vec2:
    return im.Vec2(b.x+a.x, b.y+a.y)

def rangeb(low: int, high: int, step: int = 1):
	"""
	Like range, but including the last element.
	rangeb(n, k) == range(n, k+1)
	"""
	return range(low, high+1, step)

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
	raise Exception("Use pyrsistent.get_in !!!")
	res = x
	for index in path:
		res = res[index]
	return res

def set_in(x, *path_n_values: List[ Tuple[Iterable[Any], Any] ]):
	""" For setting values inside nested data structures. """
	transformations = []
	while path_n_values:
		path, val, *path_n_values = path_n_values
		transformations.extend([path, const(val)])

	return x.transform(*transformations)








def only_keys(dict: Dict[K, A], keys: Iterable[K]) -> Dict[K, A]:
	return {key: dict[key] for key in keys}


def const(x): (lambda _: x)

def id_(x): return x

identity = id_



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