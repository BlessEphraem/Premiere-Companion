# Core/functions/better_motion.py
from Core.functions.server import send_to_plugin
from GUI.Widgets.BetterMotion import BetterMotionOverlay, BetterTransformOverlay

_active_overlay = None

def handle_bm_ready(prop, value):
    global _active_overlay
    if _active_overlay is not None:
        _active_overlay.set_initial_value(value)

def clear_active_overlay():
    global _active_overlay
    _active_overlay = None

def start_better_motion_adjust(prop_name):
    global _active_overlay
    if _active_overlay is not None:
        _active_overlay.finish_action(False)
    _active_overlay = BetterMotionOverlay(prop_name)
    _active_overlay.show()

def start_better_transform():
    global _active_overlay
    if _active_overlay is not None:
        _active_overlay.finish_action(False)
    _active_overlay = BetterTransformOverlay()
    _active_overlay.show()

def send_better_motion_direct(prop_name, amount_x, amount_y=0):
    send_to_plugin({
        "action": "better_motion",
        "status": "direct",
        "prop": prop_name,
        "amountX": amount_x,
        "amountY": amount_y
    })

def send_better_motion_reset(prop_name):
    send_to_plugin({
        "action": "better_motion",
        "status": "reset",
        "prop": prop_name
    })
