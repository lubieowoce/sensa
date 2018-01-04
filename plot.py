from types_util import *
from util import point_offset

from signal import Signal
from imgui import Vec2
import imgui as im
import math
import numpy as np

# def plot(signal: Signal, start_ix: int, end_ix: int, top_left: Vec2, bottom_right: Vec2):
def plot_data(draw_list, data: NDArray[float], top_left: Vec2, bottom_right: Vec2):
	width  = bottom_right.x - top_left.x
	height = bottom_right.y - top_left.y
	assert width <= len(data) 

	gray = (0.1, 0.1, 0.1, 1)
	add_rect(draw_list, top_left, bottom_right, gray)

	left_x = top_left.x
	right_x = bottom_right.x
	middle_y = top_left.y + height/2

	middle_start = Vec2(left_x,  middle_y)
	middle_end   = Vec2(right_x, middle_y)

	white = (1.0, 1.0, 1.0, 1)
	draw_list.add_line(middle_start, middle_end, color=white)

	data_part = data[0:int(width)] 
	min_v = np.min(data_part)
	max_v = np.max(data_part)
	amplitude = max(abs(min_v), abs(max_v))

	normalized = data_part / amplitude   # now all the points are in the <-1, 1> range
	offsets = normalized * height/2 # pixel offsets of every point
	ys = offsets + middle_y # pixel heights of every point

	grue = (0.2, 0.8, 1, 1)
	for i in range(len(ys)):
		x = left_x + i
		point = Vec2(x, ys[i])
		mid = Vec2(x,  middle_y)
		draw_list.add_line(mid, point, color=grue)

	

def add_rect(draw_list, top_left: Vec2, bottom_right: Vec2, color):
	""" Necessary because i haven't added the bindings for add_rect yet """
	top_right   = Vec2(bottom_right.x, top_left.y)
	bottom_left = Vec2(top_left.x, bottom_right.y)
	# draw rect clockwise from top left
	draw_list.add_line(top_left, top_right, color=color)
	draw_list.add_line(top_right, bottom_right, color=color)
	draw_list.add_line(bottom_right, bottom_left, color=color)
	draw_list.add_line(bottom_left, top_left, color=color)



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