from collections import namedtuple
from sensa_util import (limit_lower)
TimeRange = namedtuple("TimeRange", ["start_t", "end_t"])




def clamp_time_range(min_t: float, time_range: TimeRange, max_t: float) -> TimeRange:
	"""Keeps the TimeRange within <min_t, max_t> while preserving its length."""
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)

	range_length = end_t - start_t
	bounds_length = max_t - min_t

	# assert range_length <= bounds_length, "Clamp bounds (|<{}{}>|={}) too small for time range (|<{}, {}>|={})" \
	# 									   .format(min_t, max_t, bounds_length,             start_t, end_t, range_length)
	if range_length > bounds_length:
		return TimeRange(min_t, max_t)

	if start_t < min_t:
		return TimeRange(min_t, min_t + range_length)
	elif max_t < end_t:
		return TimeRange(max_t - range_length, max_t)
	else: # range within clamp bounds
		return time_range


# def scale_at_point_limited(scaling_factor: float, point: float, time_range: TimeRange, min_len: float, max_len: float) -> TimeRange:
def scale_at_point_limited(time_range: TimeRange,
						   scaling_factor: float, point: float,
						   min_len: float, min_t: float, max_t: float) -> TimeRange:
	max_len = max_t - min_t
	assert 0 < min_len <= max_len, "min_len ({}) must be smaller than max_len ({})" \
							       .format(min_len, max_len)
	start_t, end_t = time_range
	assert start_t < end_t, "Invalid time range: start_t ({}) > end_t ({})".format(start_t, end_t)
	assert start_t < point < end_t, "Point ({}) must be in time range (<{}, {}>)".format(point, start_t, end_t)
	assert scaling_factor > 0, "Bad scaling factor ({})".format(scaling_factor)

	if scaling_factor == 1:
		return time_range

	tr_len = end_t - start_t
	# scaling_factor * tr_len >= min_len
	# scaling_factor >= min_len / tr_len
	# min_scaling_factor = min_len / tr_len
	min_scaling_factor = min_len / tr_len
	scaling_factor = limit_lower(scaling_factor, low=min_scaling_factor)
	assert scaling_factor * tr_len >= min_len

	d_point_to_start = point - start_t
	d_point_to_end   = end_t - point 

	d_point_to_new_start = d_point_to_start * scaling_factor
	d_point_to_new_end   = d_point_to_end   * scaling_factor

	new_start_t = point - d_point_to_new_start
	new_end_t   = point + d_point_to_new_end

	if scaling_factor > 1: # zooming out
		assert new_start_t <= start_t < end_t <= new_end_t, "zoom out failed: nst={} st={} et={} net={}, sf={}" \
														     .format(new_start_t, start_t, end_t, new_end_t, scaling_factor)
	elif scaling_factor < 1: # zooming in
		assert start_t <= new_start_t < new_end_t <= end_t, "zoom in failed:  st={} nst={} net={} et={}, sf={}" \
														     .format(start_t, new_start_t, new_end_t, end_t, scaling_factor)
	# ^ these assertions should theoretically be
	#         `start_t < new_start_t < new_end_t < end_t` (strictly less than)
	# but floating point sometimes gives you a scaling factor != 1.0
	# that ends up behaving like 1.0, thus not scaling anything even though
	# it should. So we allow the range to stay the same

	scaled_tr = TimeRange(new_start_t, new_end_t)
	return clamp_time_range(min_t, scaled_tr, max_t)



	



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
