import imgui as im
from imgui import Vec2

from typing import (
	Any, Tuple,
	List, Dict, 
)
from types_util import (
	PMap_, # PVector_,
	Id, SignalId,
	NDArray,
	IMGui, Actions,
)

from imgui_widget import window
from better_combo import str_combo_with_none

from debug_util import (
	debug_log, debug_log_time, #debug_log_dict,
	Range
)

from sensa_util import (
	point_offset, point_subtract_offset,
	# limit_lower,
	limit_upper,

	Rect, is_in_rect, rect_width, rect_height,
	add_rect,

	get_mouse_position, get_window_content_rect,
	range_incl,
	impossible, bad_action,
)

from eff import (
	Eff, effectful,
	ACTIONS,
	eff_operation,
)

from time_range import (
	TimeRange, clamp_time_range, time_range_length,
	scale_at_point_limited, time_range_subtract_offset, 
)

from eeg_signal import Signal

import math
import numpy as np
# from pyrsistent import (m, pmap, v, pvector,)
from uniontype import union

# Signal:
# 	  data,
# 	  frequency, num_samples,
# 	  physical_dim,
# 	  physical_min, physical_max,
# 	  digital_min,  digital_max,
# 	  transducer, prefiltering, 
# 	  num_samples_in_record, reserved_signal,
# 	  info


SignalId = str


DragState, \
	NotDragging, \
	Dragging, \
= union(
'DragState', [
	('NotDragging', [ ]),
	('Dragging', 	[('time_range_before_drag', TimeRange)]),
]
)



PlotState, \
	Empty, \
	Full, \
= union(
'PlotState', [
	('Empty', 			[('id_', Id)]),


	('Full', 			[('id_', Id),
						 ('signal_id', SignalId),
						 ('time_range', TimeRange),
						 ('drag_state', DragState)]),
]
)



def initial_signal_plot_state(id_: Id) -> PlotState:
	return PlotState.Empty(id_=id_)



PlotAction, \
	SetEmpty, \
	SelectSignal, \
	SetTimeRange, \
	StartDrag, \
	EndDrag, \
= union(
'PlotAction', [
	('SetEmpty',	 [('id_', Id)]), 

	('SelectSignal', [('id_', Id),
					  ('signal_id',  SignalId) ]), 

	('SetTimeRange', [('id_', Id),
					  ('time_range', TimeRange)]), 

	('StartDrag',	 [('id_', Id)]),

	('EndDrag', 	 [('id_', Id)]),

]
)


INITIAL_VIEW_SAMPLES_N = 800




def update_plot(plot_state: PlotState,
				signal_data: PMap_[SignalId, Signal],
				action: PlotAction) -> PlotState:

	assert plot_state.id_ == action.id_, \
		"Update function for plot\{id={this_id}\}got an action meant for plot with id={action_id}" \
		.format(this_id=plot_state.id_, action_id=action.id_)


	if   action.is_SetEmpty():
		return Empty(id_=plot_state.id_)


	elif action.is_SelectSignal():

		# compute the default time range
		new_signal_id = action.signal_id
		new_signal = signal_data[new_signal_id]
		assert new_signal != None, action

		max_t = (len(new_signal.data)-1) * new_signal.time_between_samples
		default_end_t = limit_upper(  INITIAL_VIEW_SAMPLES_N * new_signal.time_between_samples  , high=max_t)
		default_time_range = TimeRange(0.0, default_end_t)

		return Full(id_=plot_state.id_,
					signal_id=new_signal_id,
					time_range=default_time_range,
					drag_state=NotDragging())


	elif action.is_SetTimeRange():

		if plot_state.is_Empty(): 
			bad_action(msg="Cannot set time range of empty plot: " + plot_state)
			return plot_state

		if plot_state.is_Full():
			# maybe clamp the time_range here?
			return plot_state.set(time_range=action.time_range)

		


	elif action.is_StartDrag():

		if plot_state.is_Empty():
			bad_action(msg="Cannot drag an empty plot " + plot_state)
			return plot_state

		elif plot_state.is_Full():
			drag_state = plot_state .drag_state
			time_range = plot_state .time_range

			if drag_state.is_NotDragging():
				return plot_state.set(drag_state=Dragging(time_range_before_drag=time_range))
			elif drag_state.is_Dragging():
				bad_action(msg="Is already dragging: cannot start dragging in state " + plot_state)
				return plot_state

		else:
			impossible("Invalid plot state:" + plot_state)



	elif action.is_EndDrag():

		if plot_state.is_Empty():
			bad_action(msg="Cannot stop dragging an empty plot - it shouldn't be dragged in the first place. " + plot_state)
			return plot_state

		elif plot_state.is_Full():
			drag_state = plot_state .drag_state

			if drag_state.is_NotDragging():
				bad_action("Is already dragging: cannot start dragging in state " + plot_state)
				return plot_state

			elif drag_state.is_Dragging():
				return plot_state.set(drag_state=NotDragging())

		else:
			impossible("Invalid plot state:" + plot_state)



	else:
		impossible("Action is not a valid PlotAction: "+action)




white = (1.0, 1.0, 1.0, 1)

SIGNAL_PLOT_CALL_START,  SIGNAL_PLOT_CALL_END = Range("signal_plot_call")
WAVE_DRAW_START,         WAVE_DRAW_END        = Range("wave_draw")
DATA_GET_START,          DATA_GET_END         = Range("data_get")


# 0.00    0.10    0.23    0.27    0.30    0.27  v
# |-------|-------|-------|-------|-------|
# 0       200     400     600     800     1000  ms 
# 0       1       2       3       4       5     i


@effectful(ACTIONS)
def signal_plot_window(
	plot_state:  Dict[str, Any],
	signal_data:  Dict[SignalId, Signal],
	signal_names: Dict[SignalId, str],
	ui_settings: Dict[str, Any]) -> Eff(ACTIONS)[IMGui[None]]:

	emit = eff_operation('emit')

	PLOT_WINDOW_FLAGS = 0 if ui_settings['plot_window_movable'] else im.WINDOW_NO_MOVE

	# if plot_state.is_Empty():
	# 	plot_name = "No signal##{id}".format(id=plot_state.id_)
	# elif plot_state.is_Full():
	# 	plot_name = "Signal {sig_id} (drag to scroll)##{id}" \
	# 		.format(sig_id=plot_state.signal_id, id=plot_state.id_)
	# else:
	# 	impossible("Invalid plot state: "+plot_state)
	plot_name = "Plot (id={id})".format(id=plot_state.id_)

	with window(name=plot_name, flags=PLOT_WINDOW_FLAGS):
		content_top_left, content_bottom_right = get_window_content_rect()
		draw_list = im.get_window_draw_list()

		# signal selector
		if len(signal_data) > 0:
			signal_ids =  sorted(signal_data.keys())
			debug_log('signal_ids', signal_ids)

			prev_o_selected_signal_id = None if plot_state.is_Empty() else plot_state.signal_id

			changed, o_selected_signal_id = str_combo_with_none("channel", prev_o_selected_signal_id, signal_ids)
			if changed:
				if o_selected_signal_id != None:
					selected_signal_id = o_selected_signal_id
					emit( SelectSignal(id_=plot_state.id_, signal_id=selected_signal_id) )
				else:
					emit( SetEmpty(id_=plot_state.id_) )
		else:
			im.text("No signals loaded")

		# checkbox
		# changed, window_movable = im.checkbox("move", ui['plot_window_movable'])
		# if changed:
		#     ui['plot_window_movable'] = window_movable

		
		plot_draw_area = Rect(point_offset(content_top_left, im.Vec2(10, 35)),
						      point_offset(content_bottom_right, im.Vec2(-10, -10)))

		signal_plot(plot_state, signal_data, plot_draw_area, draw_list,
					ui_settings=ui_settings)

		plot_react_to_drag(plot_state, signal_data, plot_draw_area,
						   ui_settings=ui_settings)




def signal_plot(plot_state: PlotState,
				signal_data: PMap_[SignalId, Signal],
				plot_draw_area: Rect,
				draw_list, ui_settings) -> IMGui[None]:

	debug_log('plot_state', plot_state.get_variant_name())


	if plot_state.is_Empty():
		show_empty_plot(plot_state, plot_draw_area, draw_list)


	elif plot_state.is_Full():
		signal_id = plot_state.signal_id
		signal = signal_data[signal_id]

		show_full_plot(plot_state, signal, plot_draw_area, draw_list, ui_settings)

	else:
		impossible("Invalid plot state: "+plot_state)


@effectful(ACTIONS)
def plot_react_to_drag(plot_state: PlotState,
					   signal_data: PMap_[str, Signal],
					   plot_draw_area: Rect,
					   ui_settings) -> Eff(ACTIONS)[None]:
	emit = eff_operation('emit')

	if plot_state.is_Empty():
		return

	assert plot_state.is_Full()

	width_px  = int(rect_width(plot_draw_area))

	signal_id = plot_state.signal_id
	signal = signal_data[signal_id]

	time_between_samples = signal.sampling_interval
	max_t = (len(signal.data)-1) * time_between_samples	
	
	time_range = plot_state.time_range


	top_left, bottom_right = plot_draw_area
	# height_px = int(rect_height(plot_draw_area))
	left_x = top_left.x
	# right_x = bottom_right.x


	# sanity check before handling input
	# (underscores are so that these won't collide with the ones after handling inputs)
	__start_t, __end_t = time_range
	assert 0. <= __start_t < __end_t <= max_t, "time range (<{}, {}>) out of bounds (<{}, {}>)" \
										        .format(__start_t, __end_t, 0., max_t)


	# HANDLING USER INPUT (long)

	# crude dragging state machine
	drag_origin = point_subtract_offset(get_mouse_position(), im.get_mouse_drag_delta())

	if (plot_state.drag_state.is_NotDragging() 
		and im.is_mouse_dragging(button=0) 
		and is_in_rect(drag_origin, plot_draw_area)
	   ):
		# just begun dragging
		emit( StartDrag(id_=plot_state.id_) )
		
	if (plot_state.drag_state.is_Dragging() 
		and not im.is_mouse_dragging(button=0)
	   ):
		# just ended dragging
		emit( EndDrag(id_=plot_state.id_) )
		return
		# ^ Return early - imgui already thinks the drag has ended,
		# and im.get_mouse_drag_delta() will return (-1, -1), so the plot
		# will get updated badly.

	# end dragging state machine



	# code that might change the time range starts here

	updated_time_range = time_range  # if no drag or < > button input


	# DRAGGING


	if plot_state.drag_state.is_Dragging():

		time_range_before_drag = plot_state .drag_state .time_range_before_drag
		mouse_drag_delta = im.get_mouse_drag_delta()

		updated_time_range = time_range_before_drag


		# ZOOMING

		min_time_range_length = 2*time_between_samples # so there's always at least one point visible

		# zoom_factor_per_100px = 1.1
		# zoom_factor_per_1px   = 1 + ((zoom_factor_per_100px-1) / 100)

		x_delta = mouse_drag_delta.x
		y_delta = mouse_drag_delta.y

		do_zoom   = True
		do_scroll = True


		if do_zoom and y_delta != 0.:
			factor = (math.exp(-y_delta / 100))
			# 
			assert left_x <= drag_origin.x
			viewed_data_dur_before_drag = time_range_before_drag.end_t - time_range_before_drag.start_t
			time_per_1px_before_drag  = viewed_data_dur_before_drag / width_px

			origin_x_offset = drag_origin.x - left_x
			origin_t_offset = origin_x_offset * time_per_1px_before_drag
			origin_t = time_range_before_drag.start_t + origin_t_offset

			updated_time_range = scale_at_point_limited(time_range_before_drag, factor, origin_t, 
											min_len=min_time_range_length,
											min_t=0., max_t=max_t)

		# SCROLLING
		viewed_data_dur = updated_time_range.end_t - updated_time_range.start_t
		time_per_1px  = viewed_data_dur / width_px  # to know how much 1px of drag should move the time range

		if do_scroll and x_delta != 0.:
			updated_time_range = time_range_subtract_offset(
						           		updated_time_range,
						          		x_delta * time_per_1px )
			# ^ mouse moves left -> start_t moves right, so we subtract


		updated_time_range = clamp_time_range(0., updated_time_range, max_t)



	# UPDATE THE TIME RANGE based on input
	if plot_state.time_range != updated_time_range:
		emit( SetTimeRange(id_=plot_state.id_, time_range=updated_time_range)  )


	# END OF HANDLING USER INPUT





def show_full_plot(plot_state: Dict[str, Any],
				   signal: Signal,
				   plot_draw_area: Rect,
				   draw_list,
				   ui_settings) -> IMGui[None]:

	assert plot_state.is_Full()

	debug_log_time(SIGNAL_PLOT_CALL_START)

	top_left, bottom_right = plot_draw_area
	width_px  = int(rect_width(plot_draw_area))
	debug_log('width_px', width_px)
	height_px = int(rect_height(plot_draw_area))

	left_x = top_left.x
	right_x = bottom_right.x

	top_y = top_left.y
	bottom_y = bottom_right.y

	time_between_samples = signal.sampling_interval
	max_t = (len(signal.data)-1) * time_between_samples

	


	# INPUT HANDLING USED TO BE HERE

	# debug_log_dict("plot", plot_state)
	time_range = plot_state .time_range
	start_t, end_t = time_range
	assert 0. <= start_t < end_t <= max_t, "time range (<{}, {}>) out of bounds (<{}, {}>)" \
										    .format(start_t, end_t, 0., max_t)

	viewed_data_dur = end_t - start_t
	debug_log('viewed_data_dur', viewed_data_dur)



	# BOX AROUND PLOT
	gray = (0.8, 0.8, 0.8, 1)
	add_rect(draw_list, plot_draw_area, gray)



	# MIDDLE LINE (AT DATA VALUE 0)
	middle_y = top_left.y + height_px/2
	mid_line_start = Vec2(left_x,  middle_y)
	mid_line_end   = Vec2(right_x, middle_y)

	draw_list.add_line(mid_line_start, mid_line_end, color=white)






	# THE SIGNAL PLOT (long)


	# get the indexes of the signal data to plot

	first_ix = math.ceil(start_t / time_between_samples)    # first sample after start_t
	last_ix  = math.floor(end_t / time_between_samples)      # last sample before end_t
	#                                                       (so we can draw a line to it even though it's not visible yet)
	assert 0 <= first_ix < last_ix <= len(signal.data)-1, "indexes <{},{}> out of bounds of data <{},{}>" \
														   .format(first_ix, last_ix, 0, len(signal.data)-1)

	debug_log('first_ix', first_ix)
	debug_log('last_ix', last_ix)

	# get some plot properties

	n_samples_in_range  = last_ix+1 - first_ix
	debug_log('n_samples_in_range', n_samples_in_range)
	n_points_in_plot = limit_upper(n_samples_in_range, high=width_px) # cap n_points_in_plot at the plot width
	debug_log('n_points_in_plot', n_points_in_plot)



	# get the signal data to plot

	# if n_samples_in_range <= n_points_in_plot:
	# 	data_part = signal.data[first_ix : last_ix+1] 
	# else: # n_samples_in_range > n_points_in_plot:
	# 	# there's more samples than pixels, so we do some very crude downsampling
	# 	# ixs = n_indexes_from_range(first_ix, last_ix, n_points_in_plot)
	# 	# data_part = signal.data[ixs]
	# 	data_part = downsample(signal.data[first_ix : last_ix+1], n_points_in_plot)
	debug_log_time(DATA_GET_START)

	if n_samples_in_range > n_points_in_plot:
		assert n_points_in_plot == width_px
		if ui_settings['numpy_resample']:
			point_times = np.linspace(start=0., stop=(len(signal.data)-1)*time_between_samples, num=len(signal.data)) 
			sampled_times = np.linspace(start=start_t, stop=end_t, num=n_points_in_plot)
			data_part = np.interp(x=sampled_times, xp=point_times, fp=signal.data)
		else:
			data_part = downsample(signal.data[first_ix : last_ix+1], n_points_in_plot)
	else: # n_samples_in_range <= n_points_in_plot
		assert n_points_in_plot == n_samples_in_range
		data_part = signal.data[first_ix : last_ix+1] 

	assert n_points_in_plot == len(data_part)

	# map the data points to pixel heights

	amplitude = max(abs(signal.physical_max), abs(signal.physical_min))
	# TODO:  # PERF-IMPROVEMENT: the following could be fused into one operation
	# NOTE: these are numpy's array operations, so `xs + 1` actually means `[x+1 for x in xs]`
	normalized = data_part / amplitude   # now all the points are in the <-1, 1> range
	offsets = (- normalized) * height_px/2 # pixel offsets from the mid line.
	# ^ note the negation. top left coordinates mean that
	# positive datapoints need to go "up" - in the negative y of the middle.
	ys = offsets + middle_y # pixel heights of every point

	debug_log_time(DATA_GET_END)
	debug_log('data_part_len', len(ys))

	# draw the actual plot

	# how much px per 1 sample?       
	# time_range_length(time_range)   sec  -> width px
	# 1 sample (time_between_samples) sec  ->  x px
	#
	# x = (time_between_samples / time_range_length(time_range)) * width
	#     ( the fraction of the time_range that 1 sample takes ) * width         
	px_per_1sample = (time_between_samples / time_range_length(time_range)) * width_px

	if n_samples_in_range > n_points_in_plot:
		assert n_points_in_plot == width_px
		assert len(ys) == width_px
		# We have exactly width_px samples in ys, because we downsampled them earlier
		px_per_1point = 1
	else: # n_samples_in_range <= n_points_in_plot
		assert n_points_in_plot == n_samples_in_range
		px_per_1point = px_per_1sample
		
	# assert math.isclose((len(ys)-1) * px_per_1point, width_px)
	debug_log('px_per_1sample', px_per_1sample)
	debug_log('length of plot', px_per_1point * (len(ys)-1))

	px_per_1second = px_per_1sample * signal.samples_per_second
	first_point_t = first_ix * time_between_samples
	first_point_offset_t = first_point_t - start_t
	first_point_x_offset = first_point_offset_t * px_per_1second
	first_point_x = left_x + first_point_x_offset


	grue = (0.2, 0.7, 0.8, 1)
	debug_log_time(WAVE_DRAW_START)
	for i in range(0, len(ys)-1): # the last one doesn't have a next point to draw a line to, hence the -1
		# x1 = left_x + i*px_per_1point
		# x2 = left_x + (i+1)*px_per_1point
		x1 = first_point_x + i*px_per_1point
		x2 = first_point_x + (i+1)*px_per_1point
		point1 = Vec2(x1, ys[i])
		point2 = Vec2(x2, ys[i+1])
		draw_list.add_line(point1, point2, color=grue, thickness=2.0)

	debug_log_time(WAVE_DRAW_END)

	# END OF THE SIGNAL PLOT

	# draw a line at drag location
	if plot_state .drag_state .is_Dragging():
		mouse_x, _ = get_mouse_position()
		draw_list.add_line(Vec2(mouse_x, bottom_y), Vec2(mouse_x, top_y), color=white)





	debug_log_time(SIGNAL_PLOT_CALL_END)



	# END


def show_empty_plot(plot_state: Dict[str, Any], plot_draw_area: Rect, draw_list) -> IMGui[None]:
	assert plot_state.is_Empty()
	# BOX AROUND PLOT
	gray = (0.8, 0.8, 0.8, 1)
	add_rect(draw_list, plot_draw_area, gray)
	im.text("Nothing here? Load a file and select a channel.")






# ================================================






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






def time_range_to_ix_range_incl(time_range: TimeRange, signal: Signal) -> Tuple[int, int]:
	assert signal.sampling_interval >= 0, "sampling_interval ({}) must be >= 0.0" \
										   .format(signal.sampling_interval)

	time_between_samples = signal.sampling_interval
	start_t, end_t = time_range
	first_f_ix, last_f_ix = start_t / time_between_samples, end_t / time_between_samples
	first_ix = math.ceil(first_f_ix)
	last_ix  = math.floor(last_f_ix)
	# last_data_ix = len(signal.data) - 1
	# max_t = last_ix * time_between_samples

	# TODO: consider floating point inaccuracies.
	#       I'm guessing that currently it might not be possible 
	#       to hit 0, last_data_ix with a time inside the signal's range
	#       because the inaccurate f_ixs get rounded.
	#       (rounding them like this is desirable for non-edge points because 
	#        it guarantees that the ix will be inside the time range)

	return (first_ix, last_ix)




# some unused code stashed for maybe-later:


# # setting different mouse cursor if hovering over plot
# mouse_pos = get_mouse_position()

# im.get_io().mouse_draw_cursor = True
# if is_in_rect(mouse_pos, plot_draw_area):
# 	im.set_mouse_cursor(im.MOUSE_CURSOR_MOVE)
# 	plot_state['hovered'] = True
# else:
# 	# im.set_mouse_cursor(im.MOUSE_CURSOR_ARROW)
# 	plot_state['hovered'] = False



# ZOOMING BUTTONS


#   buttons

# ^ important: zoom in narrows the time range,
#   zooming out widens it.

# if im.button("  -  "):
# 	did_zoom = True
# 	updated_time_range = scale_by_limited(zoom_factor, time_range,
# 									   min_len=min_time_range_length,
# 									   max_len=max_time_range_length)
# im.same_line()
# if im.button("  +  "):
# 	did_zoom = True
# 	updated_time_range = scale_by_limited(1/zoom_factor, time_range,
# 									   min_len=min_time_range_length,
# 									   max_len=max_time_range_length)

# if did_zoom_____:
# 	mid_x = left_x + (right_x - left_x)/2
# 	draw_list.add_line(Vec2(mid_x, bottom_y), Vec2(mid_x, top_y), color=white)ot_state['hovered'] = True
# else:
# 	# im.set_mouse_cursor(im.MOUSE_CURSOR_ARROW)
# 	plot_state['hovered'] = False



# ZOOMING BUTTONS


#   buttons

# ^ important: zoom in narrows the time range,
#   zooming out widens it.

# if im.button("  -  "):
# 	did_zoom = True
# 	updated_time_range = scale_by_limited(zoom_factor, time_range,
# 									   min_len=min_time_range_length,
# 									   max_len=max_time_range_length)
# im.same_line()
# if im.button("  +  "):
# 	did_zoom = True
# 	updated_time_range = scale_by_limited(1/zoom_factor, time_range,
# 									   min_len=min_time_range_length,
# 									   max_len=max_time_range_length)

# if did_zoom_____:
# 	mid_x = left_x + (right_x - left_x)/2
# 	draw_list.add_line(Vec2(mid_x, bottom_y), Vec2(mid_x, top_y), color=white)