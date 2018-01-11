from types_util import *
from eeg_signal import Signal

from sensa_util import chain


class Trans():
	# An editable closure with some metadata.
	# A partially applied function (with some parameters applied)
	# and some metadata about its name and type. It stores the parameters
	# so that they can be edit - that's why we can't use normal partial application.

	def __init__(self, name: str, func, func_sig: Sequence[str], params: Dict[str, Any] = None):
		self.name = name
		self.func = func
		self.params = params if params!=None else {}
		self.func_sig = func_sig
		# TODO: It'll probably be useful to make it possible
		#		to create a Trans without parameters, and then
		# 		set them. Usecase - Transes with parameters that
		# 		have no sensible defaults
		self.inputs = [Signal]
		# only 1-signal inputs for now
		
	def __call__(self, signal: Signal) -> Signal:
		return self.func(signal, **self.params)
		
	def has_all_parameters(self) -> bool:
		return set(self.params.keys()) == set(self.func_sig)

	def __repr__(self):
		return self.name + '(' + str(self.params) + ')'

class TransChain:
	# A simple editable list of Transes.
	def __init__(self, ts: List[Trans]):
		self.ts = ts

	def __call__(self, sig: Signal) -> Signal:
		return chain(*self.ts)(sig)
