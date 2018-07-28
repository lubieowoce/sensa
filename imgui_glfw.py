"""
This module contains procedures that take
some callbacks (init, draw, update_after_drawing)
and actually creates a window and runs a render loop.
"""

import glfw
import OpenGL.GL as gl

from sys import exit
from time import sleep
# import importlib
import reload_util as rlu

import imgui
from imgui.integrations.glfw import GlfwRenderer


DEFAULT_WINDOW_TITLE = "ImGui+GLFW3 app"
# DEFAULT_PAUSE_ON_NO_INPUT = True
DEFAULT_WINDOW_SIZE = (1280, 720)
DEFAULT_TARGET_FRAMERATE = 30.

def DEFAULT_DRAW():
	imgui.text("Hello, imgui!")






def run_reloadable_imgui_app(app_module, no_reload=()):

	no_reload = no_reload + (__name__,)
	settings = getattr(app_module, '__settings__', {})

	window_title        = settings.get('window_title',         DEFAULT_WINDOW_TITLE)
	initial_window_size = settings.get('initital_window_size', DEFAULT_WINDOW_SIZE)
	target_framerate    = settings.get('target_framerate',     DEFAULT_TARGET_FRAMERATE)
	num_active_frames_after_input = 2*target_framerate # arbitrary

	window = impl_glfw_init(window_title=window_title, window_size=initial_window_size)
	renderer = GlfwRenderer(window)
	io = imgui.get_io()

	max_frame_dur = 1/target_framerate

	frame_start = 0.
	frame_end = 0.
	frame_dur = 0.
	wait_dur = 0.

	prev_mouse_pos = (0, 0)
	mouse_pos = (0, 0)
	prev_mouse_down_0 = False
	prev_frame_click_0_finished = False

	frames_since_last_input = 0

	# TODO:
	def got_input() -> bool:
		"""
		Checks if the user sent any left-mouse mouse inputs, like moving/clicking the mouse
		"""
		nonlocal mouse_pos
		nonlocal prev_mouse_pos
		nonlocal prev_mouse_down_0
		nonlocal prev_frame_click_0_finished

		mouse_pos = io.mouse_pos
		mouse_moved = (mouse_pos != prev_mouse_pos)
		mouse_changed = io.mouse_down[0] != prev_mouse_down_0
		click_0_finished = prev_mouse_down_0 and (not io.mouse_down[0]) # mouse was down previous frame, now it's up
		# key_clicked = any(io.keys_down)
		result =  mouse_moved or mouse_changed or io.mouse_down[0] or prev_frame_click_0_finished # or key_clicked

		prev_mouse_pos = mouse_pos
		prev_mouse_down_0 = io.mouse_down[0]
		prev_frame_click_0_finished = click_0_finished
		return result


	m_request = None
	setattr(app_module, '__was_reloaded__', False)
	# reload loop
	while True: 
		# This isn't the render loop yet.
		# This one is to enable reloading,
		# in which case we need to run init
		# and start the render loop again.


		# ========================
		if hasattr(app_module, '__app_init__'):
			app_module.__app_init__()
		# ========================

		# render loop
		while True:

			frame_start = glfw.get_time() # seconds
			# debug_log("frame_start_ms", frame_start*1000) # miliseconds

			glfw.poll_events()
			renderer.process_inputs()

			if got_input():
				frames_since_last_input = 0
			else:
				frames_since_last_input += 1

			if frames_since_last_input <= num_active_frames_after_input:

				imgui.new_frame()

				# =========================
				if hasattr(app_module, '__pre_frame__'): # TODO: should this run before imgui.new_frame(?)
					app_module.__pre_frame__()

				app_module.__draw__()

				if hasattr(app_module, '__post_frame__'): # TODO: should this run before imgui.end_frame(?)
					m_request = app_module.__post_frame__()
					# the app's request is processed at the end of the loop
				# =========================


				gl.glClearColor(1., 1., 1., 1)
				gl.glClear(gl.GL_COLOR_BUFFER_BIT)

				imgui.render()
				glfw.swap_buffers(window)

			frame_end = glfw.get_time() # seconds
			frame_dur = frame_end - frame_start
			wait_dur = max_frame_dur - frame_dur
			if wait_dur > 0:
				sleep(wait_dur)

			if m_request in ('reload', 'shutdown') or glfw.window_should_close(window):
				break # stop the render loop

		# end render loop


		# if control flow got to this point, it means that 
		# the render loop finished. possible reasons:
		#	- the app requested a reload
		#	- the app requested a shutdown
		#	- glfw.window_should_close(window) is true

		if glfw.window_should_close(window) or m_request == 'shutdown':
			break # end the reload loop, run user shutdown, close
		elif m_request == 'reload':
			rlu.recursive_reload(app_module, dir=rlu.module_dirpath(app_module), excluded=no_reload)
			setattr(app_module, '__was_reloaded__', True)
			continue

	# end reload loop

	# =========================
	if hasattr(app_module, '__app_shutdown__'):
		app_module.__app_shutdown__()
	# =========================

	renderer.shutdown()
	imgui.shutdown()
	glfw.terminate()







def run_imgui_glfw_app(app_init=None,
					   pre_frame=None,
					   draw=DEFAULT_DRAW,
					   post_frame=None,
					   app_shutdown=None,
					   # should_update,
					   window_title: str = DEFAULT_WINDOW_TITLE,
					   window_size=DEFAULT_WINDOW_SIZE,
					   # pause_on_no_input: bool = DEFAULT_PAUSE_ON_NO_INPUT,
					   target_framerate: float = DEFAULT_TARGET_FRAMERATE) -> None:


	user_app_init = app_init
	user_pre_frame = pre_frame
	user_post_frame = post_frame
	user_app_shutdown = app_shutdown

	window = impl_glfw_init(window_title=window_title, window_size=window_size)
	renderer = GlfwRenderer(window)
	io = imgui.get_io()

	max_frame_dur = 1/target_framerate

	frame_start = 0.
	frame_end = 0.
	frame_dur = 0.
	wait_dur = 0.

	prev_mouse_pos = (0, 0)
	mouse_pos = (0, 0)
	prev_mouse_down_0 = False
	prev_frame_click_0_finished = False

	def got_input() -> bool:
		"""
		Checks if the user sent any left-mouse mouse inputs, like moving/clicking the mouse
		"""
		nonlocal mouse_pos
		nonlocal prev_mouse_pos
		nonlocal prev_mouse_down_0
		nonlocal prev_frame_click_0_finished

		mouse_pos = io.mouse_pos
		mouse_moved = (mouse_pos != prev_mouse_pos)
		mouse_changed = io.mouse_down[0] != prev_mouse_down_0
		click_0_finished = prev_mouse_down_0 and (not io.mouse_down[0]) # mouse was down previous frame, now it's up
		# key_clicked = any(io.keys_down)
		result =  mouse_moved or mouse_changed or io.mouse_down[0] or prev_frame_click_0_finished # or key_clicked

		prev_mouse_pos = mouse_pos
		prev_mouse_down_0 = io.mouse_down[0]
		prev_frame_click_0_finished = click_0_finished
		return result

	# ========================
	if user_app_init != None:
		user_app_init()
	# ========================

	while not glfw.window_should_close(window):

		frame_start = glfw.get_time() # seconds
		# debug_log("frame_start_ms", frame_start*1000) # miliseconds

		glfw.poll_events()
		renderer.process_inputs()

		got_inp = got_input()
		if got_inp:

			imgui.new_frame()
			

			# =========================
			if user_pre_frame != None: # TODO: should this run before imgui.new_frame(?)
				user_pre_frame()

			draw() 

			if user_post_frame != None: # TODO: should this run before imgui.end_frame(?)
				user_post_frame()
			# =========================


			gl.glClearColor(1., 1., 1., 1)
			gl.glClear(gl.GL_COLOR_BUFFER_BIT)

			imgui.render()

			glfw.swap_buffers(window)



		

		frame_end = glfw.get_time() # seconds
		frame_dur = frame_end - frame_start
		wait_dur = max_frame_dur - frame_dur
		if wait_dur > 0:
			sleep(wait_dur)

	# =========================
	if user_app_shutdown != None:
		user_app_shutdown()
	# =========================

	renderer.shutdown()
	imgui.shutdown()
	glfw.terminate()






def impl_glfw_init(window_title, window_size):
	width, height = window_size

	if not glfw.init():
		print("Could not initialize OpenGL context")
		exit(1)

	# OS X supports only forward-compatible core profiles from 3.2
	glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
	glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
	glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

	glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

	# Create a windowed mode window and its OpenGL context
	window = glfw.create_window(
		int(width), int(height), window_title, None, None
	)
	glfw.make_context_current(window)

	if not window:
		glfw.terminate()
		print("Could not initialize Window")
		exit(1)

	return window




