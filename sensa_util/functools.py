from typing import (
	List, Iterable,
	TypeVar,
)
from itertools import islice


A = TypeVar('A'); B = TypeVar('B')


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

