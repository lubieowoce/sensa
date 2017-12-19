from functools import partial

import imgui

from types_util import *

class NoWidget(Exception): pass

# TODO: consider switching to contextlib.@contextmanager

# TODO: Add a styles parameter - using imgui.styled one property at a time will be cumbersome.
# Also, it doesn't look good with the IM contexts, as it needlessly increases nesting.

class IM():
	def __init__(im, begin, end, **kwargs):

		im.begin = begin
		im.end = end
		im.styles = kwargs.pop('styles', None)
		im.args = kwargs



	def __enter__(im):
		if im.styles != None:
			for name, value in im.styles.items():
				imgui.push_style_var(name, value)
		ret = im.begin(**im.args)
		return ret

	def __exit__(im, *args):
		im.end()
		if im.styles != None:
			imgui.pop_style_var(len(im.styles))





window = partial(IM, begin=imgui.begin, end=imgui.end)
group  = partial(IM, begin=imgui.begin_group, end=imgui.end_group)
child  = partial(IM, begin=imgui.begin_child, end=imgui.end_child)

