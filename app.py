from imgui_glfw_app import run_imgui_glfw_app

import imgui as im

from pyrsistent import (m , pmap,) #thaw, freeze,)#v, pvector)

from typing import (
	Any,
	# List,
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
	get_ids,
	eff_operation,
	get_signal_ids,
)

from imgui_widget import window


from plot import (
	initial_signal_plot_state, update_plot,
	# PlotState,
	PlotAction,
	signal_plot_window,
)

from filter_box import (
	initial_filter_box_state, update_filter_box,
	# FilterBoxState,
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
	state, eff_res = run_eff(initial_state, id=current_id, signal_id=current_signal_id)()
	current_id        = eff_res[ID]
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
	global PLOT_1_ID, PLOT_2_ID, FILTER_BOX_ID
	PLOT_1_ID = min(state.plots.keys())
	PLOT_2_ID = max(state.plots.keys())
	FILTER_BOX_ID = min(state.filter_boxes.keys())
	# End Demo


	ui = {
		'settings': {
			'plot_window_movable': False,
			'numpy_resample': True,
			'filter_slider_power': 3.0,
		}
	}

	


def draw_and_log_actions() -> IO_[None]:
	global frame_actions

	_, eff_res = run_eff(  draw,   actions=[])()

	frame_actions = eff_res[ACTIONS]
	# since this will be called by run_glfw_app,
	# writing to frame_actions is the only way to communicate
	# with the rest of our code




def update_state_with_frame_actions_and_run_effects() -> IO_[None]:
	global state
	global frame_actions
	global current_signal_id

	for act in frame_actions:
		# note: `frame_actions` might be modified if `update` emits an action

		state, eff_res = run_eff(update, actions=[], effects=[])(state, act)

		frame_actions.extend(eff_res[ACTIONS]) # so we can process actions emitted during updating, if any

		for command in eff_res[EFFECTS]:
			state, eff_res = run_eff(handle, signal_id=current_signal_id)(state, command)
			current_signal_id = eff_res[SIGNAL_ID]

	debug_log_dict('state', state)
	debug_log_dict('state.data', state.data)

def sensa_post_frame():
	global state
	global frame_actions

	update_state_with_frame_actions_and_run_effects()
	frame_actions.clear()

	if flags.DEBUG:
		debug_post_frame()
		debug_window()




# ==============================================




AppState = PMap_[str, Any]

@effectful(ID, SIGNAL_ID)
def initial_state() -> Eff(ID, SIGNAL_ID)[AppState]:
	n_filter_boxes = 1

	filter_boxes = pmap({id: initial_filter_box_state(id)
					  	 for id in get_ids(n_filter_boxes)})

	output_ids = pmap({id: sig_id
					   for (id, sig_id) in zip(filter_boxes.keys(),
					  						   get_signal_ids(n_filter_boxes)) })
	output_signal_names = pmap({sig_id: 'filter_{id}_output'.format(id=id) 
								for (id, sig_id) in output_ids.items()})

	data = m(
		signals = m(),       # type: PMap_[SignalId, Signal]
		signal_names = m(),   # type: PMap_[SignalId, str]

		output_ids = output_ids, # type: PMap_[Id, SignalId]
		output_signal_names = output_signal_names, # type: PMap_[SignalId, str]
		output_signals = m() # type: PMap_[SignalId, Signal] 


		# outputs = pmap({str(id): None for id in filter_boxes.keys()})
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
	emit = eff_operation('emit'); emit_effect = eff_operation('emit_effect')

	new_state = None

	if type(action) == PlotAction:
		# state_e['plots'][target_id] = update_plot(plot_state, state_e['data'], __plot_draw_area__, action)

		target_id = action.id_

		plots = state['plots']
		old_plot_state = plots[target_id]

		# Demo
		signal_data = state.data.output_signals if action.id_ == PLOT_2_ID else state.data.signals
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

	elif type(action) == FilterBoxAction and action.is_UnsetFilter():
		emit( PlotAction.SetEmpty(id_=PLOT_2_ID) )
		
	if (new_state != None
		and state.plots[PLOT_2_ID].is_Empty()
		and is_filter_box_full(state.filter_boxes[FILTER_BOX_ID])
		and state.data.output_ids[FILTER_BOX_ID] in state.data.output_signals
		and state.data.output_signals[state.data.output_ids[FILTER_BOX_ID]] != None
	   ):
			emit(
				PlotAction.SelectSignal(
					id_=PLOT_2_ID,
					signal_id=state.data.output_ids[FILTER_BOX_ID])
			)
	# End Demo





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
						) \
		
			

	elif type(command) == FilterBoxEffect:
		filter_box_id = command.id_
		filter_box_state = state.filter_boxes[filter_box_id]

		o_output = handle_filter_box_effect(filter_box_state, state.data.signals, command)

		# Demo
		output_id = state.data.output_ids[filter_box_id]

		data    = state['data']
		output_signals = data['output_signals']
		return \
			state\
			.set('data', data.set('output_signals', output_signals.set(output_id, o_output) ))
		# End Demo

		# data    = state['data']
		# outputs = data['outputs']
		# return state.set('data', data.set('outputs', outputs.set(filter_box_id, o_output) ))

	else:
		return state


# =======================================================



@effectful(ACTIONS)
def draw() -> Eff(ACTIONS)[None]:
	emit = eff_operation('emit')

	global state


	im.show_metrics_window()

	# ------------------------

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


	# state.data:
		# signals = m(),       # type: PMap_[SignalId, Signal]
		# signal_names = m(),   # type: PMap_[SignalId, str]

		# output_ids = output_ids, # type: PMap_[Id, SignalId]
		# output_signal_names = output_signal_names,
		# output_signals = m() # type: PMap_[SignalId, Signal] 


	
	# signal plot 1
	signal_plot_window(state.plots[PLOT_1_ID],
						state.data.signals, state.data.signal_names,
						ui_settings=ui['settings'])

	# filter box
	filter_box_window(state.filter_boxes[FILTER_BOX_ID],
						state.data.signals, state.data.signal_names,
					  	ui_settings=ui_settings)

	# signal plot 2
	signal_plot_window(state.plots[PLOT_2_ID],
						state.data.output_signals, state.data.output_signal_names,
						ui_settings=ui['settings'])



	# debug_log_dict('ui', ui)
	debug_log_dict("first plot", state.plots[PLOT_1_ID].as_dict())

 	

# ===================================================



if __name__ == "__main__":
	run_imgui_glfw_app(app_init=sensa_app_init, draw=draw_and_log_actions, post_frame=sensa_post_frame,
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