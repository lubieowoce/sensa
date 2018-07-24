from imgui import Vec2

from typing import (
	Any,
	Iterable,
	TypeVar
)

A = TypeVar('A'); B = TypeVar('B')



def impossible(msg):
	raise Exception("Internal error: " + msg)





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




