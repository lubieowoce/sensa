from typing import (
	Generic, TypeVar
)

A = TypeVar('A')

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
