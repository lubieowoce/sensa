import imgui as im
from imgui import Vec2

import typing
from typing import (
	Any, Tuple,
	List, Dict, Union,
)
from utils.types import (
	PMap_, # PVector_,
	Id, SignalId,
	NDArray,
	Fun, IMGui, Actions,
)

from components.grouped import window, child
from components.draggable import draggable

from debug_util import (
	debug_log, debug_log_time, #debug_log_dict,
	Range
)

from utils import (
	point_offset, point_subtract_offset,
	# limit_lower,
	limit_upper,

	Rect, is_in_rect, rect_width, rect_height,
	add_rect,

	get_mouse_position,
	get_window_rect, get_window_content_rect,
	range_incl,
	impossible, bad_action, identity,
	Maybe, Nothing, Just,
)

from eff import (
	Eff, effectful,
	ID, ACTIONS,
	eff_operation,
)

from time_range import (
	TimeRange, clamp_time_range, time_range_length,
	scale_at_point_limited, time_range_subtract_offset, 
)


import node_graph as ng


from eeg_signal import Signal

import math
import numpy as np
import scipy.ndimage
# from pyrsistent import (m, pmap, v, pvector,)
from sumtype import sumtype

# Signal:
# 	  data,
# 	  frequency, num_samples,
# 	  physical_dim,
# 	  physical_min, physical_max,
# 	  digital_min,  digital_max,
# 	  transducer, prefiltering, 
# 	  num_samples_in_record, reserved_signal,
# 	  info





class DragState(sumtype):
	def NotDragging(): ...
	def Dragging(time_range_before_drag: TimeRange): ...

class DragAction(sumtype):
	def StartDrag(id_: Id): ...
	def EndDrag  (id_: Id): ...

# --------------

class PlotState(sumtype):
	def NoTimeRange(): ...
	def WithTimeRange(time_range: TimeRange): ...


class PlotAction(sumtype):
	def SetTimeRange  (id_: Id, time_range: TimeRange): ...
	def SetNoTimeRange(id_: Id): ... 





# --------------
PlotBoxState = typing.NamedTuple(
'PlotBoxState', [
	('id_', Id),
	('plot_state', PlotState),
	('drag_state', DragState),
]
)


def eval_node(plot_box_state: PlotBoxState) -> Fun[ [List[Signal]], Maybe[List[Signal]] ] :
	# a Sink might do some preprocessing here,
	# like computing some stuff for a FFT plot
	# (then the function signature would have to be more general)
	return (Just
			if plot_box_state.plot_state.is_WithTimeRange()
			else lambda _: Nothing())

def to_node(plot_box_state: PlotBoxState) -> ng.Node:
	return ng.Node(n_inputs=1, n_outputs=0)

PlotBoxState.eval_node = eval_node
PlotBoxState.to_node   = to_node




INITIAL_VIEW_SAMPLES_N = 800
DEFAULT_TIME_RANGE = TimeRange(0.0, INITIAL_VIEW_SAMPLES_N/200.0)

PLOT_BOX_ACTION_TYPES = (PlotAction, DragAction)
PlotBoxAction = Union[PLOT_BOX_ACTION_TYPES]

@effectful(ID, ACTIONS)
def initial_plot_box_state() -> Eff(ID, ACTIONS)[PlotBoxState]:
	get_id = eff_operation('get_id')
	emit = eff_operation('emit')

	id_ = get_id()
	state = PlotBoxState(
				id_=id_,
				# plot_state=PlotState.NoTimeRange(),
				plot_state=PlotState.WithTimeRange(DEFAULT_TIME_RANGE), # TODO: not great...
				drag_state=DragState.NotDragging()
			)
	emit(ng.GraphAction.AddNode(id_=id_, node=to_node(state)))
	return state










@effectful(ACTIONS)
def update_plot_box(plot_box_state: PlotBoxState, action: PlotBoxAction) -> PlotBoxState:

	assert plot_box_state.id_ == action.id_
	# emit = eff_operation('emit')

	old_state = plot_box_state
	new_state = None


	if type(action) == PlotAction:
		if action.is_SetTimeRange():
			new_state = plot_box_state._replace(plot_state=PlotState.WithTimeRange(time_range=action.time_range))
		elif action.is_SetNoTimeRange():
			new_state = plot_box_state._replace(plot_state=PlotState.NoTimeRange())
		

	elif type(action) == DragAction:

		if action.is_StartDrag():

			if plot_box_state.plot_state.is_NoTimeRange():
				bad_action(msg="Cannot drag an empty plot " + plot_box_state)
				new_state = plot_box_state

			elif plot_box_state.plot_state.is_WithTimeRange():
				drag_state = plot_box_state .drag_state
				time_range = plot_box_state .plot_state .time_range

				if drag_state.is_NotDragging():
					new_state = plot_box_state._replace(drag_state=DragState.Dragging(time_range_before_drag=time_range))
				elif drag_state.is_Dragging():
					bad_action(msg="Is already dragging: cannot start dragging in state " + plot_box_state)

			else:
				plot_box_state.impossible()



		elif action.is_EndDrag():

			if plot_box_state.plot_state.is_NoTimeRange():
				bad_action(msg="Cannot stop dragging an empty plot - it shouldn't be dragged in the first place. " + plot_box_state)

			elif plot_box_state.plot_state.is_WithTimeRange():
				drag_state = plot_box_state .drag_state

				if drag_state.is_NotDragging():
					bad_action("Is already dragging: cannot start dragging in state " + plot_box_state)

				elif drag_state.is_Dragging():
					return plot_box_state._replace(drag_state=DragState.NotDragging())

			else:
				plot_box_state.impossible()



	else:
		action.impossible()

	return    new_state if new_state != None  else old_state





white = (1.0, 1.0, 1.0, 1)

# profiling markers
SIGNAL_PLOT_CALL_START,  SIGNAL_PLOT_CALL_END = Range("signal_plot_call")
WAVE_DRAW_START,         WAVE_DRAW_END        = Range("wave_draw")
DATA_GET_START,          DATA_GET_END         = Range("data_get")


# 0.00    0.10    0.23    0.27    0.30    0.27  v
# |-------|-------|-------|-------|-------|
# 0       200     400     600     800     1000  ms 
# 0       1       2       3       4       5     i


@effectful(ACTIONS)
def signal_plot_window(
	plot_box_state:  PlotBoxState,
	m_inputs: List[Maybe[Signal]],
	ui_settings: Dict[str, Any]) -> Eff(ACTIONS)[IMGui[None]]:

	# emit = eff_operation('emit')
	m_signal = m_inputs[0 ]
	assert ((type(m_signal.val) == Signal) if m_signal.is_Just() else True), repr(m_signal)


	PLOT_WINDOW_FLAGS = 0 if ui_settings['plot_window_movable'] else im.WINDOW_NO_MOVE
	plot_name = "Plot (id={id})###{id}".format(id=plot_box_state.id_)

	with window(name=plot_name, flags=PLOT_WINDOW_FLAGS):
		plot_width = -1. # auto
		plot_height = im.get_content_region_available().y - 20


		signal_plot(plot_box_state, m_signal,
					width=plot_width, height=plot_height,
					ui_settings=ui_settings)


		if m_signal.is_Nothing():
			im.text(" ")
		elif m_signal.is_Just():
			signal = m_signal.val
			im.text_colored(str(signal), 0.8, 0.8, 0.8)

		return get_window_rect()



@effectful(ACTIONS)
def signal_plot(plot_box_state: PlotState,
				m_signal: Maybe[Signal],
				width: float,
				height: float,
				ui_settings) -> IMGui[None]:

	# TODO: try using IMGui::PlotLines?
	
	# m_signal = box_inputs[plot_box_state.id_][0]
	assert ((type(m_signal.val) == Signal) if m_signal.is_Just() else True), repr(m_signal)
	emit = eff_operation('emit')
	drag_state = plot_box_state .drag_state

	im.push_style_color(im.COLOR_CHILD_WINDOW_BACKGROUND, 1., 1., 1., 0.05)
	with draggable(name="signal_plot##"+str(plot_box_state.id_),
					was_down=drag_state.is_Dragging(),
					width=width, height=height) as (status, is_down):

		if status == 'pressed': # and plot_box_state.plot_state.is_WithTimeRange():
			emit( DragAction.StartDrag(id_=plot_box_state.id_) )
		elif status == 'released': # and plot_box_state.plot_state.is_WithTimeRange():
			emit( DragAction.EndDrag(id_=plot_box_state.id_) )
		# im.text("{!r:<10}   {!r:<5}".format(status, is_held))


		if m_signal.is_Nothing() or plot_box_state.plot_state.is_NoTimeRange():
			im.text("Not ready")

		elif m_signal.is_Just():
			signal = m_signal.val
			plot_draw_area = get_window_rect()
			if ui_settings['plot_draw_function'] == 'manual':
				draw_list = im.get_window_draw_list()
				show_full_plot(plot_box_state, signal, plot_draw_area, draw_list, ui_settings)
			else:
				show_imgui_plot(plot_box_state, signal, width=-1, height=-1, ui_settings=ui_settings)

			if status == 'held':
				# Unfortunately, a DragAction.[StartDrag/EndDrag] will only be processed after draw()
				# So without this if, the drag code is called once before, and once after a drag ends,
				# without being reflected in the drag_state.
				# In the latter case, If the mouse isn't dragging, drag_delta == (0,0)
				# So effectively, the state is set as if the mouse never moved.
				assert plot_box_state .drag_state .is_Dragging()

				drag_delta = im.get_mouse_drag_delta(button=0, lock_threshold=1.)
				drag_origin = point_subtract_offset(get_mouse_position(), drag_delta)
				
				updated_time_range = time_range_after_drag(
										plot_box_state .drag_state .time_range_before_drag,
										signal,
										plot_draw_area, drag_origin, drag_delta
									 )
				if plot_box_state .plot_state .time_range != updated_time_range:
					emit( PlotAction.SetTimeRange(id_=plot_box_state.id_, time_range=updated_time_range)  )

	im.pop_style_color()




# TODO: Switch it to a pure function that just
# computes the new time range based on mouse position
def time_range_after_drag(
		time_range_before_drag: TimeRange,
		signal: Signal,
		plot_draw_area: Rect,
		drag_origin,
		drag_delta,
		) -> TimeRange:

	
	if drag_delta == (0., 0.):
		return time_range_before_drag


	time_between_samples = signal.sampling_interval
	max_t = (len(signal.data)-1) * time_between_samples	
	
	width_px  = int(rect_width(plot_draw_area))
	# height_px = int(rect_height(plot_draw_area))
	left_x = plot_draw_area.top_left.x
	# right_x = plot_draw_area.bottom_right.x


	# # sanity check before handling input
	# # (underscores are so that these won't collide with the ones after handling inputs)
	# __start_t, __end_t = time_range
	# assert 0. <= __start_t < __end_t <= max_t, "time range (<{}, {}>) out of bounds (<{}, {}>)" \
	# 									        .format(__start_t, __end_t, 0., max_t)


	updated_time_range = time_range_before_drag


	# ZOOMING
	min_time_range_length = 2*time_between_samples # so there's always at least one point visible

	# zoom_factor_per_100px = 1.1
	# zoom_factor_per_1px   = 1 + ((zoom_factor_per_100px-1) / 100)

	x_delta = drag_delta.x
	y_delta = drag_delta.y

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

	return updated_time_range


	# END OF HANDLING USER INPUT





def show_full_plot(plot_box_state: PlotState,
				   signal: Signal,
				   plot_draw_area: Rect,
				   draw_list,
				   ui_settings) -> IMGui[None]:

	# assert plot_state.is_Full()
	assert type(signal) == Signal, signal

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

	

	# debug_log_dict("plot", plot_state)
	time_range = plot_box_state .plot_state .time_range
	start_t, end_t = time_range
	assert 0. <= start_t < end_t <= max_t, "time range (<{}, {}>) out of bounds (<{}, {}>)" \
										    .format(start_t, end_t, 0., max_t)

	viewed_data_dur = end_t - start_t
	debug_log('viewed_data_dur', viewed_data_dur)




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



	debug_log_time(DATA_GET_START)

	data_part = slice_signal(
					signal, time_range,
					n_points_needed=n_points_in_plot,
					variant=ui_settings['plot_resample_function']
				)


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

	transparent = (0., 0., 0., 0.01)
	grue = (0.2, 0.7, 0.8, 1)
	# made local for perf - shaves off 0.5 ms
	add_line = draw_list.add_line


	debug_log_time(WAVE_DRAW_START)

	# Reuse the same point object every iteration
	# to avoid allocations
	# (We're basically using these as mutable tuples)
	point1 = [0., 0.]
	point2 = [0., 0.]
	# add up to about ~1.5 ms 

	# surprisingly, faster than a while loop
	for i in range(0, len(ys)-1): # the last one doesn't have a next point to draw a line to, hence the -1
		x1 = first_point_x + i*px_per_1point
		x2 = first_point_x + (i+1)*px_per_1point

		y1 = ys[i]
		y2 = ys[i+1]

		# point1 = Vec2_(x1, y1)
		# point2 = Vec2_(x2, y2)
		# # creating these every time adds up to ~5ms
		# # and imgui makes a copy anyway;
		# # exposing something that took a cimgui.ImVec2
		# # and reusing the same one every time 
		# # would speed it up considerably

		point1[0] = x1; point1[1] = y1
		point2[0] = x2; point2[1] = y2

		add_line(point1, point2, color=grue, thickness=2.0)
		# calls to `add_line` add up to ~3ms




	debug_log_time(WAVE_DRAW_END)

	# END OF THE SIGNAL PLOT

	# draw a line at drag location
	if plot_box_state .drag_state .is_Dragging():
		mouse_x, _ = get_mouse_position()
		draw_list.add_line(Vec2(mouse_x, bottom_y), Vec2(mouse_x, top_y), color=white)





	debug_log_time(SIGNAL_PLOT_CALL_END)
	# END


def show_empty_plot(plot_state: PlotState, text: str, plot_draw_area: Rect, draw_list) -> IMGui[None]:
	# assert plot_state.is_Empty()
	# BOX AROUND PLOT
	gray = (0.8, 0.8, 0.8, 1)
	add_rect(draw_list, plot_draw_area, gray)
	im.text(text)



def show_imgui_plot(
	plot_box_state: PlotState,
	signal: Signal,
	width: int = -1,
	height: int = -1,
	ui_settings = {},
	) -> IMGui[None]:

	debug_log_time(SIGNAL_PLOT_CALL_START)
	
	time_range = plot_box_state .plot_state .time_range

	if width  == -1:
		width  = int(im.get_content_region_available().x)
	if height == -1:
		height = int(im.get_content_region_available().y)

	debug_log_time(DATA_GET_START)
	data_part = slice_signal(
					signal,
					time_range,
					n_points_needed=width,
					variant=ui_settings['plot_resample_function']
				).astype(np.dtype('float32'))
	debug_log_time(DATA_GET_END)

	debug_log_time(WAVE_DRAW_START)
	im.plot_lines(
		"the_actual_plot##{}".format(plot_box_state.id_),
		values=data_part,
		graph_size=(width,height),
		scale_min=signal.physical_min,
		scale_max=signal.physical_max,
	)
	debug_log_time(WAVE_DRAW_END)


	debug_log_time(SIGNAL_PLOT_CALL_END)



def slice_signal(signal: Signal, time_range: TimeRange, n_points_needed: int, variant='numpy_resample') -> NDArray[float]:
	time_between_samples = signal.sampling_interval
	start_t, end_t = time_range

	# get the indexes of the signal data to plot

	first_ix = math.ceil(start_t / time_between_samples)    # first sample after start_t
	last_ix  = math.floor(end_t / time_between_samples)      # last sample before end_t
	#                                                       (so we can draw a line to it even though it's not visible yet)
	assert 0 <= first_ix < last_ix <= len(signal.data)-1, "indexes <{},{}> out of bounds of data <{},{}>" \
														   .format(first_ix, last_ix, 0, len(signal.data)-1)
	n_samples_in_range  = last_ix+1 - first_ix

	data_part = None
	if n_samples_in_range > n_points_needed:
		if variant == 'numpy_interp':
			point_times = np.linspace(start=0., stop=(len(signal.data)-1)*time_between_samples, num=len(signal.data)) 
			sampled_times = np.linspace(start=start_t, stop=end_t, num=n_points_needed)
			data_part = np.interp(x=sampled_times, xp=point_times, fp=signal.data)

		elif variant == 'scipy_zoom':
			# apparently slower than np.interp for large inputs
			data_part = scipy.ndimage.interpolation.zoom(
							signal.data[first_ix: last_ix+1],
							zoom=(n_points_needed/n_samples_in_range),
							# order=5,
							prefilter=True,
						)[:n_points_needed]
		else:
			data_part = downsample(signal.data[first_ix : last_ix+1], n_points_needed)

	else: # n_samples_in_range <= n_points_needed
		assert n_samples_in_range <= n_points_needed
		data_part = signal.data[first_ix : last_ix+1]

	assert len(data_part) <= n_points_needed, "need at most {} points, got {}".format(n_points_needed, len(data_part))
	return data_part




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