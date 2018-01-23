from imgui_glfw_app import run_imgui_glfw_app

import imgui as im

from pyrsistent import (m , pmap,) #thaw, freeze,)#v, pvector)

from typing import (
	Any,
	List,
)
from types_util import (
	PMap_,
	Action, Effect,
	IO_,
)

from debug_util import (
	debug_initialize,
	debug_window,
	debug_log, debug_log_dict,
	debug_post_frame,
)


# from id_eff import IdEff, id_and_effects, run_id_eff, get_ids
from eff import (
	Eff, run_eff,
	effectful,
	ID, EFFECTS, SIGNAL_ID, ACTIONS,
	get_ids
)

from imgui_widget import window


from plot import (
	initial_signal_plot_state, update_plot,
	PlotState,
	PlotAction,
	signal_plot_window,
)

from filter_box import (
	initial_filter_box_state, update_filter_box,
	FilterBoxState,
	FilterBoxAction,
	filter_box_window, 
	FilterBoxEffect, handle_filter_box_effect,
	is_filter_box_full,
)

from files import (
	FileAction,
	FileEffect,
	handle_file_effect,
	example_file_path,
)

import flags


window_title = "Sensa"
initital_window_size = (1280, 850)
target_framerate = 30.

INITIAL_ACTIONS = [FileAction.Load(filename=example_file_path)]




current_id = None
current_signal_id = None
state = None
ui = None




def sensa_app_init():
	global current_id
	global current_signal_id
	global state
	global frame_actions
	global ui

	if flags.DEBUG:
		debug_initialize()


	current_id = 0
	
	# create the initial state	
	state, eff_res = run_eff(initial_state, id=current_id)()
	current_id = eff_res[ID]

	assert state != None

	# run the initial actions
	for act in INITIAL_ACTIONS:

		state, eff_res = run_eff(update, actions=[], effects=[])(state, act)

		INITIAL_ACTIONS.extend(eff_res[ACTIONS])
		for command in eff_res[EFFECTS]:
			state = handle(state, command)

	assert state != None


	# Demo
	global PLOT_1_ID, PLOT_2_ID, FILTER_BOX_ID
	PLOT_1_ID = min(state.plots.keys())
	PLOT_2_ID = max(state.plots.keys())
	FILTER_BOX_ID = min(state.filter_boxes.keys())
	# End Demo

	actions_initialize()

	ui = {
		'settings': {
			'plot_window_movable': False,
			'numpy_resample': True,
			'filter_slider_power': 3.0,
		}
	}

	






def sensa_post_frame():
	actions_post_frame()

	if flags.DEBUG:
		debug_post_frame()
		debug_window()



# ----------------------------------------


frame_actions = None

def actions_initialize():
	global frame_actions
	frame_actions = []

def _emit(action):
	frame_actions.append(action)

def clear_actions():
	frame_actions.clear()


def update_state_with_actions_and_run_effects() -> IO_[None]:
	global state
	global current_id
	global frame_actions

	for act in frame_actions:
		# note: `frame_actions` might be modified if `update` emits an action

		state, eff_res = run_eff(update, actions=[], effects=[])(state, act)

		frame_actions.extend(eff_res[ACTIONS])
		for command in eff_res[EFFECTS]:
			state = handle(state, command)





def actions_post_frame():
	global state
	assert state != None
	update_state_with_actions_and_run_effects()
	clear_actions()




# ==============================================




AppState = PMap_[str, Any]

@effectful(ID)
def initial_state() -> Eff(ID)[AppState]:

	filter_boxes = pmap({id: initial_filter_box_state(id)
					  		 for id in get_ids(1)})
	data = m(
		signals = m(),
		outputs = pmap({str(id): None for id in filter_boxes.keys()})
	)

	return m(

		data = data,
		plots = pmap({id: initial_signal_plot_state(id)
					  for id in get_ids(2)}),
		filter_boxes = filter_boxes,
	)

# Demo
PLOT_1_ID = None
PLOT_2_ID = None
FILTER_BOX_ID = None
# End Demo

# --------------------



@effectful(ACTIONS, EFFECTS)
def update(state: AppState, action: Action) -> Eff(ACTIONS, EFFECTS)[AppState]:

	new_state = None

	if type(action) == PlotAction:
		# state_e['plots'][target_id] = update_plot(plot_state, state_e['data'], __plot_draw_area__, action)

		target_id = action.id_

		plots = state['plots']
		old_plot_state = plots[target_id]

		# Demo
		signal_data = state.data.outputs if action.id_ == PLOT_2_ID else state.data.signals
		new_plot_state = update_plot(old_plot_state, signal_data, action)
		# End Demo
		# new_plot_state = update_plot(old_plot_state, state.data.signals, action)

		if not (old_plot_state is new_plot_state): # reference comparison for speed
			new_state = state.set('plots', plots.set(target_id, new_plot_state)) 


	elif type(action) == FilterBoxAction:
		target_id = action.id_

		old_filter_box_state = state.filter_boxes[target_id]
		new_filter_box_state = update_filter_box(old_filter_box_state, action) # might emit effects
		if not (old_filter_box_state is new_filter_box_state):
			filter_boxes = state['filter_boxes']
			new_state = state.set('filter_boxes', filter_boxes.set(target_id, new_filter_box_state))


	elif type(action) == FileAction:
		if action.is_Load():
			emit_effect( FileEffect.Load(action.filename) ) 



	# Demo

	if (type(action) == PlotAction
		and action.id_ == PLOT_1_ID
		and new_state != None
	   ):
		

		if action.is_SelectSignal():
			emit(
				FilterBoxAction.Connect(
					id_=FILTER_BOX_ID,
					signal_id=action.signal_id 
				)
			)



		elif action.is_SetTimeRange():
			if state.plots[PLOT_2_ID].is_Full():
				emit( action.set(id_=PLOT_2_ID) )

		elif action.is_SetEmpty():

			emit(
				FilterBoxAction.Disconnect(id_=FILTER_BOX_ID)
			)

			emit( action.replace(id_=PLOT_2_ID ) )


	if (new_state != None
		and state.plots[PLOT_2_ID].is_Empty()
		and is_filter_box_full(state.filter_boxes[FILTER_BOX_ID])
		and str(FILTER_BOX_ID) in state.data.outputs.keys()
		):
			emit(
				PlotAction.SelectSignal(
					id_=PLOT_2_ID,
					signal_id=str(FILTER_BOX_ID))
			)
	# End Demo





	return new_state if new_state != None else state


# ------------------------


def handle(state: AppState, command) -> IO_[AppState]:
	if type(command) == FileEffect:
		new_signals = handle_file_effect(state.data.signals, command)

		data = state['data']
		return state.set('data', data.set('signals', new_signals))

	elif type(command) == FilterBoxEffect:
		filter_box_id = command.id_
		filter_box_state = state.filter_boxes[filter_box_id]

		o_output = handle_filter_box_effect(filter_box_state, state.data.signals, command)

		# Demo
		output_id = str(filter_box_id)

		data    = state['data']
		outputs = data['outputs']
		return state.set('data', data.set('outputs', outputs.set(output_id, o_output) ))
		# End Demo

		# data    = state['data']
		# outputs = data['outputs']
		# return state.set('data', data.set('outputs', outputs.set(filter_box_id, o_output) ))

	else:
		return state


# =======================================================




def draw():
	global state


	assert len(frame_actions) == 0, "Actions buffer not cleared! Is:" + str(frame_actions) 


	im.show_metrics_window()

	# ------------------------

	with window(name="signals"):
		if im.button("load example"):
			emit( FileAction.LoadFile(filename=example_file_path))

		signals = state.data.signals
		if len(signals) > 0:
			labels = sorted(signals.keys())

			def right_pad(s: str, limit: int) -> str:
				n_spaces = max(0, limit-len(s))
				return s + (' ' * n_spaces)

			for label in labels:
				im.text_colored(right_pad(label,5), 0.2, 0.8, 1)
				im.same_line()
				im.text(str(signals[label]))
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




	
	# signal plot 1
	signal_plot_window(state.plots[PLOT_1_ID], state.data.signals,
					   ui_settings=ui['settings'], emit=_emit)

	# filter box
	filter_box_window(state.filter_boxes[FILTER_BOX_ID], state.data.signals,
					  ui_settings=ui_settings, emit=_emit)

	# signal plot 2
	signal_plot_window(state.plots[PLOT_2_ID], state.data.outputs,
					   ui_settings=ui['settings'], emit=_emit)

	# # filter box
	# filter_box_state = ui['filter_box']

	# # DEMO
	# # filter box should take the signal displayed in plot 1 as input
	# if (is_full_plot(ui['plot_1'] or is_freshly_selected_plot(ui['plot_1'])) \
	# 	and ui['plot_1']['signal_id_changed']):

	# 	set_filter_box_input_signal_id(filter_box_state, ui['plot_1']['signal_id'])

	# elif is_filter_box_connected(filter_box_state) and is_empty_plot(ui['plot_1']):
	# 	disconnect_filter_box(filter_box_state)
	# else:
	# 	filter_box_state['input_signal_id_changed'] = False
	# # END DEMO

	# filter_box(filter_box_state, data['signals'], ui_settings=ui['settings'], emit=emit)
	# update_filter_box(filter_box_state, data['signals'])




	# # signal plot 2

	# # DEMO
	# # plot 2 should display the output of filter box
	# if FILTER_BOX_OUTPUT_SIGNAL_ID in data['signals'] and is_empty_plot(ui['plot_2']):
	# 	select_plot_signal(ui['plot_2'], FILTER_BOX_OUTPUT_SIGNAL_ID)
	# elif FILTER_BOX_OUTPUT_SIGNAL_ID not in data['signals']:
	# 	set_plot_empty(ui['plot_2'])

	# # plot 2 should have the same time range as plot 1
	# if is_full_plot(ui['plot_1']) and is_full_plot(ui['plot_2']):
	# 	set_plot_time_range(ui['plot_2'], ui['plot_1']['time_range'])
		
	# # END DEMO

	# ui['plot_rect_2'] = signal_plot_window(ui['plot_2'], data['signals'], ui_settings=ui['settings'], emit=emit)
	# plot_react_to_drag(ui['plot_2'], data['signals'], ui['plot_rect_2'], ui_settings=ui['settings'])


	# debug_log_dict('ui', ui)
	debug_log_dict("first plot", state.plots[PLOT_1_ID].as_dict())

 	

# ===================================================



if __name__ == "__main__":
	run_imgui_glfw_app(app_init=sensa_app_init, draw=draw, post_frame=sensa_post_frame,
					   target_framerate=target_framerate, window_title=window_title,
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