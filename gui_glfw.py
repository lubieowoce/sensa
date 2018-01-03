# -*- coding: utf-8 -*-
import glfw
import OpenGL.GL as gl

import imgui
import imgui as im
from imgui.integrations.glfw import GlfwRenderer

from time import sleep
from pyrsistent import (m, pmap, v, pvector)

from types_util import *
from util import rangeb
from id_eff import id_and_effects, run_id_eff, get_ids
from imgui_widget import (window, group, child)
from counter import *
from counter_list import *

from files import *
from signal import Signal
# from multisignal import MultiSignal
# from filters import \
#     lowpass_filter,  make_lowpass_tr, \
#     highpass_filter, make_highpass_tr
# from trans import Trans, TransChain


current_id = 0


@id_and_effects
def initial_state() -> IdEff[PMap_[str, Any]]:
    n_counters = 4
    cos = [counter(id) for id in get_ids(n_counters)]
    return m(counters=    pmap(   {co.id: co for co in cos}),
             counter_list=pvector([co.id     for co in cos])  )


state, current_id, _ = run_id_eff(initial_state, id=current_id)()


@id_and_effects
def update(state: PMap_[str, Any], action: Action) -> IdEff[PMap_[str, Any]]:
    # state = { counters: {id: counter},
    #           counter_list: [id]       }
    if action.type in [ADD_COUNTER, REMOVE_COUNTER, CLEAR_COUNTERS]:
        return update_counter_list(state, action)

    elif action.type in [INCREMENT, DECREMENT, SET_VALUE]:
        id = action.id
        return state.transform(['counters', id],
                               lambda counter: update_counter(counter, action))

    elif action.type in [LOAD_FILE]:
        emit_effect( load_file_eff(action.filename) )
        return state
    else:
        return state


data = {'signals':{}}

def handle(data, command):
    if command.type in [LOAD_FILE_EFF]:
        handle_load_file(data['signals'], command)




frame_actions = [] # all the actions that happened during current frame

def emit(action):
    frame_actions.append(action)

def clear_actions():
    frame_actions.clear()


def update_state_with_actions():
    global state
    global frame_actions
    global current_id

    all_effects = []
    for act in frame_actions:
        state, current_id, effects = run_id_eff(update, id=current_id)(state, act)
        all_effects.extend(effects)

    for eff in all_effects:
        handle(data, eff)



def draw():
    """
    imgui.new_frame() is called right before `draw` in main.
    imgui.render() is called `draw` returns.
    """
    global state
    global data
    # state = { counters: {id: counter},
    #           counter_list: [id]       }

    assert len(frame_actions) == 0, "Actions buffer not cleared! Is:" + str(frame_actions) 


    with window(name="eeh"):
        im.text("counters")
        # with im.styled(im.STYLE_CHILD_WINDOW_ROUNDING, im.STYLE_WINDOW_ROUNDING):
        with child(name="add+delete",  width=40, height=100,
                   styles={im.STYLE_CHILD_WINDOW_ROUNDING: im.STYLE_WINDOW_ROUNDING}):

            if im.button("+", width=30, height=30):
                emit(add_counter())
                
            if im.button("-", width=30, height=30):
                emit(remove_counter())

            if im.button("clear", width=30, height=30):
                emit(clear_counters())


        im.same_line()
        for id in state.counter_list:

            with child(name="counter "+str(id), width=100, height=100, border=True,
                       styles={im.STYLE_CHILD_WINDOW_ROUNDING: im.STYLE_WINDOW_ROUNDING}) as is_counter_visible:
                if is_counter_visible:
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

    im.show_metrics_window()

    im.text(str(frame_actions))

    with window(name="waveform"):
        window_pos = im.get_window_position()
        draw_list = im.get_window_draw_list()

        red = (1,0,0,1)
        draw_list.add_line(point_offset(window_pos, im.Vec2(40, 60)),
                           point_offset(window_pos, im.Vec2(110, 150)),
                           color=red)

    with window(name="signals"):
        if im.button("load example"):
            emit(load_file(example_file))


        if len(data['signals']) > 0:
            im.separator()

        for label, signal in data['signals'].items():
            im.text_colored(label, 0.2, 0.8, 1)
            im.same_line()
            im.text(str(signal))
        






def point_delta(a: im.Vec2, b: im.Vec2) -> im.Vec2:
    return im.Vec2(b.x-a.x, b.y-a.y)

def point_offset(a: im.Vec2, b: im.Vec2) -> im.Vec2:
    return im.Vec2(b.x+a.x, b.y+a.y)


def main():

    window = impl_glfw_init()
    impl = GlfwRenderer(window)
    io = imgui.get_io()

    target_framerate = 30.
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

        nonlocal prev_mouse_pos
        nonlocal prev_mouse_down_0
        nonlocal prev_frame_click_0_finished

        mouse_moved = (io.mouse_pos != prev_mouse_pos)
        mouse_changed = io.mouse_down[0] != prev_mouse_down_0
        click_0_finished = prev_mouse_down_0 and (not io.mouse_down[0]) # mouse was down previous frame, now it's up
        # key_clicked = any(io.keys_down)
        result =  mouse_moved or mouse_changed or io.mouse_down[0] or prev_frame_click_0_finished # or key_clicked

        prev_mouse_pos = io.mouse_pos
        prev_mouse_down_0 = io.mouse_down[0]
        prev_frame_click_0_finished = click_0_finished
        return result


    while not glfw.window_should_close(window):

        frame_start = glfw.get_time() # seconds

        glfw.poll_events()
        impl.process_inputs()

        got_inp = got_input()


        if got_inp:
            imgui.new_frame()
    

            draw() # defined above

            update_state_with_actions()
            clear_actions()


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