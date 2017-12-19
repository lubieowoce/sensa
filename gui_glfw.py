# -*- coding: utf-8 -*-
import glfw
import OpenGL.GL as gl

import imgui
import imgui as im
from imgui.integrations.glfw import GlfwRenderer

from time import sleep
from pyrsistent import (m, pmap, v, pvector)

from types_util import *
from util import rangeb, get_id, get_ids
from imgui_widget import (window, group, child)
from counter import *
from counter_list import *

MAX_AVAILABLE_SIZE = 0
NO_FLAGS = 0




n_counters = 4

cos = [counter(id) for id in get_ids(n_counters)]
state = m(counters=pmap({co.id: co for co in cos}))


def update(state: PMap_[str, Any], action: Action):

    if action.type in [ADD_COUNTER, REMOVE_COUNTER]:
        return state.transform(['counters'],
                                lambda counters: update_counter_list(counters, action))
    elif action.type in [INCREMENT, DECREMENT, SET_VALUE]:
        id = action.id
        return state.transform(['counters', id],
                               lambda counter: update_counter(counter, action))
    else:
        return state




def draw():
    """
    imgui.new_frame() is called right before `draw` in main.
    imgui.render() is called `draw` returns.
    """
    global state

    actions = []
    def emit(action):
        actions.append(action)

    with window(name="eeh"):
        im.text("counters")
        # with im.styled(im.STYLE_CHILD_WINDOW_ROUNDING, im.STYLE_WINDOW_ROUNDING):
        with child(name="add+delete",  width=40, height=100,
                   styles={im.STYLE_CHILD_WINDOW_ROUNDING: im.STYLE_WINDOW_ROUNDING}):

            if im.button("+", width=30, height=30):
                emit(add_counter())
                
            if im.button("-", width=30, height=30):
                emit(remove_counter())


        im.same_line()
        for id in state.counters:

            with child(name="counter "+str(id), width=100, height=100, border=True,
                       styles={im.STYLE_CHILD_WINDOW_ROUNDING: im.STYLE_WINDOW_ROUNDING}):

                im.text(str(state.counters[id].val))

                imgui.separator()

                changed, new_val = \
                    im.input_text('value', value=str(state.counters[id].val),
                                  buffer_length=1000,
                                  flags=im.INPUT_TEXT_ENTER_RETURNS_TRUE | im.INPUT_TEXT_CHARS_DECIMAL)
                if changed:
                    emit( set_value(new_val, id) )


                if im.button("+"):
                    emit( increment(1, id) )

                if im.button("-"):
                    emit( decrement(1, id))

            im.same_line()

        im.new_line()

        st = state
        for act in actions:
            st = update(st, act)
        state = st



def main():
    window = impl_glfw_init()
    impl = GlfwRenderer(window)

    target_framerate = 30.
    max_frame_dur = 1/target_framerate

    frame_start = 0.
    frame_end = 0.
    frame_dur = 0.
    wait_dur = 0.


    while not glfw.window_should_close(window):

        frame_start = glfw.get_time() # seconds

        glfw.poll_events()
        impl.process_inputs()

        imgui.new_frame()
        

        draw() # defined above


        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        glfw.swap_buffers(window)

        frame_end = glfw.get_time() # seconds
        frame_dur = frame_end - frame_start
        wait_dur = max_frame_dur - frame_dur
        if wait_dur > 0:
            sleep(wait_dur)



    impl.shutdown()
    imgui.shutdown()
    glfw.terminate()




def impl_glfw_init():
    width, height = 1280, 720
    window_name = "minimal ImGui/GLFW3 example"

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
        int(width), int(height), window_name, None, None
    )
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window


if __name__ == "__main__":
    main()



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