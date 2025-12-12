from talon import Module, Context

mod = Module()
mod.tag(
    "mouse_glide_keyboard_on",
    desc="Enables stopping mouse glide by pressing space",
)
ctx = Context()


@mod.action_class
class Actions:
    def mouse_glide_keyboard_off():
        """Turn off ability to exit glide mode by pressing space"""
        ctx.tags = []

    def mouse_glide_keyboard_on():
        """Turn on ability to exit glide mode by pressing space"""
        ctx.tags = ["user.mouse_glide_keyboard_on"]
