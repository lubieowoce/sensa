import imgui as im
from imgui import Vec2

from types_util import *
from util import (
	point_offset, point_subtract_offset,
	clamp, limit_lower, limit_upper,
	Rect, is_in_rect, rect_width, rect_height,
	add_rect,
	get_mouse_position,
	range_incl
)
from time_range import *
from signal import Signal

import math
import numpy as np



# Signal:
# 	  data,
# 	  frequency, num_samples,
# 	  physical_dim,
# 	  physical_min, physical_max,
# 	  digital_min,  digital_max,
# 	  transducer, prefiltering, 
# 	  num_samples_in_record, reserved_signal,
# 	  info

def signal_plot_state(time_range: TimeRange) -> Dict[str, Any]:
	return \
		{
		    'time_range'
		    'is_dragged': False,
		    'start_t_before_drag': None,
		}

# 0.00    0.10    0.23    0.27    0.30    0.27  v
# |-------|-------|-------|-------|-------|
# 0       200     400     600     800     1000  ms 
# 0       1       2       3       4       5     i

def plot_signal(draw_list, emit, plot_state: Dict[str, Any], signal: Signal, plot_draw_area: Rect) -> IO_[None]:



	top_left, bottom_right = plot_draw_area
	width_px  = int(rect_width(plot_draw_area))
	debug_print(plot_state, 'width_px', width_px)
	height_px = int(rect_height(plot_draw_area))

	left_x = top_left.x
	right_x = bottom_right.x

	top_y = top_left.y
	bottom_y = bottom_right.y

	max_t = (len(signal.data)-1) * signal.time_between_samples

	# if a new plot channel was selected, pick a sensible default time range
	# (hacky, should actually be done on plot channel selection)
	if plot_state['time_range'] == None:
		end_t = limit_upper(width_px * signal.sampling_interval, high=max_t)
		# end_t = width_px * signal.sampling_interval
		plot_state['time_range'] = TimeRange(0.0, end_t)


	# MIDDLE LINE (AT DATA VALUE 0)
	middle_y = top_left.y + height_px/2
	mid_line_start = Vec2(left_x,  middle_y)
	mid_line_end   = Vec2(right_x, middle_y)

	white = (1.0, 1.0, 1.0, 1)
	draw_list.add_line(mid_line_start, mid_line_end, color=white)


	# BOX AROUND PLOT
	gray = (0.8, 0.8, 0.8, 1)
	add_rect(draw_list, top_left, bottom_right, gray)




	# THE SIGNAL PLOT (long)


	time_range = plot_state['time_range']
	start_t, end_t = time_range
	assert 0 <= start_t < end_t <= max_t, "time range (<{}, {}>) out of bounds (<{}, {}>)" \
										   .format(start_t, end_t, 0, max_t)
	time_between_samples = signal.sampling_interval


	# get the indexes of the signal data to plot

	first_ix = math.ceil(start_t / time_between_samples)    # first sample after start_t
	last_ix  = math.floor(end_t / time_between_samples)      # last sample before end_t
	#                                                       (so we can draw a line to it even though it's not visible yet)
	assert 0 <= first_ix < last_ix <= len(signal.data)-1, "indexes <{},{}> out of bounds of data <{},{}>" \
													       .format(first_ix, last_ix, 0, len(signal.data)-1)

	debug_print(plot_state, 'first_ix', first_ix)
	debug_print(plot_state, 'last_ix', last_ix)

	# get some plot properties

	viewed_data_dur = end_t - start_t
	debug_print(plot_state, 'viewed_data_dur', viewed_data_dur)

	n_samples_in_range  = last_ix+1 - first_ix
	debug_print(plot_state, 'n_samples_in_range', n_samples_in_range)
	n_points_in_plot = limit_upper(n_samples_in_range, high=width_px) # cap n_points_in_plot at the plot width
	debug_print(plot_state, 'n_points_in_plot', n_points_in_plot)



	# get the signal data to plot

	# if n_samples_in_range <= n_points_in_plot:
	# 	data_part = signal.data[first_ix : last_ix+1] 
	# else: # n_samples_in_range > n_points_in_plot:
	# 	# there's more samples than pixels, so we do some very crude downsampling
	# 	# ixs = n_indexes_from_range(first_ix, last_ix, n_points_in_plot)
	# 	# data_part = signal.data[ixs]
	# 	data_part = downsample(signal.data[first_ix : last_ix+1], n_points_in_plot)

	if n_samples_in_range > n_points_in_plot:
		assert n_points_in_plot == width_px
		data_part = downsample(signal.data[first_ix : last_ix+1], n_points_in_plot)
	else: # n_samples_in_range <= n_points_in_plot
		assert n_points_in_plot == n_samples_in_range
		data_part = signal.data[first_ix : last_ix+1] 


	assert n_points_in_plot == len(data_part)

	# map the data points to pixel heights

	amplitude = max(abs(signal.physical_max), abs(signal.physical_min))
	# TODO:  # PERF-IMPROVEMENT: the following could be fused into one operation
	normalized = data_part / amplitude   # now all the points are in the <-1, 1> range
	offsets = (- normalized) * height_px/2 # pixel offsets from the mid line.
	# ^ note the negation. top left coordinates mean that
	# positive datapoints need to go "up" - in the negative y of the middle.
	ys = offsets + middle_y # pixel heights of every point

	debug_print(plot_state, 'data_part_len', len(ys))

	# draw the actual plot

    # how much px per 1 sample?       
	# time_range_length(time_range)   sec  -> width px
	# 1 sample (time_between_samples) sec  ->  x px
	#
	# x = (time_between_samples / time_range_length(time_range)) * width
	px_per_1sample = (time_between_samples / time_range_length(time_range)) * width_px

	if n_samples_in_range > n_points_in_plot:
		assert n_points_in_plot == width_px
		px_per_1point = 1
	else: # n_samples_in_range <= n_points_in_plot
		assert n_points_in_plot == n_samples_in_range
		px_per_1point = px_per_1sample
		
	# assert math.isclose((len(ys)-1) * px_per_1point, width_px)
	debug_print(plot_state, 'px_per_1sample', px_per_1sample)
	debug_print(plot_state, 'length of plot', px_per_1point * (len(ys)-1))

	px_per_1second = px_per_1sample * signal.samples_per_second
	first_point_t = first_ix * time_between_samples
	first_point_offset_t = first_point_t - start_t
	first_point_x_offset = first_point_offset_t * px_per_1second
	first_point_x = left_x + first_point_x_offset


	grue = (0.2, 0.7, 0.8, 1)
	for i in range(0, len(ys)-1): # the last one doesn't have a next point to draw a line to, hence the -1
		# x1 = left_x + i*px_per_1point
		# x2 = left_x + (i+1)*px_per_1point
		x1 = first_point_x + i*px_per_1point
		x2 = first_point_x + (i+1)*px_per_1point
		point1 = Vec2(x1, ys[i])
		point2 = Vec2(x2, ys[i+1])
		draw_list.add_line(point1, point2, color=grue, thickness=2.0)


	# END OF THE SIGNAL PLOT



	# HANDLING USER INPUT

	# crude dragging state machine
	drag_origin = point_subtract_offset(get_mouse_position(), im.get_mouse_drag_delta())
	if not plot_state['dragging_plot'] \
		and im.is_mouse_dragging(button=0) \
		and is_in_rect(drag_origin, plot_draw_area):
		# just begun dragging
		plot_state['dragging_plot'] = True
		plot_state['time_range_before_drag'] = time_range
		
	if plot_state['dragging_plot'] and not im.is_mouse_dragging(button=0):
		# just ended dragging
		plot_state['dragging_plot'] = False
		plot_state['time_range_before_drag'] = None
	# end dragging state machine



	# code that might change the time range starts here

	next_time_range = time_range  # if no drag or < > button input


	# DRAGGING

	time_per_1px  = viewed_data_dur / width_px  # to know how much 1px of drag should move the time range

	if plot_state['dragging_plot']:
		next_time_range = time_range_subtract_offset(
					          plot_state['time_range_before_drag'],
					          im.get_mouse_drag_delta().x * time_per_1px )
		# ^ mouse moves left -> start_t moves right 

		# draw line at mouse position:
		mouse_x = get_mouse_position().x
		draw_list.add_line(Vec2(mouse_x, bottom_y), Vec2(mouse_x, top_y), color=white)



	# ZOOMING

	data_dur = len(signal.data) * time_between_samples

	#   buttons
	did_zoom = False
	zoom_factor = 1.5
	min_time_range_length = 2*time_between_samples # so there's always at least one point visible
	max_time_range_length = data_dur
	# ^ important: zoom in narrows the time range,
	#   zooming out widens it.

	if im.button("  -  "):
		did_zoom = True
		next_time_range = scale_by_limited(zoom_factor, time_range,
										   min_len=min_time_range_length,
										   max_len=max_time_range_length)
	im.same_line()
	if im.button("  +  "):
		did_zoom = True
		next_time_range = scale_by_limited(1/zoom_factor, time_range,
										   min_len=min_time_range_length,
										   max_len=max_time_range_length)

	if did_zoom:
		mid_x = left_x + (right_x - left_x)/2
		draw_list.add_line(Vec2(mid_x, bottom_y), Vec2(mid_x, top_y), color=white)


	# UPDATE THE TIME RANGE based on input
	next_time_range = clamp_time_range(0, next_time_range, data_dur)
	# should also set a minimum and maximum time range length here
	# to prevent crash when zooming too far/too close
	plot_state['time_range'] = next_time_range 


	# END




# # setting different mouse cursor if hovering over plot
# mouse_pos = get_mouse_position()

# im.get_io().mouse_draw_cursor = True
# if is_in_rect(mouse_pos, plot_draw_area):
# 	im.set_mouse_cursor(im.MOUSE_CURSOR_MOVE)
# 	plot_state['hovered'] = True
# else:
# 	# im.set_mouse_cursor(im.MOUSE_CURSOR_ARROW)
# 	plot_state['hovered'] = False

def debug_print(debug_dict: Dict[str, Any], key: str, val) -> IO_[None]:
	debug_dict[key] = val



def amplitude(data: NDArray[float]) -> float:
	min_v = np.min(data)
	max_v = np.max(data)
	return max(abs(min_v), abs(max_v))




def downsample(data: NDArray[float], n_samples: int) -> NDArray[float]:
	assert n_samples <= len(data), "data length ({d_len}) < target downsample amount ({n_sam}) - downsampling cannot produce more samples" \
									.format(d_len=len(data), n_sam=n_samples)
	downsampled = crude_downsample(data, n_samples)
	assert len(downsampled) == n_samples

	return downsampled



def crude_downsample(data: NDArray[float], n_samples: int) -> NDArray[float]:
	"""
	Downsample `data` by picking `n_samples` samples from `data`
	at a regular interval. Works pretty bad for noisy data.
	"""
	assert n_samples <= len(data), "data length ({d_len}) < target downsample amount ({n_sam}) - downsampling cannot produce more samples!" \
									.format(d_len=len(data), n_sam=n_samples)
	ixs = n_indexes_from_range(0, len(data)-1, n_samples)
	downsampled = data[ixs]
	return downsampled



def frange(start, end, step: float = 1) -> Iterable[float]:
	""" Like range, but supports float parameters"""
	n = start
	while n < end:
		yield n
		n += step

# 0  1  2  3  4  5  6  7  8  9  
# 0                          9
# 0           4              9 
# 0        3        6        9
# 0     2     4        7     9
# 0  1    
def n_indexes_from_range(first_ix: int, last_ix: int, n: int) -> List[int]:
	""" Returns n indexes picked from <first_ix, last_ix> at a regular interval """

	# first_ix + (n-1)*step = last_ix
	# (n-1)*step = last_ix - first_ix
	# step = (last_ix - first_ix) / (n-1)
	assert first_ix < last_ix

	step = (last_ix - first_ix) / (n-1)
	assert step > 0, "step ({}) > 0 "
	indexes = [first_ix]
	for i in range_incl(1, n-2):
		f_ix = first_ix + i*step
		ix = round(f_ix)
		limited_ix = limit_upper(ix, high=last_ix) # sanity check, should protect from floating point errors
		indexes.append(limited_ix)
	indexes.append(last_ix)
	
	assert len(indexes) == n, "len(indexes) should be {}, is {}" \
							   .format(n, len(indexes))
	assert max(indexes) == last_ix, "max ix should be {last_ix}, is {max_ix} at position {imax} (f:{first_ix}, s:{step}, l:{last_ix})" \
									 .format(last_ix=last_ix, max_ix=max(indexes), imax=indexes.index(max(indexes)),
									 	     step=step, first_ix=first_ix)
	return indexes




