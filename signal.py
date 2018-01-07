from types_util import *

class Signal:
	"""
	Signal:
		data,
		frequency, num_samples,
		physical_dim,
		physical_min, physical_max,
		digital_min,  digital_max,
		transducer, prefiltering, 
		num_samples_in_record, reserved_signal,
		info
	"""
	def __init__(sig, signal_info: Dict[str, Any], data):
		# ['patient_id', 'rec_id', 'startdate', 'starttime',
		fields = \
			['frequency', 'num_samples',
			 'physical_dim', 'physical_min', 'physical_max',
			 'digital_min', 'digital_max',
			 'transducer', 'prefiltering', 
			 'num_samples_in_record', 'reserved_signal']
		for field in fields:    
			setattr(sig, field, signal_info[field])
		sig.data = data
		sig.info = signal_info

	@property
	def samples_per_second(sig):
		""" alias for frequency """
		return sig.frequency

	@property
	def sampling_interval(sig):
		return 1/sig.frequency

	@property
	def time_between_samples(sig):
		""" alias for sampling_interval """
		return sig.sampling_interval


	def __repr__(sig):
		return 'Signal({num_samp} samples @{freq}Hz, p:<{pmin}, {pmax}> | d:<{dmin}, {dmax}>)' \
				.format(num_samp=sig.num_samples, freq=sig.frequency,
						pmin=sig.physical_min, pmax=sig.physical_max,
						dmin=sig.digital_min,  dmax=sig.digital_max  )


