from functools import partial

import imgui as im

class NoWidget(Exception): pass

# TODO: consider switching to contextlib.@contextmanager

# TODO: Add a styles parameter - using imgui.styled one property at a time will be cumbersome.
# Also, it doesn't look good with the IM contexts, as it needlessly increases nesting.

class IM():
	def __init__(im, begin, end, **kwargs):
		im.begin = begin
		im.args = kwargs
		im.end = end


	def __enter__(im):
		ret = im.begin(**im.args)
		return ret
	def __exit__(im, *args):
		im.end()





window = partial(IM, begin=im.begin, end=im.end)
group  = partial(IM, begin=im.begin_group, end=im.end_group)
child  = partial(IM, begin=im.begin_child, end=im.end_child)

