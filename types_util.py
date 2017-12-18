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
	IO,
)

from pyrsistent import (
	PMap,
	PVector, 
)

# from store import Store

Hz = 1

class PMap_(Generic[TypeVar('K'), TypeVar('A')]):
	pass
class PVector_(Generic[TypeVar('A')]):
	pass

WidgetState = PMap_[str, Any]

Id = int

Action = PMap_[str, Any]


# the numpy stubs from the numpy_stubs folder are passed to mypy 
# through an environment variable in .env like this:
# MYPYPATH=mypy_stubs\mypy-data\numpy-mypy

