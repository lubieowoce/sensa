from typing import (
	Any,
	Dict, Sequence, List,
)
from types_util import (
	PMap_,
)

from eeg_signal import Signal

from sensa_util import chain


class Trans():
	# An editable closure with some metadata.
	# A partially applied function (with some parameters applied)
	# and some metadata about its name and type. It stores the parameters
	# so that they can be edit - that's why we can't use normal partial application.

	# def __init__(self, name: str, func, func_sig: Sequence[str], params: Dict[str, Any] = None):
	def __init__(self, name: str, func, func_sig: Sequence[str]):
		self.name = name
		self.func = func
		self.func_sig = func_sig
		# TODO: It'll probably be useful to make it possible
		#		to create a Trans without parameters, and then
		# 		set them. Usecase - Transes with parameters that
		# 		have no sensible defaults
		self.inputs = [Signal]
		# only 1-signal inputs for now
		
	def __call__(self, signal: Signal, params: PMap_[str, Any]) -> Signal:
		return self.func(signal, **params)
		
	def are_complete_parameters(self, params: PMap_[str, Any]) -> bool:
		return set(params.keys()) == set(self.func_sig)

	def __repr__(self):
		return self.name + '(' + str(self.func_sig) + ')'



# class TransChain:
# 	# A simple editable list of Transes.
# 	def __init__(self, ts: List[Trans]):
# 		self.ts = ts

# 	def __call__(self, sig: Signal) -> Signal:
# 		return chain(*self.ts)(sig)
