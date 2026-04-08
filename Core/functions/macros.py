# Core/functions/macros.py
import time
import threading
from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QTimer
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

def execute_macro(macro_data, main_window):
    """
    Executes a sequence of actions. 
    Runs in a separate thread to avoid UI freezing if presets are involved.
    """
    actions = macro_data.get("actions", [])
    if not actions:
        return

    def safe_log(msg, color=THEME_USER_COLORS["info"]):
        if hasattr(main_window, "hotkey_signal"):
            main_window.hotkey_signal.log_signal.emit(msg, color)
        else:
            # Fallback to direct call via timer if signal not found
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: main_window.append_log(msg, color))

    safe_log(f" Starting Macro: '{macro_data['name']}'")

    def run():
        try:
            for action in actions:
                match_name = action["matchName"]
                e_type = action["type"]
                display_name = action.get('displayName', match_name)
                
                safe_log(f"  > Action: {display_name}", THEME_USER_COLORS["text_subtle"])
                
                if is_command(e_type):
                    from Core.functions.cmd_actions import execute_cmd_action
                    from PyQt6.QtCore import QTimer
                    # We MUST execute command actions on the main thread
                    QTimer.singleShot(0, lambda m=match_name: execute_cmd_action(m, main_window))
                
                elif is_preset(e_type):
                    config = PresetApplier.load_config()
                    is_qa = config.get("quick_apply_enabled", False) if config else False
                    success, msg = PresetApplier.apply_preset_to_premiere(match_name, is_qa)
                    if not success:
                        safe_log(f" Macro Aborted: {msg}", THEME_USER_COLORS["error"])
                        return
                
                elif is_transition(e_type):
                    # Default to 'both' for transitions in macros to avoid blocking
                    EffectApplier.apply_effect_to_premiere(match_name, e_type, alignment="both")
                
                else:
                    EffectApplier.apply_effect_to_premiere(match_name, e_type)
                
                # Small pause between actions
                time.sleep(0.5)
                
            safe_log(f" Macro '{macro_data['name']}' completed!", THEME_USER_COLORS["success"])
            
        except Exception as e:
            safe_log(f" Macro Error: {e}", THEME_USER_COLORS["error"])

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
