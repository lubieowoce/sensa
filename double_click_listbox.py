

from typing import Tuple, Sequence
import imgui as im



def double_click_listbox(state: tuple, options: Sequence[str]) -> Tuple[bool, bool, tuple]:
	"""
	Good for item-pickers where only one item can be selected, like tool pickers.
	Offers a similar API to imgui.listbox, with important differences:
	- Only one item selected at a time
	- Allows double-clicks on items, and distinguishes them
	  from single clicks

	Takes a tuple representing the selection state (explained further)
	and a sequence of string labels, and returns a triple: 
	```
		state_changed: bool, 	# Anything in the state changed:
								# for example, stopped waiting for second click
								# and switched `('waiting', ix, t) -> ('idle', ix)`
								# Useful to know if you should update the stored state.

		selection_changed: bool # The selected item changed:
								# stays false e.g when the list stops waiting for the
								# second click, that is on changes `('waiting', ix, t) -> ('idle', ix)`
								# Useful to know if the selection changed.
		new selection state: tuple  # Explained below.
	```
	The selection state is a normal tuple of one of the following shapes: 
	```
	('no_selection',   None)
	('idle', 		   int)			# item selected, not waiting for double-click
	('waiting', 	   int, float)	# item selected, but the user might click a second time, creating a double-click
	('double_clicked', int)			# item at index was double-clicked
	#				   ^ state[1]: the index of the selected item in `options`
	#					    ^ state [2]: the time (in seconds) of the click

	```
	prev_state = my_global_state['tool_picker_state']

	opts = ['first', 'second', 'third']
	state_changed, selection_changed, state = double_click_listbox(prev_state, opts)
	if state_changed:
		my_global_state['tool_picker_state'] = state

	if state[0] == 'double_clicked':
		_, ix = state
		... # ix was double-clicked 
	elif selection_changed:
		_, ix = state
		... # ix was selected


	
	The initial state for a `double_click_listbox is usually `('no_selection', None)`,
	or `('idle', ix)` if ix should be selected by default.

	"""
	prev_state = state
	prev_variant = prev_state[0]
	prev_o_selection = prev_state[1]

	changed_option = None
	for ix, option in enumerate(options):
		was_selected = prev_o_selection is not None and prev_o_selection == ix
		changed, selected = im.selectable(option, was_selected)

		if changed:
			changed_option = (ix, selected)

	# Now we know which one (if any) changed and how
	# Time to work those state machines!
	state = None

	if prev_variant == 'no_selection':
		if changed_option is None:
			state = prev_state
		else:
			ix, _ = changed_option
			state = ('waiting', ix, im.get_time())

	elif prev_variant == 'idle':
		if changed_option is None:
			state = prev_state
		else:
			ix, selected = changed_option
			state = ('waiting', ix, im.get_time())

	elif prev_variant == 'waiting':
		_, prev_selection, selected_t = prev_state
		current_t = im.get_time()
		time_is_up = current_t - selected_t >= im.get_io().mouse_double_click_time
		if changed_option is None:
			if time_is_up:
				state = ('idle', prev_selection)
			else:
				state = prev_state
		else: # changed_option is not None
			ix, selected = changed_option
			if time_is_up:
				if ix == prev_selection:
					# start waiting again
					state = ('waiting', prev_selection, current_t)
				else: # ix != prev_selection
					state = ('waiting', ix, current_t)
			else: # not time_is_up
				if ix == prev_selection:
					assert not selected
					state = ('double_clicked', prev_selection)
				else: # ix != prev_selection
					state = ('waiting', ix, current_t)

	elif prev_variant == 'double_clicked':
		_, prev_selection = prev_state
		state = ('idle', prev_selection)

	else:
		raise Exception("Invalid state (see this function's help): " + str(prev_state))

	selection_changed = state[1] != prev_state[1]
	state_changed     = state != prev_state
	return state_changed, selection_changed, state

			# state = ('waiting', ix, im.get_time())


# TODO: 
# 	Maybe we could avoid storing the click time
# 	by checking if a potential double-click is in progress?
# 	
# 	Trouble is, for now we can only do that using
# 	`io._mouse_clicked_time` (ImGuiIO.MouseClickedTime)
# 	which is an internal ImGui attribute and could change in the future.
#
# def is_mouse_potentially_double_clicking():
# 	io = im.get_io()
# 	f_clicked_t = io._mouse_clicked_time[0]
#   # ^ time (s) as a float, resets to FLT_MIN after a double_click
# 	o_clicked_t = f_clicked_t if f_clicked_t >= 0 else None
# 	double_click_dur = io.mouse_double_click_time
# 	current_t = im.get_time()
#
# 	return (
# 		o_clicked_t is not None
# 		and current_t - o_clicked_t <= double_click_dur
# 	)
# 
	
