from typing import (
	Sequence, Tuple,  Optional
)
from sensa_util.types import (
	K, A,
	OrderedDict_,
	IMGui,
)

import imgui as im
from sensa_util import is_sequence_unique


def str_combo(name: str,
			  current_option: str,
			  options: Sequence[str],
			  label_left: bool = False) -> IMGui[Tuple[bool, str]]:

	assert current_option in options, \
		"Current_option {co} not in options ({opts})"\
		 .format(co=current_option, opts=options) 
	assert is_sequence_unique(options), "Duplicate options: {}".format(options)

	cur_option_ix = options.index(current_option)

	if label_left:
		imgui_label = "##"+name
		im.text(name)
		im.same_line()
	else:
		imgui_label = name
	changed, selected_ix = im.combo(imgui_label, cur_option_ix, options)

	assert selected_ix in range(len(options)), \
		"Index ({ix}) not in list: {opts}, len={lo}" \
		 .format(ix=selected_ix, opts=options, lo=len(options))
	return (changed, options[selected_ix])


NOTHING_SELECTED_TEXT = '---'

def str_combo_with_none(name: str,
			  			o_current_option: Optional[str],
			  			options: Sequence[str],
			  			nothing_text=NOTHING_SELECTED_TEXT,
			  			label_left: bool = False) -> IMGui[Tuple[bool, Optional[str]]]:

	assert is_sequence_unique(options + [nothing_text]),\
		"Option named same as `nothing_text`. Options: {}".format(options)
	if o_current_option != None:
		assert o_current_option in options, \
			"Current_option {co} not in options ({opts})"\
			 .format(co=o_current_option, opts=options)
	current_option_text = o_current_option if o_current_option != None else nothing_text
	changed, selected_str = str_combo(
								name, current_option_text,
								options=[nothing_text] + options,
								label_left=label_left
							)
	o_selected_val = selected_str if selected_str != nothing_text else None
	return (changed, o_selected_val)


# def combo_with_empty(name: str,
# 					 current_option: Tuple[str, A],
# 					 options: OrderedDict_[str, A],
# 					 empty_text=EMPTY_TEXT) -> IMGui[Tuple[bool, Optional[A]]]:
# 	options_list = ordered_dict_to_list(options)
# 	options_with_empty = OrderedDict( [empty_text, None] + options_list)

# 	changed, o_val = combo(name, current_option, options_with_empty)
# 	return changed, o_val

# def combo(name: str,
# 		  current_option: Tuple[str, A],
# 		  options: OrderedDict_[str, A]) -> IMGui[Tuple[bool, A]]:
# 	cur_option_text, _ = current_option
# 	options_texts = ordered_dict_keys(options)
# 	option_values = ordered_dict_values(options)

# 	changed, selected_ix = im.combo("channel", , options_texts)
# 	return (changed, option_values[selected_ix])




def ordered_dict_to_list(odict: OrderedDict_[K, A]) -> Sequence[Tuple[K, A]]:
	return [(key, value) for (key, value) in odict.items()]

def ordered_dict_keys(odict: OrderedDict_[K, A]) -> Sequence[K]:
	return [key for (key, _) in odict.items()]

def ordered_dict_values(odict: OrderedDict_[K, A]) -> Sequence[K]:
	return [value for (_, value) in odict.items()]