import imgui as im
from imgui_widget import window
from eff import effectful, ACTIONS, eff_operation
from utils.types import IMGui
import arrayplot as aplt


@effectful(ACTIONS)
def show_pleple_window(name, plot_info, multi_resolution_signals, plot_gl_resources, plot_gl_canvas) -> IMGui[None]:
	emit = eff_operation('emit')
	with window(name):
		window_width, window_height = im.get_content_region_available()
		window_width, window_height = int(window_width), int(window_height)

		if (window_width, window_height) != (plot_gl_canvas.width_px, plot_gl_canvas.height_px):
			print("\t### resizing canvas  {} -> {}".format((plot_gl_canvas.width_px, plot_gl_canvas.height_px), (window_width, window_height)), flush=True)
			del plot_gl_canvas
			plot_gl_canvas = aplt.init_plot_canvas(window_width, window_height)
			emit(___new_canvas_(plot_gl_canvas) )

		canvas_width  = plot_gl_canvas.width_px
		canvas_height = plot_gl_canvas.height_px

		should_redraw = True
		if should_redraw:
			aplt.draw_plot_to_canvas_multires(plot_gl_canvas, plot_info, multi_resolution_signals, plot_gl_resources, line_color=aplt.WHITE, background_color=aplt.TRANSPARENT_BLACK)

		im.image(plot_gl_canvas.texture_id, canvas_width, canvas_height, uv0=(0, 1), uv1=(1, 0))


def generate_pleple():
	o_new_mipmap_level = aplt.new_mipmap_level_if_needed(plot_gl_canvas, plot_info, multi_resolution_signals)
	if o_new_mipmap_level is not None:
		multi_resolution_signals = aplt.add_mipmap_level(o_new_mipmap_level, multi_resolution_signals)