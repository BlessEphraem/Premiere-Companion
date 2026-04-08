# Core/functions/cmd_actions.py
# Dynamic CMD action commands — generation and execution

import os
import json
from Core.paths import get_data_path
from Core.theme_qss import THEME_USER_COLORS


# ── Config I/O ────────────────────────────────────────────────────────────────

def load_cmd_actions_config():
    from Core.configs.cmd_actions_config import DEFAULT_CMD_ACTIONS_CONFIG
    path = get_data_path("cmd_actions_config.json")
    config = dict(DEFAULT_CMD_ACTIONS_CONFIG)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except Exception:
            pass
    return config


def save_cmd_actions_config(config):
    path = get_data_path("cmd_actions_config.json")
    os.makedirs(get_data_path(), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def _load_qa_config():
    from Modules.apply_preset import PresetApplier
    return PresetApplier.load_config() or {}


def _load_bm_config():
    path = get_data_path("betterMotion_config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ── Dynamic command list ──────────────────────────────────────────────────────

def get_dynamic_commands():
    """
    Build the list of CMD action items based on current QA/BM config.
    Returns a list of dicts with displayName, matchName, type="CMD".
    """
    cfg = load_cmd_actions_config()
    if not cfg.get("enabled", True):
        return []

    commands = []

    # ── Quick Apply commands ──────────────────────────────────────────────────
    qa_config = _load_qa_config()
    qa_enabled = qa_config.get("quick_apply_enabled", False)
    qa_has_capture = "mouse_x" in qa_config and "mouse_y" in qa_config

    if qa_has_capture:
        state = "ON" if qa_enabled else "OFF"
        delay_ms = qa_config.get("delay_ms", 200)
        commands += [
            {"displayName": f"Toggle Quick Apply ({state})", "matchName": "CMD.QA.toggle",    "type": "CMD.QA"},
            {"displayName": f"Set Delay ({delay_ms} ms)",    "matchName": "CMD.QA.delay",     "type": "CMD.QA"},
            {"displayName": "Start Calibration",              "matchName": "CMD.QA.calibrate", "type": "CMD.QA"},
        ]

    # ── Better Motion commands ────────────────────────────────────────────────
    bm_config = _load_bm_config()
    bm_enabled = bm_config.get("enabled", False)

    if bm_enabled:
        def _amt(sec, act):
            d = bm_config.get(sec, {}).get(act, {})
            return d.get("amount", 0) if isinstance(d, dict) else 0

        commands += [
            {"displayName": "Better Transform",            "matchName": "CMD.BM.transform",       "type": "CMD.BM"},
        ]

        pxa = _amt("position", "x_add")
        pxs = _amt("position", "x_sub")
        pya = _amt("position", "y_add")
        pys = _amt("position", "y_sub")
        commands += [
            {"displayName": "Position Adjust",            "matchName": "CMD.BM.position.adjust", "type": "CMD.BM"},
            {"displayName": "Position Reset",             "matchName": "CMD.BM.position.reset",  "type": "CMD.BM"},
            {"displayName": f"Position Add X (+{pxa})",   "matchName": "CMD.BM.position.x_add",  "type": "CMD.BM"},
            {"displayName": f"Position Sub X ({pxs})",    "matchName": "CMD.BM.position.x_sub",  "type": "CMD.BM"},
            {"displayName": f"Position Add Y (+{pya})",   "matchName": "CMD.BM.position.y_add",  "type": "CMD.BM"},
            {"displayName": f"Position Sub Y ({pys})",    "matchName": "CMD.BM.position.y_sub",  "type": "CMD.BM"},
        ]

        for sec in ("scale", "rotation", "opacity"):
            amt_add = _amt(sec, "add")
            amt_sub = _amt(sec, "sub")
            sec_cap = sec.capitalize()
            commands += [
                {"displayName": f"{sec_cap} Adjust",           "matchName": f"CMD.BM.{sec}.adjust", "type": "CMD.BM"},
                {"displayName": f"{sec_cap} Reset",            "matchName": f"CMD.BM.{sec}.reset",  "type": "CMD.BM"},
                {"displayName": f"{sec_cap} Add (+{amt_add})", "matchName": f"CMD.BM.{sec}.add",    "type": "CMD.BM"},
                {"displayName": f"{sec_cap} Sub ({amt_sub})",  "matchName": f"CMD.BM.{sec}.sub",    "type": "CMD.BM"},
            ]

    # ── Macros ───────────────────────────────────────────────────────────────
    from Core.functions.macros import get_macros_as_commands
    commands += get_macros_as_commands()

    return commands


# ── Execution ─────────────────────────────────────────────────────────────────

def execute_cmd_action(match_name, main_window, custom_value=None):
    """
    Execute a CMD action. custom_value is an optional positive integer
    provided by the smart number search (e.g. the user typed 'position add 125').
    """
    if match_name == "CMD.QA.toggle":
        _qa_toggle(main_window)
    elif match_name == "CMD.QA.delay":
        _qa_delay(main_window)
    elif match_name == "CMD.QA.calibrate":
        _qa_calibrate(main_window)
    elif match_name.startswith("CMD.BM."):
        _bm_action(match_name, main_window, custom_value)
    elif match_name.startswith("CMD.MA."):
        from Core.functions.macros import execute_macro
        # matchName is CMD.MA.<MacroName>
        macro_name = match_name[7:]
        from Core.configs.macros_config import load_macros_config
        config = load_macros_config()
        for macro in config.get("macros", []):
            if macro["name"] == macro_name:
                execute_macro(macro, main_window)
                break


# ── QA helpers ────────────────────────────────────────────────────────────────

def _qa_toggle(main_window):
    from Modules.apply_preset import PresetApplier
    config = PresetApplier.load_config() or {}
    config["quick_apply_enabled"] = not config.get("quick_apply_enabled", False)
    PresetApplier.save_config(config)
    state = "ENABLED" if config["quick_apply_enabled"] else "DISABLED"
    main_window.append_log(f" Quick Apply {state}", THEME_USER_COLORS["info"])
    main_window.reload_commands()


def _qa_delay(main_window):
    from PyQt6.QtWidgets import QInputDialog
    from Modules.apply_preset import PresetApplier
    config = PresetApplier.load_config() or {}
    current = config.get("delay_ms", 200)
    val, ok = QInputDialog.getInt(
        main_window,
        "Set Delay",
        "Set a delay value (ms):",
        value=current, min=0, max=5000, step=10
    )
    if ok:
        config["delay_ms"] = val
        PresetApplier.save_config(config)
        main_window.append_log(f" QA Delay set to {val} ms", THEME_USER_COLORS["success"])
        main_window.reload_commands()


def _qa_calibrate(main_window):
    from GUI.Pages.quickApply_page import QuickApplyWizard
    from Core.functions.windows import apply_window_config
    wizard = QuickApplyWizard(main_window)
    apply_window_config(wizard, "quick_apply", "Configuration: Quick Apply for Presets")
    main_window.register_child_window(wizard)
    wizard.show()
    wizard.start_capture()


# ── BM helpers ────────────────────────────────────────────────────────────────

def _bm_action(match_name, main_window, custom_value=None):
    # CMD.BM.transform  (special top-level)
    if match_name == "CMD.BM.transform":
        from Core.functions.better_motion import start_better_transform
        start_better_transform()
        return

    # CMD.BM.<sec>.<act>  →  parts = [CMD, BM, sec, act]
    parts = match_name.split(".")
    if len(parts) < 4:
        return
    sec = parts[2]
    act = parts[3]

    if act == "adjust":
        from Core.functions.better_motion import start_better_motion_adjust
        start_better_motion_adjust(sec)
        return

    if act == "reset":
        from Core.functions.better_motion import send_better_motion_reset
        send_better_motion_reset(sec)
        return

    if custom_value is not None:
        # custom_value is always a positive integer from smart search
        sign = -1 if "sub" in act else 1
        amount = sign * abs(custom_value)
    else:
        bm_config = _load_bm_config()
        d = bm_config.get(sec, {}).get(act, {})
        amount = d.get("amount", 0) if isinstance(d, dict) else 0

    from Core.functions.better_motion import send_better_motion_direct

    if sec == "position":
        if act in ("x_add", "x_sub"):
            send_better_motion_direct("position", amount, 0)
        elif act in ("y_add", "y_sub"):
            send_better_motion_direct("position", 0, amount)
    else:
        send_better_motion_direct(sec, amount)
