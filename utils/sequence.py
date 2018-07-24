from typing import (
	Any,
	Optional, List, Sequence,
	TypeVar,
)

from .either import Either, Left, Right

import flags
import builtins

A = TypeVar('A'); B = TypeVar('B')


def is_sequence_unique(seq: Sequence[A]) -> bool:
	seen = set()
	for x in seq:
		if x in seen:
			return False
		seen.add(x)
	# ran through list without seeing same value twice	
	return True


def is_sequence_uniform(seq: Sequence[Any]) -> bool:
	if len(seq) == 0:
		return True
	else: # list has values
		return sequence_type(seq).is_right




def sequence_type(seq: Sequence[Any]) -> Either[int, type]:
	"""
	Returns either Right(the type of the sequence's values)
			or     Left(index of first badly typed value)
			or	   Left(0) if the sequence is empty
	"""
	if len(seq) == 0:
		return Left(0)
	else:
		first_value_type = type(seq[0])
		is_nth_value_right_type = [ type(value) == first_value_type  for value in seq ]
		
		o_value_of_different_type_ix = optional_index(is_nth_value_right_type, False)
		if o_value_of_different_type_ix == None:
			return Right(first_value_type)
		else: # found a value of different type
			return Left(o_value_of_different_type_ix)


def uniform_sequence_type(seq: Sequence[A]) -> type:
	assert len(seq) > 0, "Sequence is empty, cannot tell what type its values are"
	assert_sequence_is_uniform(seq)

	return type(seq[0])


def assert_sequence_is_uniform(seq: Sequence[A]):
	if not flags.DEBUG:
		return

	if len(seq) == 0:
		return
	else: # seq has values
		e_type_or_ix = sequence_type(seq)
		assert e_type_or_ix.is_right, \
			"Sequence is not of uniform type. First value ({v1}) is of type {t1}, but value at index {ix} ({v2}) is of type {t2}: {}"\
			 .format(v1=seq[0], t1=type(seq[0]), ix=e_type_or_ix.err_val, v2=seq[e_type_or_ix.err_val], t2=type(seq[e_type_or_ix.err_val]))




def optional_index(seq: Sequence[A], of: A) -> Optional[int]:
	"""
	Like list.index, but returns None if `needle` is not present
	instead of throwing ValueError
	"""
	needle = of

	if len(seq) == 0:
		return None

	try:
		return seq.index(needle)
	except ValueError:
		return None


def parts_of_len(xs: Sequence[A], len: int) -> List[List[A]]:
	""" 
	Splits a list into lists of length `n`.
	parts_of_len(3, [0,1,2,3,4,5,6]) == [[0,1,2], [3,4,5], [6]]
	parts_of_len(3, [0]) == [[0]]
	parts_of_len(3, []) == []
	parts_of_len(0,  _ ) == Error
	parts_of_len(-3, _ ) == Error
	"""
	n = len
	len = builtins.len
	assert n >= 1, "Part length must be >= 1 (is {n})" \
				   .format(n=n)

	if len(xs) == 0:
		return []
	else: # xs has values
		parts = []
		while(len(xs) > 0):
			n_elems, xs = xs[:n], xs[n:]
			parts.append(n_elems)
		return parts
