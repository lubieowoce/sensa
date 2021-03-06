from typing import Tuple

import imgui as im
from components.grouped import child
from components.styled import style

import contextlib




@contextlib.contextmanager
def draggable(name: str, was_down: bool, width: float, height: float) -> Tuple[str, bool]:

	with style({im.STYLE_WINDOW_PADDING: (0,0)}), \
		 child(name=name+"_frame", border=True,
			   width=width, height=height):
		prev_cursor_screen_pos = im.get_cursor_screen_position()

		_ = im.invisible_button(name+"_invisible_button", width, height)
		# _ = im.button("{},{}".format(width,height), width, height)
		is_down = im.is_item_active()
		status = {
			(False, False): 'idle',
			(False, True) : 'pressed',
			(True,  True) : 'held',
			(True,  False): 'released',
		}[(was_down, is_down)]

		im.set_cursor_screen_position(prev_cursor_screen_pos)

		# The window takes no inputs, so it's okay that we 
		# draw the button first - clicks just pass through the window

		with style({im.STYLE_WINDOW_PADDING: (0,0)}), \
			 child(name=name+"_content", flags=im.WINDOW_NO_INPUTS,
					width=width, height=height):

			yield (status, is_down)
			
	return True
