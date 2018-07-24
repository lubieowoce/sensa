from typing import (
	TypeVar,
)

from .types import (
	PMap_,
)

from .sequence import (
	is_sequence_unique,
)

from pyrsistent import pmap

A = TypeVar('A'); B = TypeVar('B'); K = TypeVar('K');



def invert(d: PMap_[A, B]) -> PMap_[B, A]:
	assert is_sequence_unique(d.values()), d+" has duplicate values, so it's not invertible"
	return pmap({val: key for (key, val) in d.items()})


def matches(map: PMap_[K, A], *keys, **pairs) -> bool:
	assert len(keys) > 0 or len(pairs) > 0, \
		   "tried to match " + str(map) + " with empty key list and pair dict - probably a bug"
	return \
		all( map.get(key) != None  for key in keys ) and \
		all( map.get(key) == val   for key, val in pairs.items() )