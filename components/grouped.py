from functools import partial
from utils.types import IMGui
from typing import Any, Callable, Generic, TypeVar, Optional

import imgui


__all__ = [
	'window',
	'child',
	'group',
	'only_draw_if',
]



A = TypeVar('A')

class _IMGuiCtx(Generic[A]):
	__slots__ = ('begin', 'end', 'args', 'kwargs')

	"Wrap imgui begin_*/end_* functions with a context manager"
	def __init__(self, begin: Callable[..., A], end: Callable[[], Any], *args, **kwargs) -> None:
		self.begin = begin
		self.end = end
		self.args = args
		self.kwargs = kwargs

	def __enter__(self) -> IMGui[A]:
		return self.begin(*self.args, **self.kwargs) 

	def __exit__(self, exc_type, exc, traceback) -> IMGui[Optional[bool]]:
		self.end()
		if exc_type == _DontDrawWindowException:
			return True # swallow the exception


window = partial(_IMGuiCtx, imgui.begin,       imgui.end)
group  = partial(_IMGuiCtx, imgui.begin_group, imgui.end_group)
child  = partial(_IMGuiCtx, imgui.begin_child, imgui.end_child)



class _DontDrawWindowException(Exception): pass

def only_draw_if(cond: bool) -> None:
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