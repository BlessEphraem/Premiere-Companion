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
        commands += [
            {"displayName": "Better Transform", "matchName": "CMD.BM.transform", "type": "CMD.BM"},
            {"displayName": "Position",         "matchName": "CMD.BM.position",  "type": "CMD.BM", "dynamic": True},
            {"displayName": "Scale",            "matchName": "CMD.BM.scale",     "type": "CMD.BM", "dynamic": True},
            {"displayName": "Rotation",         "matchName": "CMD.BM.rotation",  "type": "CMD.BM", "dynamic": True},
            {"displayName": "Opacity",          "matchName": "CMD.BM.opacity",   "type": "CMD.BM", "dynamic": True},
        ]

    # ── Macros ───────────────────────────────────────────────────────────────
    from Core.functions.macros import get_macros_as_commands
    commands += get_macros_as_commands()

    return commands


# ── Execution ─────────────────────────────────────────────────────────────────

def execute_cmd_action(match_name, main_window, custom_data=None):
    """
    Execute a CMD action. custom_data is an optional string provided by
    the search bar when the user typed an inline value (e.g. 'opacity 0').
    """
    if match_name == "CMD.QA.toggle":
        _qa_toggle(main_window)
    elif match_name == "CMD.QA.delay":
        _qa_delay(main_window)
    elif match_name == "CMD.QA.calibrate":
        _qa_calibrate(main_window)
    elif match_name.startswith("CMD.BM."):
        _bm_action(match_name, main_window, custom_data)
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
    from Modules.apply_preset import PresetApplier
    from Core.theme_qss import THEME_USER_COLORS
    success, msg, data = PresetApplier.capture_and_validate(delay_ms=200)
    if success and data:
        PresetApplier.save_config(data)
        main_window.append_log(f" Quick Apply Calibration: {msg}", THEME_USER_COLORS["success"])
    else:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(main_window, "Calibration Failed", msg)
        main_window.append_log(f" Quick Apply Calibration Failed: {msg}", THEME_USER_COLORS["error"])


# ── BM helpers ────────────────────────────────────────────────────────────────

def parse_bm_value(prop, raw):
    """
    Parse raw user input into a structured BM command dict.
    Returns dict with prop, op_x, val_x, op_y, val_y  — or None if unparseable.

    Decimal separator : ","  (e.g. "100,5" = 100.5)
    X/Y separator (position only): "."  (e.g. "100.200" → X=100, Y=200)
    Prefix + → add (direct);  prefix - → sub (direct);  no prefix → set (absolute)
    Leading dot  ".200"  → skip X, operate on Y only
    Trailing dot "100."  → operate on X only, skip Y
    """
    raw = raw.strip()
    if not raw:
        return None

    def _parse_part(s):
        s = s.strip()
        if not s:
            return None, None
        s = s.replace(",", ".")
        try:
            if s.startswith("+"):
                return "add", float(s[1:])
            elif s.startswith("-"):
                return "sub", float(s[1:])
            else:
                return "set", float(s)
        except ValueError:
            return None, None

    result = {"prop": prop, "op_x": None, "val_x": None, "op_y": None, "val_y": None}

    if prop == "position":
        dot_idx = raw.find(".")
        if dot_idx == -1:
            op, val = _parse_part(raw)
            result.update(op_x=op, val_x=val, op_y=op, val_y=val)
        else:
            op_x, val_x = _parse_part(raw[:dot_idx])
            op_y, val_y = _parse_part(raw[dot_idx + 1:])
            result.update(op_x=op_x, val_x=val_x, op_y=op_y, val_y=val_y)
    else:
        op, val = _parse_part(raw)
        result.update(op_x=op, val_x=val)

    if result["val_x"] is None and result["val_y"] is None:
        return None
    return result


def _bm_action(match_name, main_window, custom_data=None):
    # CMD.BM.transform  (special top-level)
    if match_name == "CMD.BM.transform":
        from Core.functions.better_motion import start_better_transform
        start_better_transform()
        return

    parts = match_name.split(".")
    prop = parts[2] if len(parts) >= 3 else None
    if not prop:
        return

    if match_name.endswith(".dynamic") and custom_data and isinstance(custom_data, str):
        if custom_data.strip().lower() == "reset":
            from Core.functions.better_motion import send_better_motion_reset
            send_better_motion_reset(prop)
            return

        parsed = parse_bm_value(prop, custom_data)
        if not parsed:
            return
        from Core.functions.better_motion import send_better_motion_direct, send_better_motion_set
        op_x, val_x = parsed.get("op_x"), parsed.get("val_x")
        op_y, val_y = parsed.get("op_y"), parsed.get("val_y")

        if prop == "position":
            # Combine X+Y into a single call when both axes are the same operation type,
            # to avoid a read-then-write race where the second call overwrites the first.
            both_set = (op_x == "set" and op_y == "set" and val_x is not None and val_y is not None)
            both_rel = (op_x in ("add", "sub") and op_y in ("add", "sub") and val_x is not None and val_y is not None)
            if both_set:
                send_better_motion_set("position", val_x, val_y)
            elif both_rel:
                ax = val_x if op_x == "add" else -val_x
                ay = val_y if op_y == "add" else -val_y
                send_better_motion_direct("position", ax, ay)
            else:
                # One axis only (or mixed operations — handle individually)
                if val_x is not None:
                    if op_x in ("add", "sub"):
                        send_better_motion_direct("position", val_x if op_x == "add" else -val_x, 0)
                    elif op_x == "set":
                        send_better_motion_set("position", val_x, None)
                if val_y is not None:
                    if op_y in ("add", "sub"):
                        send_better_motion_direct("position", 0, val_y if op_y == "add" else -val_y)
                    elif op_y == "set":
                        send_better_motion_set("position", None, val_y)
        else:
            if val_x is not None:
                if op_x in ("add", "sub"):
                    send_better_motion_direct(prop, val_x if op_x == "add" else -val_x)
                elif op_x == "set":
                    send_better_motion_set(prop, val_x)
        return

    # Default: open interactive overlay
    if prop in ("position", "scale", "rotation", "opacity"):
        from Core.functions.better_motion import start_better_motion_adjust
        start_better_motion_adjust(prop)
