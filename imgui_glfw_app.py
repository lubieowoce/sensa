import glfw
import OpenGL.GL as gl

from sys import exit
from time import sleep

import imgui
from imgui.integrations.glfw import GlfwRenderer


DEFAULT_WINDOW_TITLE = "ImGui/GLFW3 app"
# DEFAULT_PAUSE_ON_NO_INPUT = True
DEFAULT_WINDOW_SIZE = (1280, 720)
DEFAULT_TARGET_FRAMERATE = 30.
def DEFAULT_DRAW():
	imgui.text("Hello, imgui!")






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




