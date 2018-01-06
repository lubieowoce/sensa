from typing import (
	Any,
	Tuple,
	List,
	Dict,
	BinaryIO,
	Sequence,
	Generic,
	TypeVar,
	Optional,
	Iterable,
	Callable,
	IO,
)

from pyrsistent import (
	PMap,
	PVector, 
)

# from store import Store

Hz = 1

TV = TypeVar
K = TV('K'); A = TV('A'); B = TV('B'); C=TV('C')

class PMap_(Generic[K, A]):
	pass
class PVector_(Generic[A]):
	pass

class IdEff(Generic[A]):
	""" A computation of type A that uses `get_id` and `emit_effect` """
	pass

class IO_(Generic[A]):
	pass

class NDArray(Generic[A]):
	pass

NonEmpty = Iterable

WidgetState = PMap_[str, Any]

Id = int
Effect = PMap_[str, Any]

Action = PMap_[str, Any]

Fun = Callable  # Fun[[int, str], float]  ==  (int, str) -> float
Anys = [Any]


# the numpy stubs from the numpy_stubs folder are passed to mypy 
# through an environment variable in .env like this:
# MYPYPATH=mypy_stubs\mypy-data\numpy-mypy

