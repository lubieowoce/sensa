from typing import (
	Any,
	Dict, Optional, Sequence, List, Iterable,
	Generic,
)
from types_util import (
	K, A, B, R, 
	PMap_,
	NonEmpty,
	Fun, Anys,
	IO_, IMGui, 
)


import builtins
# from functools import partial
from itertools import islice
from collections import namedtuple
from pyrsistent import pmap

import imgui as im
from imgui import Vec2

import flags

def impossible(msg):
	raise Exception("Internal error: " + msg)


Rect = namedtuple("Rect", ['top_left', 'bottom_right'])

def rect_width(rect: Rect) -> float:
	top_left, bottom_right = rect
	return bottom_right.x - top_left.x

def rect_height(rect: Rect) -> float:
	top_left, bottom_right = rect
	return bottom_right.y - top_left.y

def get_mouse_position() -> IO_[Vec2]:
	io = im.get_io()
	return io.mouse_pos

def get_window_rect() -> IO_[Rect]:
	""" To be used only in imgui code """
	window_top_left = im.get_window_position()
	width, height = im.get_window_size()
	window_bottom_right = Vec2(window_top_left.x + width,
								  window_top_left.y + height)
	return Rect(window_top_left, window_bottom_right)


def get_window_content_rect() -> IO_[Rect]:
	TITLE_BAR_HEIGHT = 20
	window_top_left = im.get_window_position()
	content_top_left = Vec2(window_top_left.x,  window_top_left.y + TITLE_BAR_HEIGHT)
	width, height = im.get_window_size()
	window_bottom_right = Vec2(window_top_left.x + width,
								  window_top_left.y + height)
	return Rect(content_top_left, window_bottom_right)
	

def is_in_rect(point: Vec2, rect: Rect) -> bool:
	top_left, bottom_right = rect
	return \
		top_left.x <= point.x <= bottom_right.x and \
		top_left.y <= point.y <= bottom_right.y


def add_rect_coords(draw_list, top_left: Vec2, bottom_right: Vec2, color) -> IMGui[None]:
	""" Necessary because i haven't added the bindings for add_rect yet """
	top_right   = Vec2(bottom_right.x, top_left.y)
	bottom_left = Vec2(top_left.x, bottom_right.y)
	# draw rect clockwise from top left
	draw_list.add_line(top_left, top_right, color=color)
	draw_list.add_line(top_right, bottom_right, color=color)
	draw_list.add_line(bottom_right, bottom_left, color=color)
	draw_list.add_line(bottom_left, top_left, color=color)

def add_rect(draw_list, rect: Rect, color) -> IMGui[None]:
	top_left, bottom_right = rect
	add_rect_coords(draw_list, top_left, bottom_right, color)


def assert_all(xs: Sequence[A], pred: Fun[[A], bool], msg: str = "{}"):
	for x in xs:
		assert pred(x), msg.format(x)
		
# def all_satisfy(xs: Sequence[A], pred: Fun[[A], bool]) -> bool:
# 	return all()

def one_is_true_of(x: A, preds: Sequence[Fun[[A], bool]]) -> bool:
	return one_is_true([ pred(x) for pred in preds ])

def one_is_true(bools: Sequence[bool]) -> bool:
	return bools.count(True) == 1



class Either(Generic[A, B]):
	pass

class Left(Either):
	def __init__(left, val): left.val = val
	@property
	def is_left(left): return True
	@property
	def is_right(left): return False
	@property
	def err_val(left): return left.val
	@property
	def res_val(left): raise Exception("Tried calling res_val on " + str(left))
	def __str__(left): return "Left({})".format(left.val)

class Right(Either):
	def __init__(right, val): right.val = val
	@property
	def is_left(right): return False
	@property
	def is_right(right): return True
	@property
	def err_val(right): raise Exception("Tried calling err_val on " + str(right))
	@property
	def res_val(right): return right.val
	def __str__(right): return "Right({})".format(right.val)

def either(e: Either[A, B], l_fn: Fun[[A], R], r_fn: Fun[[A], R]) -> R:
	return  l_fn(e.val) if e.is_left else r_fn(e.val)


class Maybe(Generic[A]):
	__slots__ = ()

class Nothing(Maybe):
	__slots__ = ()
	def __init__(nothing): pass

	@property
	def is_nothing(nothing): return True

	def is_Nothing(nothing): return True

	@property
	def is_just(nothing):   return False

	def is_Just(nothing):   return False

	@property
	def val(nothing): raise Exception("Tried to get value of Nothing")

	def get_val(nothing): return None

	def map(nothing, fn): return nothing

	# >> (bind)
	def __rshift__(nothing, fn): return nothing

	def __repr__(just): return 'Nothing()'

class Just(Maybe):
	__slots__ = ('_val',)
	def __init__(just, val): just._val = val

	@property

	def is_nothing(just): return False

	def is_Nothing(just): return False

	@property
	def is_just(just):    return True

	def is_Just(just):    return True

	@property
	def val(just): return just._val

	def get_val(just): return just._val

	def map(just, fn): return Just(fn(just._val))

	# >> (bind)
	def __rshift__(just, fn): return fn(just._val)

	def __repr__(just): return 'Just({})'.format(just._val)



def dict_to_function(dictionary: Dict[K, A]) -> Fun[[K], A]:
	return lambda k: dictionary[k]



def is_sequence_unique(seq: Sequence[A]) -> bool:
	seen = set()
	for x in seq:
		if x in seen:
			return False
		seen.add(x)
	# ran through list without seeing same value twice	
	return True
	

def invert(d: PMap_[A, B]) -> PMap_[B, A]:
	assert is_sequence_unique(d.values()), d+" has duplicate values, so it's not invertible"

	return pmap({val: key for (key, val) in d.items()})



def is_sequence_uniform(seq: Sequence[Any]) -> bool:
	if len(seq) == 0:
		return True
	else: # list has values
		return sequence_type(sequence).is_right




def sequence_type(seq: Sequence[Any]) -> Either[int, type]:
	"""
	Returns either Right(the type of the sequence's values)
			or     Left(index of first badly typed value)
			or	   Left(0) if the sequence is empty
	"""
	if len(seq) == 0:
		return Left(0)
	else:
		first_value_type = type(seq[0])
		is_nth_value_right_type = [ type(value) == first_value_type  for value in seq ]
		
		o_value_of_different_type_ix = optional_index(is_nth_value_right_type, False)
		if o_value_of_different_type_ix == None:
			return Right(first_value_type)
		else: # found a value of different type
			return Left(o_value_of_different_type_ix)


def uniform_sequence_type(seq: Sequence[A]) -> type:
	assert len(seq) > 0, "Sequence is empty, cannot tell what type its values are"
	assert_sequence_is_uniform(seq)

	return type(seq[0])


def assert_sequence_is_uniform(seq: Sequence[A]):
	if not flags.DEBUG:
		return

	if len(seq) == 0:
		return
	else: # seq has values
		e_type_or_ix = sequence_type(seq)
		assert e_type_or_ix.is_right, \
			"Sequence is not of uniform type. First value ({v1}) is of type {t1}, but value at index {ix} ({v2}) is of type {t2}: {}"\
			 .format(v1=seq[0], t1=type(seq[0]), ix=e_type_or_ix.err_val, v2=seq[e_type_or_ix.err_val], t2=type(seq[e_type_or_ix.err_val]))


def uniform_dict_type(dictionary: Dict[K, A]) -> type:
	assert_dict_is_uniform(dictionary)
	assert len(dictionary) > 0, "Dictionary is empty, cannot tell what type the values are"

	first_value = dictionary.values()[0]
	return type(first_value)


def assert_dict_is_uniform(dictionary: Dict[K, Any]):
	if not flags.DEBUG:
		return

	if len(dictionary) == 0:
		return
	else: # dictionary has values
		values = list(dictionary.values())
		e_type_or_ix = sequence_type(values)
		assert e_type_or_ix.is_right, \
			"Sequence is not of uniform type. First value ({v1}) is of type {t1}, but another value ({v2}) is of type {t2}: {}"\
			 .format(v1=values[0], t1=type(values[0]), v2=values[e_type_or_ix.err_val], t2=type(values[e_type_or_ix.err_val]))






def optional_index(seq: Sequence[A], of: A) -> Optional[int]:
	"""
	Like list.index, but returns None if `needle` is not present
	instead of throwing ValueError
	"""
	needle = of

	if len(seq) == 0:
		return None

	try:
		return seq.index(needle)
	except ValueError:
		return None


def parts_of_len(xs: Sequence[A], len: int) -> List[List[A]]:
	""" 
	Splits a list into lists of length `n`.
	parts_of_len(3, [0,1,2,3,4,5,6]) == [[0,1,2], [3,4,5], [6]]
	parts_of_len(3, [0]) == [[0]]
	parts_of_len(3, []) == []
	parts_of_len(0,  _ ) == Error
	parts_of_len(-3, _ ) == Error
	"""
	n = len
	len = builtins.len
	assert n >= 1, "Part length must be >= 1 (is {n})" \
				   .format(n=n)

	if len(xs) == 0:
		return []
	else: # xs has values
		parts = []
		while(len(xs) > 0):
			n_elems, xs = xs[:n], xs[n:]
			parts.append(n_elems)
		return parts



def limit_upper(x: A, high: A) -> A:
	return min(x, high)

def limit_lower(x: A, low: A) -> A:
	return max(low, x)

def clamp(low, x, high):
	return max(low, min(x, high))


def point_subtract_offset(a: Vec2, offset: Vec2) -> Vec2:
	return Vec2(a.x-offset.x, a.y-offset.y)

def point_offset(a: Vec2, offset: Vec2) -> Vec2:
	return Vec2(a.x+offset.x, a.y+offset.y)


def range_incl(first: int, last: int, step: int = 1) -> Iterable[int]:
	"""
	Like range, but including the last element.
	rangeb(n, k) == range(n, k+1)
	"""
	return range(first, last+1, step)

def err_unsupported_action(action, state):
	raise Exception("Action " + str(action)+ " is not supported in state " + str(state) )

def bad_action(**kwargs):
	if flags.DEBUG:
		if 'msg' in kwargs:
			err_text = kwargs['msg']

		elif 'action' in kwargs and 'state' in kwargs:
			action = kwargs['action']
			state = kwargs['state']
			err_text = "Action " + str(action)+ " shouldn't happen in " + str(state)

		else:
			err_text = "Bad action"

		raise Exception(err_text)

def get_in(path: Iterable[Any], x: A) -> B:
	"""
	For exctracting elements out of nested data structures. 
	d = {'xs':[3,5,7], 'ys':['foo', 'bar'] }
	get(d, ['xs', 0]) == 3
	get(d, ['xs', 1]) == 5
	get(d, ['ys', 0]) == 'foo'
	get(d, ['ys', 1]) == 'bar'

	get(d, []) == d
	"""
	# raise Exception("Use pyrsistent.get_in !!!")
	res = x
	for index in path:
		res = res[index]
	return res

# def set_in(x, *path_n_values: List[ Tuple[Iterable[Any], Any] ]):
# 	""" For setting values inside nested data structures. """
# 	transformations = []
# 	while path_n_values:
# 		path, val, *path_n_values = path_n_values
# 		transformations.extend([path, const(val)])

# 	return x.transform(*transformations)




def set_in_tuple(path: NonEmpty[Any], val: B, tup: tuple) -> tuple:
	assert is_namedtuple(tup), \
			"{} is not a namedtuple, it's a {}".format(tup, type(tup))

	if len(path) == 1:
		ix = path[0]
		return tup._replace(**{ix: val})
	else: # path ~~ ix, *ixs
		ix, *path2 = path
		tup_in = getattr(tup, ix)
		return tup._replace(**{ix: set_in_tuple(path2, val, tup_in)})


def modify_in_tuple(path: NonEmpty[Any], fn: Fun[Anys, Any], tup: tuple) -> tuple:
	assert is_namedtuple(tup), \
			"{} is not a namedtuple, it's a {}".format(tup, type(tup))

	if len(path) == 1:
		ix = path[0]
		a = getattr(tup, ix)
		return tup._replace(**{ix: fn(a)})
	else: # path ~~ ix, *ixs
		ix, *path2 = path
		tup_in = getattr(tup, ix)
		return tup._replace(**{ix: modify_in_tuple(path2, fn, tup_in)})




# def set_in(path: NonEmpty[Any], val: B, x: A) -> A:
# 	if len(path) == 1:
# 		ix = path[0]
# 		return tup._replace(**{ix: val})
# 	else: # path ~~ ix, *ixs
# 		ix, *path2 = path
# 		tup_in = getattr(tup, ix)
# 		return tup._replace(**{ix: set_in_tuple(path2, val, tup_in)})


def is_namedtuple(x: A) -> bool:
	return isinstance(x, tuple) and '_replace' in dir(x)







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