from types_util import *
from collections import namedtuple

TimeRange = namedtuple("TimeRange", ["start_t", "end_t"])




def clamp_time_range(min_t: float, time_range: TimeRange, max_t: float) -> TimeRange:
	"""Keeps the TimeRange within <min_t, max_t> while preserving its length."""
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	range_length = end_t - start_t
	bounds_length = max_t - min_t
	assert range_length <= bounds_length, "Clamp bounds (|<{}{}>|={}) too small for time range (|<{}{}>|={})" \
										   .format(min_t, max_t, bounds_length,             start_t, end_t, range_length)

	if start_t < min_t:
		return TimeRange(min_t, min_t + range_length)
	elif max_t < end_t:
		return TimeRange(max_t - range_length, max_t)
	else: # range within clamp bounds
		return time_range





def scale_by_limited(scaling_factor: float, time_range: TimeRange, min_len: float, max_len: float) -> TimeRange:
	assert min_len < max_len, "min_len ({}) must be smaller than max_len ({})" \
							   .format(min_len, max_len)
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	scaled_tr = scale_by(scaling_factor, time_range)

	return  scaled_tr if is_time_range_length_between(min_len, max_len, scaled_tr) else time_range
	



def scale_by(scaling_factor: float, time_range: TimeRange) -> TimeRange:
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	mid_t = time_range_middle(time_range)
	start_t_scaled = mid_t + (start_t - mid_t)*scaling_factor
	end_t_scaled =   mid_t + (end_t   - mid_t)*scaling_factor

	return TimeRange(start_t_scaled, end_t_scaled)




def is_time_range_length_between(min_len: float, max_len: float, time_range: TimeRange) -> bool:
	assert min_len < max_len, "min_len ({}) must be smaller than max_len ({})" \
							   .format(min_len, max_len)
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	tr_len = end_t - start_t

	return min_len <= tr_len <= max_len



def time_range_middle(time_range: TimeRange) -> float:
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	mid_t = start_t + (end_t - start_t)/2
	return mid_t



def time_range_add_offset(time_range: TimeRange, offset: float) -> TimeRange:
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	return TimeRange(start_t+offset, end_t+offset)



def time_range_subtract_offset(time_range: TimeRange, offset: float) -> TimeRange:
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	return TimeRange(start_t-offset, end_t-offset)


def time_range_length(time_range: TimeRange) -> float:
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	return end_t - start_t
