# This module uses code created by Wiktor Rorot <wiktor.rorot@gmail.com> as a part of pytnam project
# (https://github.com/pytnam/pytnam) licensed under GNU GPL.
# The original code has been  modified.

import numpy as np # type: ignore

from typing import (
	Any,
	Tuple, Dict, Sequence,
	BinaryIO,
)

# TODO: try converting Dict[str, Any] to TypedDict
# 	http://mypy.readthedocs.io/en/latest/kinds_of_types.html#typeddict
def read_edf(path: str) -> Tuple[ Dict[str, Any], Dict[str, Sequence[float]] ] :
# def read_edf(path: str):
	"""
	Reads a .edf file.
		header: Dict[str, Any], a dictionary containing general information about the recording from the .edf file's header.
			keys:

			!!!!! OUTDATED !!!!!
				version		: str 	- version of the .edf data format (always 0)
				patient_id	: str 	- local patient id
				rec_id 		: str 	- local recording id
				startdate	: str 	- startdate of the recording (dd.mm.yy) (for more info see EDF and EDF+ specs at: http://www.edfplus.info/specs/index.html)
				starttime	: str 	- starttime of the recording (hh.mm.ss)
				header_bytes: int 	- size of the header (in bytes)
				reserved_general
							: str 	- reserved field of 44 characters; 
					since introduction of EDF+ it conveys the information about the continuity of the record (see EDF+ specs)
				num_records	: int 	- the recording in the edf format is broken into records of not less than 1 second and no more than 61440 bytes (see specs);
				record_duration
							: float - duration of one record; usually an integer >= 1;
				ns 			: int 	- number of signals in the recording (e.g. in EEG - number of channels)
				labels 		: List[str]
									- labels of signals;
				transducer 	: Dict[str, str]
							- key: label (str, an element of labels), value: transducer type;
				physical_dim
							: Dict[str, str]
							- key: label (str, an element of labels), value: physical dimension;
				physical_min Dict[str, float]
							- key: label (str, an element of labels), value: physical minimum;
				physical_max
							: Dict[str, float]
							- key: label (str, an element of labels), value: physical maximum;
				digital_min : Dict[str, float]
							- key: label (str, an element of labels), value: digital minimum;
				digital_max : Dict[str, float]
							- key: label (str, an element of labels), value: digital maximum;
				prefiltering
							: Dict[str, str]
							- key: label (str, an element of labels), value: signal's prefiltering;
				num_samples_in_record
							: Dict[str, int]
							- key: label (str, an element of labels), value: number of samples in each record of the signal;
				num_samples
							: Dict[str, int]
							- key: label (str, an element of labels), value: total number of samples in each signal;
				reserved_signal
							: Dict[str, str]
							- key: label (str, an element of labels), value: a reserved field of 32 characters;
				frequency 	: Dict[str, float]
							- key: label (str, an element of labels), value: frequency of the signal;

		:return signal	: Dict[str, np.array[float]] -- a dictionary of the following format: key: label, value: list of samples;

			NOTE: this version ignores the differences between edf and edf+, what makes her more suitable for edf,
			rather than edf+ files

			TODO: signal is represented in the digital or physical form? does it have to be transformed?
	"""
	data_file = open(path, 'rb')
	header = read_header(data_file)
	signals = read_signals(data_file, header)
	data_file.close()

	for label in header['labels']: 
		# compute sampling frequency for every channel
		header['signal_infos'][label]['frequency'] = header['signal_infos'][label]['num_samples_in_record'] / header['record_duration']

		# compute length for each channel
		header['signal_infos'][label]['num_samples'] = len(signals[label])
		
	return header, signals




def scale(physical_max: float, digital_max: float, signal: Sequence[float]):
	"""Scales the signal from digital (arbitrary) to physical (uV) units."""
	# note: this function will increase the computational complexity of Reader

	signal *= physical_max / digital_max
	return signal





def read_header(data_file: BinaryIO) -> Dict[str, Any]:
	"""Reads EDF file header."""

	def read_n_bytes(df: BinaryIO, n, method):
		return method(df.read(n).strip().decode('ascii'))

	def static_header(df: BinaryIO, hdr):
		# this part of code reads the part of the header with the general information about the record

		header_keys_static = [('version', 8, str), ('patient_id', 80, str), ('rec_id', 80, str),
							  ('startdate', 8, str),
							  ('starttime', 8, str), ('header_bytes', 8, int), ('reserved_general', 44, str),
							  ('num_records', 8, int), ('record_duration', 8, float), ('ns', 4, int)]

		for key, n, method in header_keys_static:
			hdr[key] = read_n_bytes(df, n, method)
		return hdr


	def dynamic_header(df: BinaryIO, hdr):
		# this part reads the part of the header with the information about each signal

		ns = hdr['ns']

		hdr['labels'] = []
		for i in range(ns):
			label = df.read(16).strip().decode('ascii')
			hdr['labels'].append(label)

		header_keys_dynamic = [('transducer', 80, str), ('physical_dim', 8, str), ('physical_min', 8, float),
							   ('physical_max', 8, float), ('digital_min', 8, float), ('digital_max', 8, float),
							   ('prefiltering', 80, str), ('num_samples_in_record', 8, int), ('reserved_signal', 32, str)]

		# in a 4-channel file the header would be laid out like this:
		# t1 t2 t3 t4 p1 p2 p3 p4 ...
		# where tn = transducer of the nth channel
		# 		pn = physical dim of the nth channel
		#		etc.

		hdr['signal_infos'] = {label:{} for label in hdr['labels']}

		# because of the data layout, we read all the transducers first,
		# then all the physical dims, etc

		for key, n, method in header_keys_dynamic:
			for label in hdr['labels']:
				hdr['signal_infos'][label][key] = read_n_bytes(df, n, method)

		return hdr

	header = dynamic_header(data_file, static_header(data_file, {}))
	# header = dynamic_header(data_file, static_header(data_file, defaultdict(lambda: None)))
	# header = static_header(data_file, header)
	# header = dynamic_header(data_file, header)

	return header



def read_signals(data_file: BinaryIO, hdr) -> Dict[str, Sequence[float]]:
	"""Reads EEG signals from the EDF file."""

	signals = {}
	num_records = hdr['num_records']
	rest = bytes(data_file.read())
	offset = 0
	int16 = np.dtype(np.int16) 		# type: ignore
	dt = int16.newbyteorder('<')	# type: ignore

	for label in hdr['labels']:
		num_samples_in_record = hdr['signal_infos'][label]['num_samples_in_record']
		signals[label] = np.zeros(num_records * num_samples_in_record).reshape(num_records, num_samples_in_record)

	for i in range(num_records):
		for label in hdr['labels']:
			num_samples_in_record = hdr['signal_infos'][label]['num_samples_in_record']
			signals[label][i] = np.frombuffer(rest, dtype=dt, count=num_samples_in_record, offset=offset)
			offset += num_samples_in_record * 2

	for label in hdr['labels']:
		num_samples_in_record = hdr['signal_infos'][label]['num_samples_in_record']
		signals[label] = scale(	hdr['signal_infos'][label]['physical_max'],
								hdr['signal_infos'][label]['digital_max'],
							  	np.array(signals[label].reshape(num_samples_in_record * num_records)))

	return signals

