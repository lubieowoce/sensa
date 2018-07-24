from typing import Tuple, Sequence
from sensa_util.types import (
	# OrderedDict_,
	IMGui,
)

import imgui as im
from sensa_util import is_sequence_unique

# from collections import OrderedDict

def str_listbox(label: str, current_option: str, options: Sequence[str]) -> IMGui[Tuple[bool, str]]:


	assert current_option in options, \
		"Current_option {co} not in options ({opts})"\
		 .format(co=current_option, opts=options) 
	assert is_sequence_unique(options), "Duplicate options: {}".format(options)

	cur_option_ix = options.index(current_option)
	changed, selected_ix = im.listbox(label, cur_option_ix, options)
	assert selected_ix in range(len(options)), \
		"Index ({ix}) not in list: {opts}, len={lo}" \
		 .format(ix=selected_ix, opts=options, lo=len(options))
	return (changed, options[selected_ix])
