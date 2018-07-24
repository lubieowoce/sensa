from .types import (
	Fun, Anys,
	NonEmpty,
)

from typing import (
	Any,
	TypeVar,
)

A = TypeVar('A'); B = TypeVar('B')


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


