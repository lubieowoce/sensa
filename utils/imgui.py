from .types import (
	IO_, IMGui,
)

import imgui as im
from imgui import Vec2


from .rect import Rect

def get_mouse_position() -> IO_[Vec2]:
	io = im.get_io()
	return io.mouse_pos

def get_window_rect() -> IMGui[Rect]:
	""" To be used only in imgui code """
	window_top_left = im.get_window_position()
	width, height = im.get_window_size()
	window_bottom_right = Vec2(window_top_left.x + width,
								  window_top_left.y + height)
	return Rect(window_top_left, window_bottom_right)


def get_window_content_rect() -> IMGui[Rect]:
	TITLE_BAR_HEIGHT = 20
	window_top_left = im.get_window_position()
	content_top_left = Vec2(window_top_left.x,  window_top_left.y + TITLE_BAR_HEIGHT)
	width, height = im.get_window_size()
	window_bottom_right = Vec2(window_top_left.x + width,
								  window_top_left.y + height)
	return Rect(content_top_left, window_bottom_right)


def get_item_rect() -> IMGui[Rect]:
	return Rect(im.get_item_rect_min(), im.get_item_rect_max())


def add_rect_coords(draw_list, top_left: Vec2, bottom_right: Vec2, color) -> IMGui[None]:
	""" Necessary because i haven't added the bindings for add_rect yet """
	top_right   = Vec2(bottom_right.x, top_left.y)
	bottom_left = Vec2(top_left.x, bottom_right.y)
	# draw rect clockwise from top left
	draw_list.add_line(top_left, top_right, color=color)
	draw_list.add_line(top_right, bottom_right, color=color)
	draw_list.add_line(bottom_right, bottom_left, color=color)
	draw_list.add_line(bottom_left, top_left, color=color)


def add_rect(draw_list, rect: Rect, color) -> IMGui[None]:
	top_left, bottom_right = rect
	add_rect_coords(draw_list, top_left, bottom_right, color)
