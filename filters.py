from typing import (
	Tuple, Sequence
)

from pyrsistent import m, pmap
from collections import OrderedDict
from functools import partial as part
# import numpy as np
from scipy.signal import butter, lfilter
from eeg_signal import Signal
from trans import Trans

Hz = 1



# Filters based on:
# https://stackoverflow.com/questions/25191620/creating-lowpass-filter-in-scipy-understanding-methods-and-units

def butter_lowpass_coeffs(cutoff_freq: float, sampling_freq: float, type: str, order=5) -> Tuple[Sequence[float], Sequence[float]]:
	nyquist_freq = 0.5 * sampling_freq
	normalized_cutoff_freq = cutoff_freq / nyquist_freq
	b_v, a_v = butter(order, normalized_cutoff_freq, btype=type, analog=False)
	# ^ coefficient vectors descirbing the filter
	return b_v, a_v

def simple_filter_raw(data: Sequence[float], cutoff_freq: float, sampling_freq: float, type: str, order=5) -> Sequence[float]:
	b_v, a_v = butter_lowpass_coeffs(cutoff_freq, sampling_freq, type, order)
	filtered = lfilter(b_v, a_v, data)
	return filtered

def simple_filter(signal: Signal, cutoff_freq: float, type: str) -> Signal:
	# cutoff_freq - Hz

	filtered_data = simple_filter_raw(signal.data, cutoff_freq, signal.frequency, type)
	return Signal(signal.info, filtered_data)
	# TODO: pretty sure the amplitude changes after filtering,
	# 		so the new info could be incorrect

lowpass_filter_sig = ['cutoff_freq']
lowpass_default_params = m(cutoff_freq = 10*Hz)
# lowpass_filter : (Signal, cutoff_freq: float) -> float
lowpass_filter = part(simple_filter, type='low')
lowpass_tr = Trans('Lowpass filter', lowpass_filter, lowpass_filter_sig, )

highpass_filter_sig = ['cutoff_freq']
highpass_default_params = m(cutoff_freq = 0.05*Hz)
# highpass_filter : (Signal, float) -> float
highpass_filter = part(simple_filter, type='high')
highpass_tr = Trans('Highpass filter', highpass_filter, highpass_filter_sig)



######################################################################
# IMPORTANT - DON'T DELETE THESE CLASSES WITHOUT READING THE COMMENT #
######################################################################

class FiltersDict(OrderedDict): pass # SEE COMMENT BELOW
class FilterDefaultParametersDict(dict): pass # SEE COMMENT BELOW

# These two classes seem useless, BUT they serve an important purpose.
# Allow me to describe a bug that using plain OrderedDicts/dicts caused.

# module `A` did `from filters import available_filters`.
# `available_filters` is an OrderedDict, defined in the stdlib, so
# `inspect.getmodule(available_filters)` yields None.
# Hence, the reloader couldn't see that `A` depended on `filters`,
# and `filters` wasn't reloaded.
# That in turn caused `filters` to use an outdated version of the Signal class -
# the one from before the reload - so suddenly typechecks started failing
# with puzzling messages like "expected Signal, got Signal".
# I spent half a day tracking this bug down, so I thought I'd
# prevent that from happening in the future. 

# TODO: Make these classes unnecessary, i.e. figure out a way to
# 		export this data sensibly


available_filters = FiltersDict([
	('highpass', highpass_tr),
	('lowpass',  lowpass_tr),
])

default_parameters = FilterDefaultParametersDict({
	'lowpass': lowpass_default_params,
	'highpass': highpass_default_params,
})