from functools import partial
from types_util import IMGui
from typing import Any

import imgui




class IM:
	def __init__(im, begin, end, *args, **kwargs):
		im.begin = begin
		im.end = end
		im.args = args
		im.kwargs = kwargs

	def __enter__(im) -> IMGui[Any]:
		return im.begin(*im.args, **im.kwargs) 

	def __exit__(im, exc_type, exc, traceback) -> IMGui[None]:
		im.end()
		if exc_type == _DontDrawWindowException:
			return True # swallow the exception


window = partial(IM, imgui.begin, 		imgui.end)
group  = partial(IM, imgui.begin_group, imgui.end_group)
child  = partial(IM, imgui.begin_child, imgui.end_child)



class _DontDrawWindowException(Exception): pass

def only_draw_if(cond: bool):
	"""
	NOTE:
		This is meant to be used to improve performance,
		but I haven't actually profiled it; for cheap
		window bodies, the overhead of throwing an exception
		could conceivably overshadow any speed gains. I could be wrong
		though.

	This is meant as a replacement for this idiom:
	```
	if imgui.begin("test"):
		...
		imgui.end()
	```
	which is not easily possible with a context manager, as it
	necessarily has to execute the body.

	Intended usage:
	```
	with window("test") as (expanded, _):
		only_draw_if(expanded)
		im.text("This line won't be executed if the window is collapsed")
	```
	It could also be used with a visibility check:
		only_draw_if(some_function_to_check_if_window_is_visible())

	The only thing `only_draw_if()` does is raise a 
	special exception that aborts the `with` block, but is 
	caught and swallowed by `window`'s `__exit__`.
	"""
	if not cond:
		raise _DontDrawWindowException()




class IMColor:
	def __init__(imc, colors):
		imc.colors = colors

	def __enter__(imc) -> IMGui[None]:
		for (col_var, color) in imc.colors.items():
			imgui.push_style_color(col_var, *color)

	def __exit__(imc, *args) -> IMGui[None]:
		imgui.pop_style_color(len(imc.colors))

color = IMColor


class IMStyle:
	def __init__(ims, styles):
		ims.styles = styles

	def __enter__(ims) -> IMGui[None]:
		for (style_var, value) in ims.styles.items():
			imgui.push_style_var(style_var, value)

	def __exit__(ims, *args) -> IMGui[None]:
		imgui.pop_style_var(len(ims.styles))


style = IMStyle






# @contextmanager
# def child(**kwargs):
# 	styles = kwargs.pop('styles', None)
# 	args = kwargs

# 	if styles != None:
# 		for name, value in styles.items():
# 			imgui.push_style_var(name, value)

# 	is_visible = imgui.begin_child(**args)
	
# 	# if is_visible:
# 	# 	yield is_visible
# 	yield is_visible

# 	imgui.end_child()

# 	if styles != None:
# 		imgui.pop_style_var(len(styles))