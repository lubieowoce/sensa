from typing import Tuple

import imgui as im
from imgui_widget import child

import contextlib




@contextlib.contextmanager
def draggable(name: str, was_held: bool, width: float, height: float) -> Tuple[str, bool]:
	with child(name=name+"_frame", border=True,
				width=width, height=height,
				styles={im.STYLE_WINDOW_PADDING: (0,0)}):
		prev_cursor_screen_pos = im.get_cursor_screen_position()

		_ = im.invisible_button(name+"_invisible_button", width, height)
		# _ = im.button("{},{}".format(width,height), width, height)
		is_held = im.is_item_active()
		status = {
			(False, False): 'idle',
			(False, True) : 'pressed',
			(True,  True) : 'held',
			(True,  False): 'released',
		}[(was_held, is_held)]

		im.set_cursor_screen_position(prev_cursor_screen_pos)

		with child(name=name+"_content", flags=im.WINDOW_NO_INPUTS,
					width=width, height=height,
					styles={im.STYLE_WINDOW_PADDING: (0,0)}):

			yield (status, is_held)
			
	return True
