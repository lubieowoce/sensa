from typing import (
	Generic, TypeVar
)

from .types import (
	Fun,
)
A = TypeVar('A'); B = TypeVar('B'); R = TypeVar('R')



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
