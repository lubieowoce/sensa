"""
Main entry point of the app.
(Actually a dummy module that just launches the actual app)

It has to be a separate module to enable live reloading
of app code - `app.py` cannot reload itself.
""" 

import app
from imgui_glfw import run_reloadable_imgui_app


if __name__ == "__main__":
	run_reloadable_imgui_app(
		app_module=app,
		no_reload=('imgui_glfw', 'main', 'reload_util')
	)
