from types_util import *


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