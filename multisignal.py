from types_util import *

from eeg_signal import Signal
import numpy as np


class MultiSignal:
	def __init__(msig, signals: Sequence[Signal]):
		msig.channels = signals

	@property
	def num_channels(msig):
		return len(msig.channels)

	def as_column_matrix(msig):
		# turns each channel into a column
		# assumes all channels have the same length and sample rate
		height = msig.num_channels
		length = msig.channels[0].num_samples
		shape = (height, length)
		return \
			np.concatenate([chan.data for chan in msig.channels]) \
			.reshape(shape) \
			.transpose()

	def __repr__(msig):
		return \
			'MultiSignal({num_chans} channels, {chans})' \
				.format(num_chans=msig.num_channels, chans=msig.channels)



