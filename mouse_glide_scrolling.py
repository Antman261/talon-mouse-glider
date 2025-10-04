from collections import deque
from math import trunc
from talon import Module, Context, cron, actions, ctrl, imgui, settings


mod = Module()
mod.tag(
    "mouse_glide_active",
    desc="commands for stopping mouse glide",
)

ctx = Context()

position_tuple = [None, None]
scroll_job = None
delta_y_previous = 0
delta_x_previous = 0
has_stopped = True

inertia_buffer_x = deque(maxlen=10)
inertia_buffer_y = deque(maxlen=10)


@imgui.open(x=700, y=0)
def gui_wheel(gui: imgui.GUI):
    gui.text(f"Scroll mode: Mouse Glide")
    gui.line()
    if gui.button("Glide Stop [stop scrolling]"):
        actions.user.mouse_glide_stop()


def scroll_glide_helper():
    global delta_y_previous, delta_x_previous, has_stopped
    current_x, current_y = ctrl.mouse_pos()
    previous_x, previous_y = get_position()
    delta_y_accel = calc_accel(*calc_vector(current_y, previous_y))
    delta_x_accel = calc_accel(*calc_vector(current_x, previous_x))
    buffer(delta_x_accel, delta_y_accel)
    has_stopped = delta_x_accel == 0 and delta_y_accel == 0
    set_previous_delta()
    delta_y_inertia = delta_y_previous if has_stopped else 0.0
    delta_x_inertia = delta_x_previous if has_stopped else 0.0
    actions.mouse_scroll(
        delta_y_accel + delta_y_inertia, delta_x_accel + delta_x_inertia
    )
    actions.mouse_move(previous_x, previous_y)


def set_previous_delta():
    global delta_y_previous, delta_x_previous
    if has_stopped:
        delta_y_previous = delta_y_previous / 1.1
        delta_x_previous = delta_x_previous / 1.1
    else:
        delta_y_previous = calc_buffer_avg("y")
        delta_x_previous = calc_buffer_avg("x")


def calc_vector(curr, prev):
    delta = trunc(curr - prev)
    direction = int(delta >= 0) or -1
    return delta, direction


def calc_accel(delta, direction):
    acceleration = 1.5
    if -1 < delta < 1:
        return delta * -acceleration
    return abs(delta**acceleration) * -direction


def initialize_position():
    x, y = ctrl.mouse_pos()
    set_position(x, y)


def set_position(x: int, y: int):
    global position_tuple
    position_tuple.clear()
    position_tuple.append(x)
    position_tuple.append(y)


def get_position():
    global position_tuple
    return position_tuple


def calc_buffer_avg(dir):
    inertia_buffer = inertia_buffer_y if dir == "y" else inertia_buffer_x
    return sum(inertia_buffer) / (len(inertia_buffer) or 1)


def buffer(x, y):
    inertia_buffer_x.append(x)
    inertia_buffer_y.append(y)


control_enabled = None
control1_enabled = None


def save_tracking_state():
    global control_enabled, control1_enabled
    control_enabled = actions.tracking.control_enabled()
    control1_enabled = actions.tracking.control1_enabled()
    actions.tracking.control_toggle(False)
    actions.tracking.control1_toggle(False)


def restore_tracking_state():
    global control_enabled, control1_enabled
    actions.tracking.control_toggle(control_enabled)
    actions.tracking.control1_toggle(control1_enabled)


@mod.action_class
class Actions:
    def mouse_glide_toggle():
        """Toggle mouse glide scrolling"""
        if scroll_job != None:
            return actions.user.mouse_glide_stop()
        actions.user.mouse_glide_start()

    def mouse_glide_start():
        """begin mouse glide scrolling"""
        global scroll_job
        if scroll_job != None:
            return
        save_tracking_state()
        scroll_job = cron.interval("16ms", scroll_glide_helper)
        initialize_position()
        ctx.tags = ["user.mouse_glide_active"]
        if not settings.get("user.mouse_hide_mouse_gui"):
            gui_wheel.show()

    def mouse_glide_stop():
        """stop mouse glide scrolling"""
        global scroll_job
        cron.cancel(scroll_job)
        scroll_job = None
        gui_wheel.hide()
        ctx.tags = []
        restore_tracking_state()
