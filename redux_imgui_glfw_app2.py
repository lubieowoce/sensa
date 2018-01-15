from typing import (
	List, Tuple, Sequence,
)
from types_util import (
	A, B, C, K,
	Action, Effect,
	Fun,
	IO_, 
)

from imgui_glfw_app import (
	run_imgui_glfw_app,
	DEFAULT_WINDOW_TITLE,
	# DEFAULT_PAUSE_ON_NO_INPUT,
	DEFAULT_WINDOW_SIZE,
	DEFAULT_TARGET_FRAMERATE,
	DEFAULT_DRAW,
)

from sensa_util import sequence

from id_eff import IdEff, run_id_eff



NoInitialActions = None

state = None
current_id = None



frame_actions = None

def actions_initialize():
	global frame_actions
	frame_actions = []

def emit(action):
	frame_actions.append(action)

def get_frame_actions() -> List[Action]:
	return frame_actions[:]

def actions_post_frame():
	frame_actions.clear()


def update_state_with_actions(update: Fun[[A, Action], A], state: A, actions, current_id) -> Tuple[A, List[Effect]]:

	all_effects = []
	for act in actions:
		state, current_id, effects = run_id_eff(update, id=current_id)(state, act)
		all_effects.extend(effects)
	return state, current_id, all_effects


def execute_effects(effects: List[Effect], handle, data) -> IO_[None]:
	for eff in effects:
		handle(data, eff)





def redux_app_initialize(get_initial_state,
						 update, handle, data,
						 initial_actions=NoInitialActions) -> IO_[None]:
	global current_id
	global state

	current_id = 0
	state, current_id, _ = run_id_eff(get_initial_state, id=current_id)()

	actions_initialize()

	# run the initial actions
	if initial_actions != NoInitialActions:
		redux_app_pre_frame()

		for action in initial_actions:
			emit(action)

		redux_app_post_frame(update, handle, data)


def redux_app_pre_frame() -> IO_[None]:
	assert len(frame_actions) == 0, "Actions buffer not cleared! Is:" + str(frame_actions) 


def redux_app_post_frame(update, handle: Fun[[B, Effect], None], get_data) -> IO_[None]:
	global state
	global current_id
	state, current_id, effects = update_state_with_actions(update, state, get_frame_actions(), current_id)
	actions_post_frame()
	execute_effects(effects, handle, get_data())





def run_redux_imgui_glfw_app(get_initial_state: Fun[[None], IdEff[A]],
							 update: Fun[[A, Action], A],

							 handle: Fun[[B, Effect], None],
							 get_data: IO_[B],

							 initial_actions: Sequence[Action] = NoInitialActions,

							 app_init: Fun[[None], IO_[None]] = None,
							 draw: Fun[  [Fun[[Action], IO_[None]]],  IO_[None] ] = DEFAULT_DRAW,
							 post_frame=None,
							 app_shutdown=None,
							 # should_update,
							 window_title: str = DEFAULT_WINDOW_TITLE,
							 window_size=DEFAULT_WINDOW_SIZE,
							 # pause_on_no_input: bool = DEFAULT_PAUSE_ON_NO_INPUT,
							 target_framerate: float = DEFAULT_TARGET_FRAMERATE) -> None:

	global state

	user_update = update
	user_handle = handle
	user_get_data = get_data
	user_app_init = app_init if app_init != None else (lambda: None)
	user_post_frame = post_frame
	user_app_shutdown = app_shutdown

	r_init = sequence(
				user_app_init,
				lambda: redux_app_initialize(get_initial_state,
											 user_update, user_handle, user_get_data,
											 initial_actions=initial_actions)
			 )
	r_pre_frame = redux_app_pre_frame
	r_draw = lambda: draw(state, emit)
	r_post_frame = sequence(
						lambda: redux_app_post_frame(user_update, user_handle, user_get_data),
						user_post_frame
				   )
	run_imgui_glfw_app(app_init=r_init,
					   pre_frame=r_pre_frame, draw=r_draw, post_frame=r_post_frame,
					   app_shutdown=user_app_shutdown,
					   window_title=window_title, window_size=window_size, target_framerate=target_framerate)
	

# def run_imgui_glfw_app(app_init=None,
# 					   pre_frame=None,
# 					   draw=DEFAULT_DRAW,
# 					   post_frame=None,
# 					   app_shutdown=None,
# 					   # should_update,
# 					   window_title: str = DEFAULT_WINDOW_TITLE,
# 					   window_size=DEFAULT_WINDOW_SIZE,
# 					   # pause_on_no_input: bool = DEFAULT_PAUSE_ON_NO_INPUT,
# 					   target_framerate: float = DEFAULT_TARGET_FRAMERATE) -> None:

