from redux_imgui_glfw_app import run_redux_imgui_glfw_app

import imgui as im

from pyrsistent import m #, pmap, v, pvector)

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


from id_eff import IdEff, id_and_effects, run_id_eff
from imgui_widget import window


from plot import (
	initial_signal_plot_state, update_signal_plot,
	signal_plot_window,
	is_empty_plot, is_full_plot, is_freshly_selected_plot,
	select_plot_signal, set_plot_time_range,
	set_plot_empty,
)

from filter_box import (
	initial_filter_box_state,
	filter_box, update_filter_box,
	FILTER_BOX_OUTPUT_SIGNAL_ID,
	# is_filter_box_disconnected,
	is_filter_box_connected,
	disconnect_filter_box, set_filter_box_input_signal_id, 
)

from files import (
	example_file_path,
	load_file, LOAD_FILE,
	load_file_eff, LOAD_FILE_EFF,
	handle_load_file
)

import flags


window_title = "Sensa"
initital_window_size = (1280, 850)
target_framerate = 30.

INITIAL_ACTIONS = [load_file(example_file_path)]




data = object()
ui = object()




def sensa_app_init():
	global data
	global ui

	if flags.DEBUG:
		debug_initialize()


	data = {'signals':{}}
	
	

	ui = {

		'plot_1': initial_signal_plot_state(),
		'plot_2': initial_signal_plot_state(),


		'filter_box': initial_filter_box_state(),


		'settings': {
			'plot_window_movable': False,
			'numpy_resample': True,
			'filter_slider_power': 3.0,
		}
	}

	
	


def sensa_post_frame():

	if flags.DEBUG:
		debug_post_frame()
		debug_window()




@id_and_effects
def sensa_get_initial_state() -> IdEff[PMap_[str, Any]]:
	return m()



@id_and_effects
def update(state: PMap_[str, Any], action: Action) -> IdEff[PMap_[str, Any]]:

	if action.type in [LOAD_FILE]:
		emit_effect( load_file_eff(action.filename) ) 
		return state
	else:
		return state




def handle(data, command):
	if command.type in [LOAD_FILE_EFF]:
		handle_load_file(data['signals'], command)



# ==============================================



def draw(state, emit):
	global data
	# state = { counters: {id: counter},
	#           counter_list: [id]       }



	im.show_metrics_window()

	# ------------------------

	with window(name="signals"):
		if im.button("load example"):
			emit(load_file(example_file_path))


		if len(data['signals']) > 0:
			labels = sorted(data['signals'].keys())


			def right_pad(s: str, limit: int) -> str:
				n_spaces = max(0, limit-len(s))
				return s + (' ' * n_spaces)

			for label in labels:
				im.text_colored(right_pad(label,5), 0.2, 0.8, 1)
				im.same_line()
				im.text(str(data['signals'][label]))
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

	# 'filter_box': {
	# 	'input_signal_id': None,
	# 	'input_signal_id_changed': True,
	# 	'trans': make_lowpass_tr,
	# 	'param_value_changed': False,
	# },




	# signal plot 1
	ui['plot_rect_1'] = signal_plot_window("view (drag to scroll)##1", ui['plot_1'], data['signals'], ui_settings=ui['settings'], emit=emit)
	update_signal_plot(ui['plot_1'], data['signals'], ui['plot_rect_1'], ui_settings=ui['settings'])



	# filter box
	filter_box_state = ui['filter_box']

	# DEMO
	# filter box should take the signal displayed in plot 1 as input
	if (is_full_plot(ui['plot_1'] or is_freshly_selected_plot(ui['plot_1'])) \
		and ui['plot_1']['signal_id_changed']):

		set_filter_box_input_signal_id(filter_box_state, ui['plot_1']['signal_id'])

	elif is_filter_box_connected(filter_box_state) and is_empty_plot(ui['plot_1']):
		disconnect_filter_box(filter_box_state)
	else:
		filter_box_state['input_signal_id_changed'] = False
	# END DEMO

	filter_box(filter_box_state, data['signals'], ui_settings=ui['settings'])
	update_filter_box(filter_box_state, data['signals'])




	# signal plot 2

	# DEMO
	# plot 2 should display the output of filter box
	if FILTER_BOX_OUTPUT_SIGNAL_ID in data['signals'] and is_empty_plot(ui['plot_2']):
		select_plot_signal(ui['plot_2'], FILTER_BOX_OUTPUT_SIGNAL_ID)
	elif FILTER_BOX_OUTPUT_SIGNAL_ID not in data['signals']:
		set_plot_empty(ui['plot_2'])

	# plot 2 should have the same time range as plot 1
	if is_full_plot(ui['plot_1']) and is_full_plot(ui['plot_2']):
		set_plot_time_range(ui['plot_2'], ui['plot_1']['time_range'])
		
	# END DEMO

	ui['plot_rect_2'] = signal_plot_window("view (drag to scroll)##2", ui['plot_2'], data['signals'], ui_settings=ui['settings'], emit=emit)
	update_signal_plot(ui['plot_2'], data['signals'], ui['plot_rect_2'], ui_settings=ui['settings'])


	debug_log_dict('ui', ui)
	# debug_log_dict("ui['plot']", ui['plot'])

 	

# ===================================================



if __name__ == "__main__":
	# run_imgui_glfw_app(app_init=sensa_app_init, draw=draw, post_frame=sensa_post_frame,
	# 				   target_framerate=target_framerate, window_title=window_title,
	# 				   window_size=initital_window_size)
	run_redux_imgui_glfw_app(update=update,
							 get_initial_state=sensa_get_initial_state,
							 initial_actions=INITIAL_ACTIONS,

							 handle=handle,
							 get_data=(lambda: data),

							 app_init=sensa_app_init,
							 draw=draw,
							 post_frame=sensa_post_frame,

					   		 window_title=window_title,
					   		 window_size=initital_window_size,
					   		 target_framerate=target_framerate)

# def run_redux_imgui_glfw_app(get_initial_state: Fun[[None], IdEff[A]],
# 							 update: Fun[[A, Action], A],
# 							 handle: Fun[[B, Effect], None],
# 							 data: IO_[B],
# 							 draw: Fun[  [Fun[[Action], IO_[None]]],  IO_[None] ] ,
# 							 initial_actions: Sequence[Action] = NoInitialActions,
# 							 post_frame=None,
# 							 app_shutdown=None,
# 							 # should_update,
# 							 window_title: str = DEFAULT_WINDOW_TITLE,
# 							 window_size=DEFAULT_WINDOW_SIZE,
# 							 # pause_on_no_input: bool = DEFAULT_PAUSE_ON_NO_INPUT,
# 							 target_framerate: float = DEFAULT_TARGET_FRAMERATE) -> None:





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