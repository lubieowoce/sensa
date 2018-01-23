from typing import (
	Any,
	Sequence,
	Callable,
	Generic, TypeVar,
)

from pyrsistent import (
	PMap,
	# PVector, 
)


TV = TypeVar
K = TV('K'); A = TV('A'); B = TV('B'); C=TV('C'); R = TV('R')



# class PMap_alias(Generic[K, A]):
# 	pass
# PMap 

class PMap_(Generic[K, A]):
	pass

class PVector_(Generic[A]):
	pass


class IO_(Generic[A]):
	pass
Actions = IO_

class OrderedDict_(Generic[K, A]):
	pass

class DefaultDict_(Generic[K, A]):
	pass

class NDArray(Generic[A]):
	pass


IMGui = IO_ # type of expressions that draw IMGui stuff, but don't do other side effects 
Unit = None

NonEmpty = Sequence

WidgetState = PMap_[str, Any]

Id = int
Effect = PMap_[str, Any]

Action = PMap_[str, Any]

Fun = Callable  # Fun[[int, str], float]  ==  (int, str) -> float
Anys = [Any]


# the numpy stubs from the numpy_stubs folder are passed to mypy 
# through an environment variable in .env like this:
# MYPYPATH=mypy_stubs\mypy-data\numpy-mypy

