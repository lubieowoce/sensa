from types_util import *
from util import (
	point_offset, point_subtract_offset,
	clamp,
	Rect, is_in_rect, add_rect,
	get_mouse_position,
)

from signal import Signal
from imgui import Vec2
import imgui as im
import math
import numpy as np

# def plot(signal: Signal, start_ix: int, end_ix: int, top_left: Vec2, bottom_right: Vec2):
def plot_data(draw_list, emit, plot_state: Dict[str, Any], data: NDArray[float], plot_draw_area: Rect) -> IO_[None]:

	start_ix = plot_state['start_ix']

	top_left, bottom_right = plot_draw_area
	width  = bottom_right.x - top_left.x
	height = bottom_right.y - top_left.y
	assert width <= len(data) - start_ix, "not enough data points to plot 1 value / 1 pixel"
	# assert width <= len(data[start_ix:])
	n_points = int(width)

	left_x = top_left.x
	right_x = bottom_right.x


	# middle line (at data value 0)
	middle_y = top_left.y + height/2
	mid_line_start = Vec2(left_x,  middle_y)
	mid_line_end   = Vec2(right_x, middle_y)

	white = (1.0, 1.0, 1.0, 1)
	draw_list.add_line(mid_line_start, mid_line_end, color=white)



	# plot
	data_part = data[start_ix : start_ix+n_points] 
	
	# TODO:  # PERF-IMPROVEMENT: the following could be fused into one operation
	normalized = data_part / amplitude(data_part)   # now all the points are in the <-1, 1> range
	offsets = (- normalized) * height/2 # pixel offsets of every point.
	# ^ note the negation. top left coordinates mean that
	# positive datapoints need to go "up" - in the negative y of the middle.
	ys = offsets + middle_y # pixel heights of every point

	grue = (0.2, 0.7, 0.8, 1)
	for i in range(len(ys)-1): # the last one doesn't have a next point to draw a line to
		x1 = left_x + i
		x2 = left_x + i + 1
		point1 = Vec2(x1, ys[i])
		point2 = Vec2(x2, ys[i+1])
		draw_list.add_line(point1, point2, color=grue, thickness=2.0)



	# box around plot
	gray = (0.8, 0.8, 0.8, 1)
	add_rect(draw_list, top_left, bottom_right, gray)


	# # mouse cursor
	# mouse_pos = get_mouse_position()

	# im.get_io().mouse_draw_cursor = True
	# if is_in_rect(mouse_pos, plot_draw_area):
	# 	im.set_mouse_cursor(im.MOUSE_CURSOR_MOVE)
	# 	plot_state['hovered'] = True
	# else:
	# 	# im.set_mouse_cursor(im.MOUSE_CURSOR_ARROW)
	# 	plot_state['hovered'] = False

	
	# dragging
	# crude dragging state machine
	drag_origin = point_subtract_offset(get_mouse_position(), im.get_mouse_drag_delta())
	if not plot_state['dragging_plot'] \
		and im.is_mouse_dragging(button=0) \
		and is_in_rect(drag_origin, plot_draw_area):
		# just begun dragging
		plot_state['dragging_plot'] = True
		plot_state['start_ix_before_drag'] = start_ix
		
	if plot_state['dragging_plot'] and not im.is_mouse_dragging(button=0):
		# just ended dragging
		plot_state['dragging_plot'] = False
		plot_state['start_ix_before_drag'] = None


	next_start_ix = start_ix  # if no drag or < > button input

	if plot_state['dragging_plot']:
		next_start_ix = plot_state['start_ix_before_drag'] - int(im.get_mouse_drag_delta().x)
		#                                                  ^ mouse moves left -> start_ix moves right 


	# buttons
	move_amount = 5
	if im.button("  <  "):
		# next_start_ix = start_ix - move_amount
		pass
	im.same_line()
	if im.button("  >  "):
		pass
		# next_start_ix = start_ix + move_amount

	min_start_ix = 0
	max_start_ix = len(data)-n_points-1
	plot_state['start_ix'] = clamp(0, next_start_ix, max_start_ix)


def amplitude(data: NDArray[float]) -> float:
	min_v = np.min(data)
	max_v = np.max(data)
	return max(abs(min_v), abs(max_v))




# Stuff for plotting sparse data (less points than pixels of plot)
# TODO: this should just be a resampling of the data
def data_part(data: NDArray[A], start_ix: int, end_ix: int, n_points: int) -> NDArray[A]:
	assert 0 <= start_ix < end_ix <= len(data)-1
	assert n_points > 0
	points_in_part = end_ix - start_ix
	step = points_in_part / n_points
	indexes = frange(start_ix, end_ix, step)
	int_indexes = (math.floor(n) for n in indexes)
	return data[int_indexes] # numpy allows passing a list of indexes

def frange(start, end, step: float = 1) -> Iterable[float]:
	""" Like range, but supports float parameters"""
	n = start
	while n < end:
		yield n
		n += step

def selected_indexes(start_ix, end_ix, step):
	indexes = frange(start_ix, end_ix, step)
	int_indexes = (math.floor(n) for n in indexes)
	return int_indexes