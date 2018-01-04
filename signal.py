from types_util import *

class Signal:
	def __init__(self, signal_info: Dict[str, Any], data):
		# ['patient_id', 'rec_id', 'startdate', 'starttime',
		fields = \
			['transducer', 'physical_dim', 'physical_min',
			 'physical_max', 'digital_min', 'digital_max',
			 'prefiltering', 'num_samples_in_record', 'reserved_signal',
			 'frequency', 'num_samples']
		for field in fields:    
			setattr(self, field, signal_info[field])
		self.data = data
		self.info = signal_info

	def __repr__(sig):
		return 'Signal({num_samp} samples @{freq}Hz, {data})' \
				.format(num_samp=sig.num_samples, freq=sig.frequency, data=sig.data)


