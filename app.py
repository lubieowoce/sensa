"""
This module doesn't run anything.
It only declares procedures (callbacks) and settings which
`main.py` will pass to `imgui_glfw.run_reloadable_imgui_app()`,
in particular:
	__app_init__
	__draw__
	__post_frame__
	__settings__

Because `run_reloadable_imgui_app` takes
this whole module as an argument (to enable reloading)
and then picks out the values it needs, the above 
procedures/values have underscored names to follow
python's `__implements_a_protocol__` convention.

(the names are actually aliases - for example
 `__post_frame__` is just an alias to `sensa_post_frame`.
 See the bottom of the file.)
"""

import imgui as im

from pyrsistent import (m , pmap,) #thaw, freeze,)#v, pvector)
from collections import deque
from sumtype import sumtype
import pickle
# import numpy as np

from typing import (
	Any,
	NamedTuple, Optional, Union, Tuple
)

from utils.types import (
	PMap_,
	Action, Effect,
	IO_,
)

from eff import (
	Eff, run_eff,
	effectful,
	ID, EFFECTS, SIGNAL_ID, ACTIONS,

	emit, emit_effect,
	get_ids, get_signal_ids,
)

import utils as util

from components.grouped import window, child, only_draw_if
from components.styled import color
from components.str_combo import str_combo
from components.double_click_listbox import double_click_listbox
# from double_click_selectable import double_click_selectable
# from components.draggable import draggable

import persist

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

from debug_util import (
	debug_initialize,
	debug_window,
	debug_log, debug_log_dict, debug_log_crash,
	debug_post_frame,
)

import flags



INITIAL_ACTIONS = [FileAction.Load(filename=example_file_path)]

STATE_SAVEFILE_NAME               = 'sensa_state.pickle'
USER_ACTION_HISTORY_SAVEFILE_NAME = 'sensa_actions_history.pickle'


current_id = None
current_signal_id = None
state = None
ui = None

frame_actions = None
user_action_history = None


def sensa_app_init():
	global __was_reloaded__

	app_state_init()

	if __was_reloaded__:
		for cmd in (AppStateEffect.LoadUserActionHistory, AppStateEffect.RunHistory):
			handle_app_state_effect(cmd)
		__was_reloaded__ = False


def app_state_init():
	global current_id
	global current_signal_id
	global state
	global user_action_history
	global ui

	if flags.DEBUG:
		debug_initialize()


	current_id = 0
	current_signal_id = 0
	
	# create the initial state	
	state, eff_res = run_eff(initial_state(), id=current_id, actions=[])
	current_id        = eff_res[ID]
	for action in eff_res[ACTIONS]:
		state, eff_res = run_eff(update(state, action), actions=[], effects=[])

		# so we can process actions emitted during updating, if any
		eff_res[ACTIONS].extend(eff_res[ACTIONS]) 

		for command in eff_res[EFFECTS]:
			state, eff_res = run_eff(handle(state, command), signal_id=current_signal_id)
			current_signal_id = eff_res[SIGNAL_ID]

	assert state != None

	# run the initial actions
	for act in INITIAL_ACTIONS:

		state, eff_res = run_eff(update(state, act), actions=[], effects=[])

		# so we can process actions emitted during updating, if any
		INITIAL_ACTIONS.extend(eff_res[ACTIONS])

		for command in eff_res[EFFECTS]:
			state, eff_res = run_eff(handle(state, command), signal_id=current_signal_id)
			current_signal_id = eff_res[SIGNAL_ID]


	assert state != None


	user_action_history = deque()
	# TODO: ^ Maybe this shouldn't be here? action history is sort of meta,
	# 		not exactly app state. This would follow the responsibility scope
	#		of `update_state_with_actions_and_run_effects` - user action history
	# 		is managed separately, by `handle_app_state_effects` (which maybe should be renamed...)

	ui = {
		'settings': {
			'plot_window_movable': True,
			'plot_resample_function': 'numpy_interp',
			# 'plot_draw_function': 'imgui',
			'plot_draw_function': 'manual',

			'filter_slider_power': 3.0,
		},
	}



	


def draw_and_log_actions() -> IO_[None]:
	global frame_actions

	_, eff_res = run_eff(  draw(),   actions=[])

	frame_actions = eff_res[ACTIONS]
	# since this will be called by run_glfw_app,
	# writing to frame_actions is the only way to communicate
	# with the rest of our code



def sensa_post_frame() -> IO_[Optional[str]]:
	global state
	global frame_actions
	global current_id
	global current_signal_id
	global user_action_history

	msg_to_render_loop = None

	user_action_history.extend(frame_actions)
	msg = update_state_with_actions_and_run_effects(frame_actions)
	frame_actions.clear()

	if msg.is_Success():
		pass

	elif msg.is_Crash():
		debug_log_crash(origin=msg.origin, cause=msg.cause, exception=msg.exception)

	elif msg.is_DoApp():	
		handle_app_state_effect(msg.command)

	elif msg.is_DoAppRunner():
		command = msg.command
		if command.is_Reload():
			# preserve history across reloads
			handle_app_state_effect(AppStateEffect.SaveUserActionHistory) 
			msg_to_render_loop = 'reload'
		elif command.is_Exit():
			msg_to_render_loop = 'shutdown'
		else: command.impossible()

	else: msg.impossible()


	# TODO: Not sure if this should be here...
	#		post_frame shouldn't draw windows.
	#		Either rename it or move the debug code.
	if flags.DEBUG:
		debug_log('n logged actions:', len(user_action_history))
		debug_log_dict('state (no signals)', state.set('data', state.data.remove('signals')) )
		debug_post_frame()
		debug_window()

	return msg_to_render_loop



def update_state_with_actions_and_run_effects(user_actions) -> IO_['AppControl']:
	global state
	global current_id
	global current_signal_id

	actions_to_process = user_actions[:]

	prev_frame_state = state

	# if actions_to_process: print('running actions:', flush=True)
	for action in actions_to_process:
		# print("\t{}".format(action), flush=True)
		try:
			state, eff_res = run_eff(update(state, action), actions=[], effects=[])
		except Exception as ex:
			state = prev_frame_state
			return AppControl.Crash(origin='update', cause=action, exception=ex)

		# so we can process actions emitted during updating, if any
		actions_to_process.extend(eff_res[ACTIONS])

		debug_log('effects', eff_res[EFFECTS])
		for command in eff_res[EFFECTS]:

			if type(command) == AppStateEffect:
				return AppControl.DoApp(command=command)
			elif type(command) == AppRunnerEffect:
				return AppControl.DoAppRunner(command=command)
			# ^ These effects affect the whole app, and can
			# manage the action history, action saving, loading,
			# app reloading, etc. This function only handles
			# updates to actual app state, so it "passes the effects
			# higher up" to be handled elswhere.

			try:
				state, eff_res = run_eff(handle(state, command), signal_id=current_signal_id)
			except Exception as ex:
				state = prev_frame_state
				return AppControl.Crash(origin='handle', cause=command, exception=ex)
			
			current_signal_id = eff_res[SIGNAL_ID]

	# if actions_to_process: print(flush=True)
	return AppControl.Success()






# ==============================================


AppState = PMap_[str, Any]

@effectful
async def initial_state() -> Eff[[ID, ACTIONS], AppState]:

	# # python 3.6
	# n_source_boxes = 1
	# source_boxes = pmap({
	# 	box.id_: box
	# 	for box in (await initial_source_state() for _ in range(n_source_boxes))
	# })

	# filter_boxes = pmap({
	# 	box.id_: box
	# 	for box in (await initial_filter_box_state(filter_id=filter_id)
	#   			for filter_id in available_filters.keys())
	# })

	# n_plots = 2
	# plots = pmap({
	# 	plot.id_: plot
	# 	for plot in (await initial_plot_box_state() for _ in range(n_plots))
	# })


	n_source_boxes = 1
	_source_boxes = {}
	for _ in range(n_source_boxes):
		box = await initial_source_state()
		_source_boxes[box.id_] = box
	source_boxes = pmap(_source_boxes)


	_filter_boxes = {}
	for filter_id in available_filters.keys(): 
		box = await initial_filter_box_state(filter_id=filter_id)
		_filter_boxes[box.id_] = box
	filter_boxes = pmap(_filter_boxes)


	n_plots = 2
	_plots = {}
	for _ in range(n_plots):
		plot = await initial_plot_box_state()
		_plots[plot.id_] = plot
	plots = pmap(_plots)


	for boxes in (source_boxes, filter_boxes, plots):
		for (id_, box) in boxes.items():
			await emit(ng.GraphAction.AddNode(id_, box.to_node()))

	return m(
		data = m(
			signals = m(),      # type: PMap_[SignalId, Signal]
			signal_names = m(), # type: PMap_[SignalId, str]
			box_outputs = m()    # type: PMap_[Id, Maybe[Signal]] 
	    ),
	    
		graph = ng.Graph.empty,
	    link_selection = LinkSelection.empty,
		source_boxes = source_boxes,
		plots		 = plots,
		filter_boxes = filter_boxes,

		n_actions=0
	)

# --------------------



@effectful
async def update(state: AppState, action: Action) -> Eff[[ACTIONS, EFFECTS], AppState]:

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
				await emit( ng.GraphAction.Disconnect(*link) )
			elif can_create_link:
				await emit( ng.GraphAction.Connect(*link) )
			else: 
				# link is invalid - e.g. connects to a filled slot
				# but we empty it after anyway, so do nothing
				pass
			
			link_selection = LinkSelection.empty

		new_state = state.set('link_selection', link_selection)

	elif type(action) == ng.GraphAction:
		graph = state.graph
		new_state = state.set('graph', await ng.update_graph(graph, action))

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
		new_filter_box_state = update_filter_box(old_filter_box_state, action)
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
		# new_plot_state = await update_plot_box(old_plot_state, signal_data, action)

		if not (old_plot_state is new_plot_state): # reference comparison for speed
			new_state = state.set('plots', plots.set(target_id, new_plot_state))
			# o_changed_box = target_id


	elif type(action) == FileAction:
		if action.is_Load():
			await emit_effect( FileEffect.Load(action.filename) )

	elif type(action) == AppStateAction:
		await emit_effect(
			{
				AppStateAction.ResetState:  AppStateEffect.ResetState,
			 	AppStateAction.SaveState:   AppStateEffect.SaveState,
				AppStateAction.LoadState:   AppStateEffect.LoadState,
				AppStateAction.ResetUserActionHistory: AppStateEffect.ResetUserActionHistory,
				AppStateAction.SaveUserActionHistory:  AppStateEffect.SaveUserActionHistory,
				AppStateAction.LoadUserActionHistory:  AppStateEffect.LoadUserActionHistory,
				AppStateAction.RunHistory: AppStateEffect.RunHistory,
			}[action]
		)
	elif type(action) == AppRunnerAction:
		await emit_effect(
			{
				AppRunnerAction.Reload(): AppRunnerEffect.Reload(),
			 	AppRunnerAction.Exit():   AppRunnerEffect.Exit(),
			}[action]
		)

	else: util.impossible('Unknown action of type {}:  {}'.format(type(action), action))


	if o_changed_box != None:
		# await emit(ng.NodeChanged(id_=o_changed_box))
		await emit_effect(ng.GraphEffect.EvalGraph())

	return (new_state if new_state is not None else state) \
			.transform(['n_actions'], lambda x: x+1)	




# ------------------------



@effectful
async def handle(state: AppState, command) -> Eff[[SIGNAL_ID], IO_[AppState]]:
	global current_id, current_signal_id  # used for state saving/loading

	if type(command) == FileEffect:

		new_signals, new_signal_names = \
			await handle_file_effect(
				state.data.signals,
				state.data.signal_names,
				command
			)

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

	# AppStateEffects are processed with `handle_app_state_effect`

	else: util.impossible('Unknown command of type {}:  {}'.format(type(command), command))
		


# Actions to influence the app state
# in ways that can be done from within
# this module. In particular, this module
# cannot directly terminate or reload itself -
# the render loop in `reloadable_imgui_app`
# has to handle those.

class AppStateAction(sumtype, constants=True):
	ResetState = ...
	SaveState = ...
	LoadState = ...
	ResetUserActionHistory = ...
	SaveUserActionHistory = ...
	LoadUserActionHistory = ...
	RunHistory = ...


class AppStateEffect(sumtype, constants=True):
	ResetState = ...
	SaveState = ...
	LoadState = ...
	ResetUserActionHistory = ...
	SaveUserActionHistory = ...
	LoadUserActionHistory = ...
	RunHistory = ...

# Actions that only the loop that actually
# runs the function can handle

class AppRunnerAction(sumtype):
	def Reload(): ...
	def Exit(): ...

class AppRunnerEffect(sumtype):
	def Reload(): ...
	def Exit(): ...


class AppControl(sumtype): 
	def Success(): ...
	def Crash(cause: Any, origin: str, exception: Exception): ...
	def DoApp(command: AppStateEffect): ...
	def DoAppRunner(command: AppRunnerEffect): ...



def handle_app_state_effect(command) -> IO_[None]:
	global state
	global current_id
	global current_signal_id
	global user_action_history
	
	if command.is_ResetState():
		app_state_init()

	elif command.is_SaveState():
		with open(STATE_SAVEFILE_NAME, mode='wb') as savefile:
			pickle.dump((state, current_id, current_signal_id), file=savefile)

	elif command.is_LoadState():
		with open(STATE_SAVEFILE_NAME, mode='rb') as savefile:
			state, current_id, current_signal_id = pickle.load(file=savefile)

	elif command.is_ResetUserActionHistory():
		user_action_history.clear()

	elif command.is_SaveUserActionHistory():
		with open(USER_ACTION_HISTORY_SAVEFILE_NAME, mode='wb') as savefile:
			persist.dump_all(user_action_history, file=savefile)

	elif command.is_LoadUserActionHistory():
		with open(USER_ACTION_HISTORY_SAVEFILE_NAME, mode='rb') as savefile:
			user_action_history = deque(persist.load_all(file=savefile))

	elif command.is_RunHistory():
		# restart everything
		actions_to_apply = [action for action in user_action_history
									if type(action) not in (AppStateAction, AppRunnerAction)]
		_ = update_state_with_actions_and_run_effects(actions_to_apply)
		# TODO: ^ it might be useful to distinguish internal effects and
		# external (IO) effects, ie file access. Rerunning internal effects
		# is safe, but running an IO effect twice might give different results

	else: command.impossible()




# =======================================================

LinkSelection = NamedTuple('LinkSelection', [
							('src_slot', Optional[ng.OutputSlotId]),
							('dst_slot', Optional[ng.InputSlotId]) ])
LinkSelection.empty = LinkSelection(src_slot=None, dst_slot=None)

class LinkSelectionAction(sumtype):
	def ClickOutput(slot: ng.OutputSlotId): ...
	def ClickInput (slot: ng.InputSlotId): ...
	def Clear(): ...



def update_link_selection(
		state: LinkSelection,
		graph,
		action: LinkSelectionAction
	) -> LinkSelection:

	if action.is_ClickOutput():
		return (LinkSelection.empty  if state.src_slot != None else
				state._replace(src_slot=action.slot) )

	if action.is_ClickInput():
		return (LinkSelection.empty  if state.dst_slot != None else
				state._replace(dst_slot=action.slot) )

	elif action.is_Clear(): return LinkSelection.empty
	else: action.impossible()

# ----------------------------------------------------------

@effectful
async def draw() -> Eff[[ACTIONS], None]:

	global state

	im.show_metrics_window()
	im.show_test_window()



	# ------------------------
	# t_flags = 0
	# t_flags = (
	# 	  im.WINDOW_NO_TITLE_BAR
	# 	| im.WINDOW_NO_MOVE
	# 	| im.WINDOW_NO_RESIZE
	# 	| im.WINDOW_NO_COLLAPSE
	# 	| im.WINDOW_NO_FOCUS_ON_APPEARING
	# 	| im.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
	# )
	# with window(name="test", flags=t_flags):
	# 	im.button("bloop")
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
	debug_log("test_drew", False)
	with window("test") as (expanded, _):
		only_draw_if(expanded)

		debug_log("test_drew", True) # only_draw_if didn't abort, overwrite 
		US = ui['settings']

		opts = ['first', 'second', 'third']
		default_state = ('no_selection', None)

		US.setdefault('selectable_state', default_state)
		US.setdefault('selectable_added', [])
		if not im.is_window_focused():
			US['selectable_state'] = default_state

		changed, selection_changed, selectable_state = double_click_listbox(US['selectable_state'], opts)
		if changed:
			US['selectable_state'] = selectable_state

		o_ix = selectable_state[1]
		im.text_colored(
			"[ {!s:<10} ] {}".format(
							opts[o_ix] if o_ix is not None else "---",
							"(!)" if selection_changed else ""
			 ),
			*(0.3, 0.8, 0.5)
		)
		im.text("")
		im.text("{!r:<5} {!r:<5} {}".format(changed, selection_changed, selectable_state) )

		if selectable_state[0] == 'double_clicked':
			US['selectable_added'].append(  opts[ selectable_state[1] ]  )
		im.text(str(US['selectable_added']))


		c  = im.is_mouse_clicked()
		dc = im.is_mouse_double_clicked()
		im.text( "{!r:<5} {!r:<5} {!r:<5}".format(c, dc, c and dc) )
		im.text("focused: "+ repr(im.is_window_focused()))





	with window(name="signals"):
		if im.button("load example"):
			await emit( FileAction.Load(filename=example_file_path) )


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
	# with window(name="modules"):
	# 	modules = sorted(
	#		rlu.all_modules(dir=pathlib.Path.cwd()),
	#		key=lambda mod: (getattr(mod, '__reload_incarnation__', -1), mod.__name__)
	#	)
	# 	for mod in modules:
	# 		incarnation_text = str(getattr(mod, '__reload_incarnation__', '-'))
	# 		im.text("{mod}[{inc}]".format(mod=mod.__name__, inc=incarnation_text))


	with window(name="settings"):
		ui_settings = ui['settings']
		changed, move = im.checkbox("move plots", ui_settings['plot_window_movable'])
		if changed:
			ui_settings['plot_window_movable'] = move

		# im.same_line()
		changed, option = str_combo(
							"resample", ui_settings['plot_resample_function'],
							['numpy_interp',
							 'scipy_zoom',
							 'crude_downsample']
						  )
		if changed:
			ui_settings['plot_resample_function'] = option

		# im.same_line()
		changed, option = str_combo(
							"plots", ui_settings['plot_draw_function'],
							['imgui',
							 'manual']
						  )
		if changed:
			ui_settings['plot_draw_function'] = option


		changed, val = im.slider_float('filter_slider_power', ui_settings['filter_slider_power'],
									   min_value=1., max_value=5.,
									   power=1.0)
		if changed:
			ui_settings['filter_slider_power'] = val

		if im.button("reload"):
			await emit(AppRunnerAction.Reload())

		# im.same_line()
		# im.button("bla bla bla")

		# im.same_line()
		# im.button("ple ple ple")

		im.text("state | ")

		im.same_line()
		if im.button("dump##state"):
			await emit(AppStateAction.SaveState)

		im.same_line()
		if im.button("load##state"):
			await emit(AppStateAction.LoadState)

		im.same_line()
		if im.button("reset##state"):
			await emit(AppStateAction.ResetState
)


		im.text("history | ")

		im.same_line()
		if im.button("dump##history"):
			await emit(AppStateAction.SaveUserActionHistory)

		im.same_line()
		if im.button("load##history"):
			await emit(AppStateAction.LoadUserActionHistory)

		im.same_line()
		if im.button("reset##history"):
			await emit(AppStateAction.ResetUserActionHistory)

		im.same_line()
		if im.button("run##history"):
			await emit(AppStateAction.RunHistory)




	# TODO: Window positions can theoretically be accessed
	# after being drawn using internal APIs.
	# See:
	#	imgui_internal.h > ImGuiWindow (search "struct IMGUI_API ImGuiWindow")
	#	imgui.cpp        > ImGui::GetCurrentContext()
	#
	# (sort-of pseudocode example)
	#
	# foo_id = None
	#
	# with window("foo"):
	# 	foo_id = GetCurrentWindow().ID
	# 	...
	#
	# ...
	#
	# with window("accessing other windows"):
	# 	windows = imgui.GetCurrentContext().Windows
	# 	foo_win = windows[ windows.find(lambda win: win.ID = foo_id) ]
	# 	im.text( "pos:{}, size:{}".format(foo_win.Pos, foo_win.Size) )


	# ----------------------------
	# await ng.graph_window(state.graph)


	prev_color_window_background = im.get_style().color(im.COLOR_WINDOW_BACKGROUND)

	im.set_next_window_position(0, 100)
	with color({im.COLOR_WINDOW_BACKGROUND: (0., 0., 0., 0.05)}), \
		 window(name="nodes", 
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


		with color({im.COLOR_WINDOW_BACKGROUND: prev_color_window_background}):

			# source boxes
			for (id_, box_state) in state.source_boxes.items():
				pos = await signal_source_window(
							box_state,
							state.data.signals,
							state.data.signal_names
					  )
				box_positions[id_] = pos


			# filter boxes
			for (id_, box_state) in state.filter_boxes.items():
				pos = await filter_box_window(
							box_state,
							ui_settings=ui_settings
					  )
				box_positions[id_] = pos
			


			# signal plot 1
			for (id_, box_state) in state.plots.items():
				pos = await signal_plot_window(box_state,
									inputs[id_],
									ui_settings=ui_settings)
				box_positions[id_] = pos
			


		# connections between boxes
		link_selection = state.link_selection

		prev_cursor_screen_pos = im.get_cursor_screen_position()

		# get slot coords and draw slots
		with color({im.COLOR_CHECK_MARK: (0, 0, 0, 100/255)}):
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
						await emit(LinkSelectionAction.ClickInput(slot))

					center_pos = util.rect_center(util.get_item_rect()) # bounding rect of prev widget
					slot_center_positions[('in', id_, slot_ix)] = center_pos

				for slot_ix in range(node.n_outputs):
					pos = im.Vec2(right_x+3, top_y+30+slot_ix*SPACING)
					im.set_cursor_screen_position(pos)

					slot = ng.OutputSlotId(id_, slot_ix)
					was_selected = (slot == link_selection.src_slot)

					changed, selected = im.checkbox("##out{}{}".format(id_, slot_ix), was_selected)
					if changed:
						await emit(LinkSelectionAction.ClickOutput(slot))

					center_pos = util.rect_center(util.get_item_rect()) # bounding rect of prev widget
					slot_center_positions[('out', id_, slot_ix)] = center_pos

		# end drawing slots		




		# draw links
		for (src, dst) in state.graph.links:
			src_pos = slot_center_positions[('out', src.node_id, src.ix)]
			dst_pos = slot_center_positions[('in',  dst.node_id, dst.ix)]
			draw_list.add_line(src_pos, dst_pos, color=(0.5, 0.5, 0.5, 1.), thickness=2.)


		im.set_cursor_screen_position(prev_cursor_screen_pos)
	# end nodes window



	im.show_style_editor()


 	

# ===================================================

__was_reloaded__ = None
__app_init__   = sensa_app_init
__draw__       = draw_and_log_actions
__post_frame__ = sensa_post_frame

__settings__ = {
	'window_title': "Sensa",
	'initital_window_size': (1280, 850),
	'target_framerate': 30.,
}
