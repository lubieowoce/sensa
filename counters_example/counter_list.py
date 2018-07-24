from utils import (err_unsupported_action)

from utils.types import (
	Any,
	PMap_,
	Action,
	Fun,
	IO_, IMGui,
)

import imgui as im
from imgui_widget import window, child
from pyrsistent import (m, v, thaw, freeze)
from id_eff import IdEff, id_and_effects
from counter import counter, set_value, increment, decrement

# counter_list = lambda id: m(id=id, items=v())

ADD_COUNTER    = "ADD_COUNTER"
REMOVE_COUNTER = "REMOVE_COUNTER"
CLEAR_COUNTERS = "CLEAR_COUNTERS"

add_counter    = lambda: m(type=ADD_COUNTER)
remove_counter = lambda: m(type=REMOVE_COUNTER)
clear_counters = lambda: m(type=CLEAR_COUNTERS)

@id_and_effects
def update_counter_list(state, action) -> IdEff[PMap_[str, Any]]:
	# state = { counters: {id: co}, counter_list: [id]}


	if action.type == ADD_COUNTER:
		id = get_id()
		# return \
		# 	state.transform(
		# 		   ['counters'], lambda counters: counters.set(id, counter(id)),
		# 		   ['counter_list'], lambda list: list.append(id) )
		st = thaw(state)
		st['counters'][id] = counter(id)
		st['counter_list'].append(id)
		return freeze(st)

	elif action.type == REMOVE_COUNTER:
		if len(state.counter_list) > 0:
			list = state.counter_list
			id = list[len(list)-1]
			# return \
			# 	state.transform(
			# 		['counters'], lambda counters: counters.delete(id)
			# 		['counter_list'], lambda list: list.delete(len(list)-1) )
			st = thaw(state)
			st['counters'].pop(id)
			st['counter_list'].pop()
			return freeze(st)

		else: # len(counters) <= 0
			return state

	elif action.type == CLEAR_COUNTERS:
		return \
		 	state.set('counters', m()).set('counter_list', v())
	else:
		err_unsupported_action(state, action)
		return state


def draw_counter_list(state, emit: Fun[[Action], IO_[None]]) -> IMGui[None]:
	with window(name="counters"):
	    im.text("counters")
	    # with im.styled(im.STYLE_CHILD_WINDOW_ROUNDING, im.STYLE_WINDOW_ROUNDING):
	    with child(name="add+delete",  width=40, height=100,
	               styles={im.STYLE_CHILD_WINDOW_ROUNDING: im.STYLE_WINDOW_ROUNDING}):

	        if im.button("+", width=30, height=30):
	            emit(add_counter())
	            
	        if im.button("-", width=30, height=30):
	            emit(remove_counter())

	        if im.button("clear", width=30, height=30):
	            emit(clear_counters())


	    im.same_line()
	    for id in state.counter_list:

	        with child(name="counter "+str(id), width=100, height=100, border=True,
	                   styles={im.STYLE_CHILD_WINDOW_ROUNDING: im.STYLE_WINDOW_ROUNDING}) as is_counter_visible:
	            if is_counter_visible:
	                im.text(str(state.counters[id].val))

	                im.separator()

	                changed, new_val = \
	                    im.input_text('value', value=str(state.counters[id].val),
	                                  buffer_length=1000,
	                                  flags=im.INPUT_TEXT_ENTER_RETURNS_TRUE | im.INPUT_TEXT_CHARS_DECIMAL)
	                if changed:
	                    emit( set_value(new_val, id) )


	                if im.button("+"):
	                    emit( increment(1, id) )

	                if im.button("-"):
	                    emit( decrement(1, id))

	        im.same_line()

	    im.new_line()