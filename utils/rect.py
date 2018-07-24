from collections import namedtuple
from imgui import Vec2


Rect = namedtuple("Rect", ['top_left', 'bottom_right'])

def rect_width(rect: Rect) -> float:
	top_left, bottom_right = rect
	return bottom_right.x - top_left.x

def rect_height(rect: Rect) -> float:
	top_left, bottom_right = rect
	return bottom_right.y - top_left.y

def rect_center(rect: Rect) -> Vec2:
	top_left, bottom_right = rect
	return Vec2(top_left.x + (bottom_right.x - top_left.x)/2,
				top_left.y + (bottom_right.y - top_left.y)/2 )

def is_in_rect(point: Vec2, rect: Rect) -> bool:
	top_left, bottom_right = rect
	return \
		top_left.x <= point.x <= bottom_right.x and \
		top_left.y <= point.y <= bottom_right.y
