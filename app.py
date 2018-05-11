from imgui_glfw_app import run_imgui_glfw_app

import imgui as im

from pyrsistent import (m , pmap,) #thaw, freeze,)#v, pvector)

from typing import (
	Any,
	NamedTuple, Optional, Union,
)
from types_util import (
	PMap_,
	Action, Effect,
	IO_,
)

from debug_util import (
	debug_initialize,
	debug_window,
	debug_log, debug_log_dict, debug_log_crash,
	debug_post_frame,
)

from uniontype import union

from eff import (
	Eff, run_eff,
	effectful,
	ID, EFFECTS, SIGNAL_ID, ACTIONS,
	get_ids,
	eff_operation,
	get_signal_ids,
)

from imgui_widget import window, child

import node_graph as ng

from signal_source import (
	initial_source_state,
	update_source, SourceAction,
	signal_source_window,
)

from filter_box import (
	initial_filter_box_state,
	update_filter_box, FILTER_BOX_ACTION_TYPES,
	filter_box_window, 
	# is_filter_box_full,
)

from filters import available_filters

from plot import (
	initial_plot_box_state,
	update_plot_box, PLOT_BOX_ACTION_TYPES,
	signal_plot_window,
)


from files import (
	FileAction,
	FileEffect,
	handle_file_effect,
	example_file_path,
)

import flags

import sensa_util as util

window_title = "Sensa"
initital_window_size = (1280, 850)
target_framerate = 30.

INITIAL_ACTIONS = [FileAction.Load(filename=example_file_path)]




current_id = None
current_signal_id = None
state = None
ui = None

frame_actions = None



def sensa_app_init():
	global current_id
	global current_signal_id
	global state
	global frame_actions
	global ui

	if flags.DEBUG:
		debug_initialize()


	current_id = 0
	current_signal_id = 0
	
	# create the initial state	
	state, eff_res = run_eff(initial_state, id=current_id, actions=[])()
	current_id        = eff_res[ID]
	for action in eff_res[ACTIONS]:
		state, eff_res = run_eff(update, actions=[], effects=[])(state, action)

		eff_res[ACTIONS].extend(eff_res[ACTIONS]) # so we can process actions emitted during updating, if any

		for command in eff_res[EFFECTS]:
			state, eff_res = run_eff(handle, signal_id=current_signal_id)(state, command)
			current_signal_id = eff_res[SIGNAL_ID]

	assert state != None

	# run the initial actions
	for act in INITIAL_ACTIONS:

		state, eff_res = run_eff(update, actions=[], effects=[])(state, act)

		INITIAL_ACTIONS.extend(eff_res[ACTIONS]) # so we can process actions emitted during updating, if any

		for command in eff_res[EFFECTS]:
			state, eff_res = run_eff(handle, signal_id=current_signal_id)(state, command)
			current_signal_id = eff_res[SIGNAL_ID]


	assert state != None


	# Demo
	global SOURCE_BOX_ID, FILTER_BOX_1_ID, FILTER_BOX_2_ID, PLOT_1_ID, PLOT_2_ID
	FILTER_BOX_1_ID = min(state.filter_boxes.keys())
	FILTER_BOX_2_ID = max(state.filter_boxes.keys())
	SOURCE_BOX_ID = min(state.source_boxes.keys())
	PLOT_1_ID = min(state.plots.keys())
	PLOT_2_ID = max(state.plots.keys())
	# End Demo


	ui = {
		'settings': {
			'plot_window_movable': True,
			'numpy_resample': True,
			'filter_slider_power': 3.0,
		},
	}

	


def draw_and_log_actions() -> IO_[None]:
	global frame_actions

	_, eff_res = run_eff(  draw,   actions=[])()

	frame_actions = eff_res[ACTIONS]
	# since this will be called by run_glfw_app,
	# writing to frame_actions is the only way to communicate
	# with the rest of our code



def sensa_post_frame() -> IO_[None]:
	global state
	global frame_actions

	update_state_with_frame_actions_and_run_effects()
	frame_actions.clear()

	if flags.DEBUG:
		debug_post_frame()
		debug_window()




def update_state_with_frame_actions_and_run_effects() -> IO_[None]:
	global state
	global frame_actions
	global current_signal_id

	actions_to_process = frame_actions[:]

	for action in actions_to_process:
		try:
			# note: `frame_actions` might be modified if `update` emits actions
			state, eff_res = run_eff(update, actions=[], effects=[])(state, action)

		except Exception as ex:
			debug_log_crash(origin='update', cause=action, exception=ex)
			actions_to_process.clear()
			break

		else:
			actions_to_process.extend(eff_res[ACTIONS]) # so we can process actions emitted during updating, if any

			debug_log('effects', eff_res[EFFECTS])
			for command in eff_res[EFFECTS]:
				try:
					state, eff_res = run_eff(handle, signal_id=current_signal_id)(state, command)
				except Exception as ex:
					debug_log_crash(origin='handle', cause=command, exception=ex)
					break
				else:
					current_signal_id = eff_res[SIGNAL_ID]




	# # Debug
	# if len(actions_to_process) > 0:
	# 	debug_log('actions', list(actions_to_process))

	debug_log_dict('state (no signals)', state.set('data', state.data.remove('signals')) )
	# End Debug





# ==============================================




AppState = PMap_[str, Any]

@effectful(ID, ACTIONS)
def initial_state() -> Eff(ID, ACTIONS)[AppState]:
	emit = eff_operation('emit')
	# output_signal_names = pmap({sig_id: 'filter_{id}_output'.format(id=id) 
	# 							for (id, sig_id) in output_ids.items()})



	n_source_boxes = 1
	source_boxes = pmap({box.id_: box
					  	 for box in (initial_source_state() for _ in range(n_source_boxes))})
	# n_filter_boxes = 2
	filter_boxes = pmap({box.id_: box
					  	 for box in (initial_filter_box_state(filter_id=filter_id) for filter_id in available_filters.keys())})
	n_plots = 2
	plots = pmap({plot.id_: plot
				  for plot in (initial_plot_box_state() for _ in range(n_plots))})

	for group in (source_boxes, filter_boxes, plots):
		for (id_, box) in group.items():
			emit(ng.AddNode(id_, box.to_node()))

	return m(
		graph = ng.empty_graph,

		data = m(
			signals = m(),      # type: PMap_[SignalId, Signal]
			signal_names = m(), # type: PMap_[SignalId, str]
			box_outputs = m()    # type: PMap_[Id, Maybe[Signal]] 
	    ),
	    link_selection = LinkSelection.empty,
		source_boxes = source_boxes,
		plots = plots,
		filter_boxes = filter_boxes,
	)

# Demo
SOURCE_BOX_ID = None
PLOT_1_ID = None
PLOT_2_ID = None
FILTER_BOX_1_ID = None
FILTER_BOX_2_ID = None
# End Demo

# --------------------



@effectful(ACTIONS, EFFECTS)
def update(state: AppState, action: Action) -> Eff(ACTIONS, EFFECTS)[AppState]:
	emit = eff_operation('emit'); emit_effect = eff_operation('emit_effect')

	new_state = None
	o_changed_box = None

	if type(action) == LinkSelectionAction:
		old_link_selection = state.link_selection
		link_selection = update_link_selection(old_link_selection, state.graph, action)
		
		if link_selection.src_slot != None and link_selection.dst_slot != None:
			link = (link_selection.src_slot, link_selection.dst_slot)

			can_create_link     = ng.is_input_slot_free(state.graph, link[1])
			link_already_exists = link in state.graph.links
			if link_already_exists:
				emit( ng.Disconnect(*link) )
			elif can_create_link:
				emit( ng.Connect(*link) )
			else: 
				# link is invalid - e.g. connects to a filled slot
				# but we empty it after anyway, so do nothing
				pass
			
			link_selection = LinkSelection.empty

		new_state = state.set('link_selection', link_selection)

	elif type(action) == ng.GraphAction:
		graph = state.graph
		new_state = state.set('graph', ng.update_graph(graph, action))

	elif type(action) == SourceAction:
		debug_log('updating', 'source')
		target_id = action.id_

		old_source_box_state = state.source_boxes[target_id]
		new_source_box_state = update_source(old_source_box_state, action) # might emit effects
		if not (old_source_box_state is new_source_box_state):
			source_boxes = state['source_boxes']
			new_state = state.set('source_boxes', source_boxes.set(target_id, new_source_box_state))
			o_changed_box = target_id

	elif type(action) in FILTER_BOX_ACTION_TYPES:
		debug_log('updating', 'filter box')
		target_id = action.id_

		old_filter_box_state = state.filter_boxes[target_id]
		new_filter_box_state = update_filter_box(old_filter_box_state, action) # might emit effects
		if not (old_filter_box_state is new_filter_box_state):
			filter_boxes = state['filter_boxes']
			new_state = state.set('filter_boxes', filter_boxes.set(target_id, new_filter_box_state))
			o_changed_box = target_id


	elif type(action) in PLOT_BOX_ACTION_TYPES:
		# state_e['plots'][target_id] = update_plot(plot_state, state_e['data'], __plot_draw_area__, action)
		debug_log('updating', 'plot')
		target_id = action.id_

		plots = state['plots']
		old_plot_state = plots[target_id]

		new_plot_state = update_plot_box(old_plot_state,  action)
		# signal_data = state.data.box_outputs
		# new_plot_state = update_plot_box(old_plot_state, signal_data, action)

		if not (old_plot_state is new_plot_state): # reference comparison for speed
			new_state = state.set('plots', plots.set(target_id, new_plot_state))
			# o_changed_box = target_id



	elif type(action) == FileAction:
		if action.is_Load():
			emit_effect( FileEffect.Load(action.filename) ) 


	if o_changed_box != None:
		# emit(ng.NodeChanged(id_=o_changed_box))
		emit_effect(ng.EvalGraph())

	return new_state if new_state != None else state








# ------------------------

@effectful(SIGNAL_ID)
def handle(state: AppState, command) -> Eff(SIGNAL_ID)[IO_[AppState]]:

	if type(command) == FileEffect:

		new_signals, new_signal_names = handle_file_effect(state.data.signals, state.data.signal_names, command)

		data = state['data']
		return state.set('data', data \
									.set('signals',      new_signals)
									.set('signal_names', new_signal_names)
						)
	elif type(command) == ng.GraphEffect:
		boxes = sum((state.source_boxes, state.filter_boxes, state.plots), m())
		new_box_outputs = ng.handle_graph_effect(
								graph=state.graph,
								source_signals=state.data.signals,
								boxes=boxes,
								command=command
						  )

		data = state['data']
		return state.set('data', data.set('box_outputs', new_box_outputs))  

	else:
		return state


# =======================================================

LinkSelection = NamedTuple('LinkSelection', [
							('src_slot', Optional[ng.OutputSlotId]),
							('dst_slot', Optional[ng.InputSlotId]) ])
LinkSelection.empty = LinkSelection(src_slot=None, dst_slot=None)

LinkSelectionAction, \
	ClickOutput, \
	ClickInput, \
	Clear, \
= union( 
'LinkSelectionAction', [
	('ClickOutput',  [('slot', ng.OutputSlotId)]),
	('ClickInput',   [('slot', ng.InputSlotId)]),
	('Clear', [])
 ])


def update_link_selection(state: LinkSelection, graph, action: LinkSelectionAction) -> LinkSelection:
	if action.is_ClickOutput():
		return (LinkSelection.empty  if state.src_slot != None else
				state._replace(src_slot=action.slot) )

	if action.is_ClickInput():
		return (LinkSelection.empty  if state.dst_slot != None else
				state._replace(dst_slot=action.slot) )

	elif action.is_Clear(): return LinkSelection.empty
	else: util.impossible()

# ----------------------------------------------------------



@effectful(ACTIONS)
def draw() -> Eff(ACTIONS)[None]:
	emit = eff_operation('emit')

	global state

	im.show_metrics_window()
	im.show_test_window()



	# ------------------------
	t_flags = 0
	# t_flags = (
	# 	  im.WINDOW_NO_TITLE_BAR
	# 	| im.WINDOW_NO_MOVE
	# 	| im.WINDOW_NO_RESIZE
	# 	| im.WINDOW_NO_COLLAPSE
	# 	| im.WINDOW_NO_FOCUS_ON_APPEARING
	# 	| im.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
	# )
	with window(name="test", flags=t_flags):
		im.button("bloop")
	# 	pos = util.point_offset(im.get_window_position(), im.Vec2(40, 80))
	# 	im.set_next_window_position(pos.x, pos.y)
	# 	with window(name="a window"):
	# 		im.text("I'm a window")

	# 	top_left = im.get_item_rect_min()
	# 	size = im.get_item_rect_size()
	# 	bottom_right = util.point_offset(top_left, size)
	# 	im.text('TL: '+str(top_left))
	# 	im.text('BR: '+str(bottom_right))
	# 	util.add_rect(im.get_window_draw_list(), util.Rect(top_left, bottom_right), (1.,1.,1.,1.))

	with window(name="signals"):
		if im.button("load example"):
			emit( FileAction.Load(filename=example_file_path) )


		if len(state.data.signals) > 0:

			def right_pad(s: str, limit: int) -> str:
				n_spaces = max(0, limit-len(s))
				return s + (' ' * n_spaces)

			for sig_id, sig_name in sorted(state.data.signal_names.items(), key=lambda pair: pair[1]):
				im.text_colored(right_pad(sig_name,5), 0.2, 0.8, 1)
				im.same_line()
				signal = state.data.signals[sig_id]
				im.text(str(signal))
		else:
			im.text("No signals loaded")


	# -------------------------

	with window(name="settings"):
		ui_settings = ui['settings']
		changed, move = im.checkbox("move plots", ui_settings['plot_window_movable'])
		if changed:
			ui_settings['plot_window_movable'] = move

		im.same_line()

		changed, val = im.checkbox("numpy resample", ui_settings['numpy_resample'])
		if changed:
			ui_settings['numpy_resample'] = val


		changed, val = im.slider_float('filter_slider_power', ui_settings['filter_slider_power'],
									   min_value=1., max_value=5.,
									   power=1.0)
		if changed:
			ui_settings['filter_slider_power'] = val


	# ----------------------------
	# ng.graph_window(state.graph)


	prev_color_window_background = im.get_style().color(im.COLOR_WINDOW_BACKGROUND)

	im.push_style_color(im.COLOR_WINDOW_BACKGROUND, 0., 0., 0., 0.05)
	im.set_next_window_position(0, 100)
	with window(name="nodes", 
				flags = (
					  im.WINDOW_NO_TITLE_BAR
					# | im.WINDOW_NO_MOVE
					# | im.WINDOW_NO_RESIZE
					| im.WINDOW_NO_COLLAPSE
					| im.WINDOW_NO_FOCUS_ON_APPEARING
					| im.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
				)
				):
		box_positions = {}
		inputs = ng.get_inputs(state.graph, state.data.box_outputs)


		im.push_style_color(im.COLOR_WINDOW_BACKGROUND, *prev_color_window_background)

		# source box
		pos = signal_source_window(state.source_boxes[SOURCE_BOX_ID],
							 state.data.signals,
							 state.data.signal_names)
		box_positions[SOURCE_BOX_ID] = pos


		# signal plot 1
		pos = signal_plot_window(state.plots[PLOT_1_ID],
							inputs[PLOT_1_ID],
							ui_settings=ui['settings'])
		box_positions[PLOT_1_ID] = pos


		# filter box 1
		pos = filter_box_window(state.filter_boxes[FILTER_BOX_1_ID],
						  	ui_settings=ui_settings)
		box_positions[FILTER_BOX_1_ID] = pos


		# filter box 2
		pos = filter_box_window(state.filter_boxes[FILTER_BOX_2_ID],
						  	ui_settings=ui_settings)
		box_positions[FILTER_BOX_2_ID] = pos


		# signal plot 2
		pos = signal_plot_window(state.plots[PLOT_2_ID],
							inputs[PLOT_2_ID],
							ui_settings=ui['settings'])
		box_positions[PLOT_2_ID] = pos

		
		im.pop_style_color()



		# connections between boxes
		link_selection = state.link_selection

		prev_cursor_screen_pos = im.get_cursor_screen_position()

		# get slot coords and draw slots
		im.push_style_color(im.COLOR_CHECK_MARK, *(0, 0, 0, 100/255))

		draw_list = im.get_window_draw_list()
		SPACING = 20.
		slot_center_positions = {}

		for (id_, position) in box_positions.items():
			node = state.graph.nodes[id_]

			left_x = position.top_left.x
			right_x = position.bottom_right.x
			top_y = position.top_left.y

			for slot_ix in range(node.n_inputs):
				pos = im.Vec2(left_x-20-3, top_y+30+slot_ix*SPACING)
				im.set_cursor_screen_position(pos)

				slot = ng.InputSlotId(id_, slot_ix)
				was_selected = (slot == link_selection.dst_slot)

				changed, selected = im.checkbox("##in{}{}".format(id_, slot_ix), was_selected)
				if changed:
					emit(ClickInput(slot))

				center_pos = util.rect_center(util.get_item_rect()) # bounding rect of prev widget
				slot_center_positions[('in', id_, slot_ix)] = center_pos

			for slot_ix in range(node.n_outputs):
				pos = im.Vec2(right_x+3, top_y+30+slot_ix*SPACING)
				im.set_cursor_screen_position(pos)

				slot = ng.OutputSlotId(id_, slot_ix)
				was_selected = (slot == link_selection.src_slot)

				changed, selected = im.checkbox("##out{}{}".format(id_, slot_ix), was_selected)
				if changed:
					emit(ClickOutput(slot))

				center_pos = util.rect_center(util.get_item_rect()) # bounding rect of prev widget
				slot_center_positions[('out', id_, slot_ix)] = center_pos

		im.pop_style_color()
		




		# draw links
		for (src, dst) in state.graph.links:
			src_pos = slot_center_positions[('out', src.node_id, src.ix)]
			dst_pos = slot_center_positions[('in',  dst.node_id, dst.ix)]
			draw_list.add_line(src_pos, dst_pos, color=(0.5, 0.5, 0.5, 1.), thickness=2.)


		im.set_cursor_screen_position(prev_cursor_screen_pos)
	# end nodes window

	im.pop_style_color()


	im.show_style_editor()

	# debug_log_dict("first plot", state.plots[PLOT_1_ID].as_dict())

 	

# ===================================================



if __name__ == "__main__":
	run_imgui_glfw_app(app_init=sensa_app_init, draw=draw_and_log_actions, post_frame=sensa_post_frame,
					   target_framerate=target_framerate,
					   window_title=window_title,
					   window_size=initital_window_size)



# if imgui.begin_main_menu_bar():
#     if imgui.begin_menu("File", True):

#         clicked_quit, selected_quit = imgui.menu_item(
#             "Quit", 'Cmd+Q', False, True
#         )

#         if clicked_quit:
#             exit(1)

#         imgui.end_menu()
#     imgui.end_main_menu_bar()

# imgui.show_test_window()

# imgui.begin("Custom window", True)
# imgui.text(str(frame_dur))
# imgui.text_colored("Eggs", 0.2, 1., 0.)
# imgui.end()



# # drawing with begin and end
# def draw(state):
#     """
#     imgui.new_frame() is called right before `draw` in main.
#     imgui.render() is called `draw` returns.
#     """
#     im.begin("eeh")
#     # im.begin_group()
#     im.text("counters")
#     with im.styled(im.STYLE_CHILD_WINDOW_ROUNDING, im.STYLE_WINDOW_ROUNDING):
#         im.begin_child("add+delete",  width=40, height=100)
#         if im.button("+", width=30, height=30):
#             if len(state['counters']) <= 0:
#                 state['counters'][0] = 0
#             else: # len(state['counters']) > 0
#                 id = max(state['counters']) + 1
#                 state['counters'][id] = 0
			
#         if im.button("-", width=30, height=30):
#             if len(state['counters']) > 0:
#                 last_id = max(state['counters'])
#                 del state['counters'][last_id]

#         im.end_child()

#     im.same_line()
#     for id in state['counters']:
#         with im.styled(im.STYLE_CHILD_WINDOW_ROUNDING, im.STYLE_WINDOW_ROUNDING):
#             im.begin_child("counter "+str(id),  width=100, height=100, border=True)

#             im.text(str(state['counters'][id]))

#             imgui.separator()

#             changed, new_val = \
#                 im.input_text('value', value=str(state['counters'][id]),
#                               buffer_length=1000,
#                               flags=im.INPUT_TEXT_ENTER_RETURNS_TRUE | im.INPUT_TEXT_CHARS_DECIMAL)
#             if changed:
#                 state['counters'][id] = int(new_val)


#             if im.button("+"):
#                 state['counters'][id] += 1

#             if im.button("-"):
#                 state['counters'][id] -= 1

#             im.end_child()
#         im.same_line()

#     im.new_line()
#     im.end()