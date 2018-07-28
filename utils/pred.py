from typing import (
	Sequence,
	TypeVar
)
from .types import (
	Fun,
)

A = TypeVar('A')

def assert_all(xs: Sequence[A], pred: Fun[[A], bool], msg: str = "predicate {pred} failed for item {i} of {len} - {val}"):
	for (i, x) in enumerate(xs):
		assert pred(x), msg.format(pred=pred.__name__, i=i, len=len(xs), val=x)
		
# def all_satisfy(xs: Sequence[A], pred: Fun[[A], bool]) -> bool:
# 	return all()


def one_is_true_of(x: A, preds: Sequence[Fun[[A], bool]]) -> bool:
	return one_is_true([ pred(x) for pred in preds ])


def one_is_true(bools: Sequence[bool]) -> bool:
	return bools.count(True) == 1

