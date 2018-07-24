from typing import (
	Any,
	Dict, Iterable,
	TypeVar,
)

from .types import (
	PMap_, Fun,
)

from .sequence import (
	is_sequence_unique, sequence_type,
)

import flags

A = TypeVar('A'); B = TypeVar('B'); K = TypeVar('K');



def uniform_dict_type(dictionary: Dict[K, A]) -> type:
	assert_dict_is_uniform(dictionary)
	assert len(dictionary) > 0, "Dictionary is empty, cannot tell what type the values are"

	first_value = dictionary.values()[0]
	return type(first_value)




def only_keys(dict: Dict[K, A], keys: Iterable[K]) -> Dict[K, A]:
	return {key: dict[key] for key in keys}



def dict_to_function(dictionary: Dict[K, A]) -> Fun[[K], A]:
	return lambda k: dictionary[k]
	



def assert_dict_is_uniform(dictionary: Dict[K, Any]):
	if not flags.DEBUG:
		return

	if len(dictionary) == 0:
		return
	else: # dictionary has values
		values = list(dictionary.values())
		e_type_or_ix = sequence_type(values)
		assert e_type_or_ix.is_right, \
			"Sequence is not of uniform type. First value ({v1}) is of type {t1}, but another value ({v2}) is of type {t2}: {}"\
			 .format(v1=values[0], t1=type(values[0]), v2=values[e_type_or_ix.err_val], t2=type(values[e_type_or_ix.err_val]))

