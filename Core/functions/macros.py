# Core/functions/macros.py
import time
import threading
from PyQt6.QtCore import QTimer
from Core.configs.macros_config import load_macros_config, save_macros_config
from Core.theme_qss import THEME_USER_COLORS
from Core.configs.labels_config import is_video, is_audio, is_transition, is_preset, is_command
from Modules.apply_effect import EffectApplier
from Modules.apply_preset import PresetApplier


def get_macros_as_commands():
    config = load_macros_config()
    commands = []
    for macro in config.get("macros", []):
        commands.append({
            "displayName": macro["name"],
            "matchName": f"CMD.MA.{macro['name']}",
            "type": "CMD.MA",
            "actions": macro["actions"]
        })
    return commands


# ── Pre-flight validation ──────────────────────────────────────────────────────

def _preflight_check(actions, log_fn):
    """
    Synchronously validate all preconditions before running the macro.
    Returns True if all checks pass; False (after logging) if any fail.
    """
    has_preset = any(is_preset(a.get("type", "")) for a in actions)
    has_bm     = any(a.get("matchName", "").startswith("CMD.BM.") for a in actions)

    if has_preset:
        ok, msg = PresetApplier.validate_for_macro()
        if not ok:
            log_fn(f" Macro bloquée — {msg}", THEME_USER_COLORS["error"])
            return False

    if has_bm:
        from Core.functions.cmd_actions import _load_bm_config
        bm_cfg = _load_bm_config()
        if not bm_cfg.get("enabled", False):
            log_fn(" Macro bloquée — Better Motion n'est pas activé.", THEME_USER_COLORS["error"])
            return False

    return True


# ── Execution ──────────────────────────────────────────────────────────────────

def execute_macro(macro_data, main_window):
    """
    Execute a macro's action sequence.
    Pre-flight runs synchronously; actions run in a daemon thread.
    """
    actions = macro_data.get("actions", [])
    if not actions:
        return

    def safe_log(msg, color=THEME_USER_COLORS["info"]):
        if hasattr(main_window, "hotkey_signal"):
            main_window.hotkey_signal.log_signal.emit(msg, color)
        else:
            QTimer.singleShot(0, lambda: main_window.append_log(msg, color))

    # Pre-flight: validate all dependencies before starting
    if not _preflight_check(actions, safe_log):
        return

    safe_log(f" Starting Macro: '{macro_data['name']}'")

    def run():
        try:
            for action in actions:
                match_name  = action.get("matchName", "")
                e_type      = action.get("type", "")
                display_name = action.get("displayName", match_name)
                params      = action.get("params", {})

                # Sleep action — IS the pause, skip the standard 0.5s gap
                if e_type == "SLEEP":
                    duration_ms = params.get("duration_ms", 1000)
                    safe_log(f"  > Sleep {duration_ms}ms", THEME_USER_COLORS["text_subtle"])
                    time.sleep(max(0, duration_ms) / 1000.0)
                    continue

                safe_log(f"  > {display_name}", THEME_USER_COLORS["text_subtle"])

                if is_command(e_type):
                    from Core.functions.cmd_actions import execute_cmd_action
                    custom_data = params.get("custom_data")
                    # Commands must run on the main thread
                    QTimer.singleShot(
                        0,
                        lambda m=match_name, cd=custom_data: execute_cmd_action(m, main_window, custom_data=cd)
                    )

                elif is_preset(e_type):
                    config = PresetApplier.load_config()
                    is_qa = config.get("quick_apply_enabled", False) if config else False
                    # Always release at mouse in macros — keep_on_mouse would block the next action
                    success, msg = PresetApplier.apply_preset_to_premiere(match_name, is_qa, keep_on_mouse=False)
                    if not success:
                        safe_log(f" Macro Aborted: {msg}", THEME_USER_COLORS["error"])
                        return

                elif is_transition(e_type):
                    alignment = params.get("alignment", "start")
                    EffectApplier.apply_effect_to_premiere(match_name, e_type, alignment=alignment)

                else:
                    # FX.V / FX.A
                    EffectApplier.apply_effect_to_premiere(match_name, e_type)

                time.sleep(0.5)

            safe_log(f" Macro '{macro_data['name']}' completed!", THEME_USER_COLORS["success"])

        except Exception as e:
            safe_log(f" Macro Error: {e}", THEME_USER_COLORS["error"])

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
