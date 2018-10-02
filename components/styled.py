from utils.types import IMGui
import imgui

__all__ = [
	'color',
	'style',
]


class _IMColorCtx:
	def __init__(imc, colors):
		imc.colors = colors

	def __enter__(imc) -> IMGui[None]:
		for (col_var, color) in imc.colors.items():
			imgui.push_style_color(col_var, *color)

	def __exit__(imc, *args) -> IMGui[None]:
		imgui.pop_style_color(len(imc.colors))

color = _IMColorCtx



class _IMStyleCtx:
	def __init__(ims, styles):
		ims.styles = styles

	def __enter__(ims) -> IMGui[None]:
		for (style_var, value) in ims.styles.items():
			imgui.push_style_var(style_var, value)

	def __exit__(ims, *args) -> IMGui[None]:
		imgui.pop_style_var(len(ims.styles))


style = _IMStyleCtx