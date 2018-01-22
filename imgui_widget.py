from functools import partial
# from contextlib import contextmanager
from types_util import IMGui

import imgui





class IM():
	def __init__(im, begin, end, **kwargs):

		im.begin = begin
		im.end = end
		im.styles = kwargs.pop('styles', None)
		im.flags  = kwargs.pop('flags', None)
		im.args = kwargs



	def __enter__(im) -> IMGui[None]:
		if im.styles != None:
			for name, value in im.styles.items():
				imgui.push_style_var(name, value)
		if im.flags != None:
			ret = im.begin(flags=im.flags, **im.args)
		else:
			ret = im.begin(**im.args)
		return ret

	def __exit__(im, *args) -> IMGui[None]:
		im.end()
		if im.styles != None:
			imgui.pop_style_var(len(im.styles))





window = partial(IM, begin=imgui.begin, end=imgui.end)
group  = partial(IM, begin=imgui.begin_group, end=imgui.end_group)
child  = partial(IM, begin=imgui.begin_child, end=imgui.end_child)


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