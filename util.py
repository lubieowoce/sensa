from types_util import *

from functools import partial
from itertools import islice
import imgui as im
from imgui import Vec2
from collections import namedtuple


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


def add_rect(draw_list, top_left: Vec2, bottom_right: Vec2, color) -> IO_[None]:
	""" Necessary because i haven't added the bindings for add_rect yet """
	top_right   = Vec2(bottom_right.x, top_left.y)
	bottom_left = Vec2(top_left.x, bottom_right.y)
	# draw rect clockwise from top left
	draw_list.add_line(top_left, top_right, color=color)
	draw_list.add_line(top_right, bottom_right, color=color)
	draw_list.add_line(bottom_right, bottom_left, color=color)
	draw_list.add_line(bottom_left, top_left, color=color)

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


def range_incl(low: int, high: int, step: int = 1) -> Iterable[int]:
	"""
	Like range, but including the last element.
	rangeb(n, k) == range(n, k+1)
	"""
	return range(low, high+1, step)

def err_unsupported_action(action, state):
	raise ValueError("action " + str(action)+ " is not supported in state " + str(state) )



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