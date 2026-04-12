# Core/hotkeys.py
import os
import json
import ctypes
import threading
from ctypes import wintypes
import win32gui
from Modules.apply_effect import EffectApplier
from Modules.apply_preset import PresetApplier
from Core.configs.labels_config import is_transition, is_preset
from Core.theme_qss import THEME_USER_COLORS
from Core.functions.keybinds_send import parse_shortcut
from Core.functions.search import save_last_used


def check_keybind_conflict(new_keybind, custom_hotkeys_list, built_in_keybinds=None):
    """
    Check if a keybind is already in use by built-in or custom hotkeys.
    
    Args:
        new_keybind: str - The keybind to check (e.g., "Ctrl+Shift+A")
        custom_hotkeys_list: list[dict] - Current custom hotkeys in memory
        built_in_keybinds: dict - Built-in keybinds {action_name: keybind_str}
    
    Returns:
        tuple: (has_conflict: bool, conflict_description: str or None)
    """
    if not new_keybind:
        return False, None
    
    new_keybind_normalized = new_keybind.strip()
    
    if built_in_keybinds:
        for action, keybind in built_in_keybinds.items():
            if keybind and new_keybind_normalized.lower() == keybind.strip().lower():
                return True, action
    
    for chk in custom_hotkeys_list:
        existing = chk.get("keybind", "")
        if existing and new_keybind_normalized.lower() == existing.strip().lower():
            effect_type = chk.get("effect_type", "Unknown")
            match_name = chk.get("match_name", "Unknown")
            return True, f"[{effect_type}] {match_name}"
    
    return False, None


class HotkeyListener(threading.Thread):
    def __init__(self, hotkeys, callbacks_map, on_stop_callback=None, log_callback=None):
        super().__init__(daemon=True)
        self.hotkeys = hotkeys
        self.callbacks_map = callbacks_map
        self.on_stop_callback = on_stop_callback
        self.log_callback = log_callback
        self.thread_id = None
        self.registered_ids = []   # only hotkeys that actually registered

    def run(self):
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        user32 = ctypes.windll.user32

        for hk in self.hotkeys:
            ok = user32.RegisterHotKey(None, hk["id"], hk["modifiers"], hk["vk"])
            if ok:
                self.registered_ids.append(hk["id"])
            else:
                err = ctypes.windll.kernel32.GetLastError()
                if self.log_callback:
                    mod_names = []
                    if hk["modifiers"] & 0x0002: mod_names.append("Ctrl")
                    if hk["modifiers"] & 0x0001: mod_names.append("Alt")
                    if hk["modifiers"] & 0x0004: mod_names.append("Shift")
                    if hk["modifiers"] & 0x0008: mod_names.append("Win")
                    mod_str = "+".join(mod_names) or "None"
                    from Core.theme_qss import THEME_USER_COLORS
                    self.log_callback(
                        f" Warning: Failed to register hotkey (mods={mod_str}, vk=0x{hk['vk']:02X}) — "
                        f"already in use by another app (error {err}).",
                        THEME_USER_COLORS["warning"]
                    )

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:  # 0x0312 = WM_HOTKEY
                hk_id = msg.wParam
                cb = self.callbacks_map.get(hk_id)
                if cb:
                    try:
                        cb()
                    except Exception as e:
                        if self.log_callback:
                            from Core.theme_qss import THEME_USER_COLORS
                            self.log_callback(f" Hotkey callback error: {e}", THEME_USER_COLORS["error"])
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        for hk_id in self.registered_ids:
            user32.UnregisterHotKey(None, hk_id)

        if self.on_stop_callback:
            self.on_stop_callback()

class GlobalHotkeyManager:
    def __init__(self, trigger_callback, log_callback, transition_callback=None,
                 last_used_getter=None, config_getter=None, bm_callback=None, bt_callback=None):
        self.trigger_callback = trigger_callback
        self.log_callback = log_callback
        self.transition_callback = transition_callback
        self.last_used_getter = last_used_getter
        self.config_getter = config_getter
        self.bm_callback = bm_callback
        self.bt_callback = bt_callback
        self.hotkey_thread = None

    def update_global_hotkey(self):
        from Core.paths import get_data_path
        kb_path = get_data_path("keybinds.json")
        legacy_kb_path = get_data_path("pr_keybinds.json")
        search_str = "Ctrl+Space"
        custom_hotkeys = []

        path_to_load = kb_path
        if not os.path.exists(kb_path) and os.path.exists(legacy_kb_path):
            path_to_load = legacy_kb_path

        if os.path.exists(path_to_load):
            try:
                with open(path_to_load, "r", encoding="utf-8") as f:
                    keybinds = json.load(f)
                search_str = keybinds.get("Run Search Bar", "Ctrl+Space")
                custom_hotkeys = keybinds.get("custom_hotkeys", [])
            except Exception as e:
                self.log_callback(f" Error reading keybinds: {e}", THEME_USER_COLORS["error"])

        bm_path = get_data_path("betterMotion_config.json")
        bm_config = {}
        if os.path.exists(bm_path):
            try:
                with open(bm_path, "r", encoding="utf-8") as f:
                    bm_config = json.load(f)
            except Exception as e:
                self.log_callback(f" Error reading Better Motion config: {e}", THEME_USER_COLORS["error"])

        if self.hotkey_thread and self.hotkey_thread.thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(self.hotkey_thread.thread_id, 0x0012, 0, 0)
                self.hotkey_thread.join(timeout=1.0)
                if self.hotkey_thread.is_alive():
                    self.log_callback(" Warning: Hotkey thread did not stop cleanly.", THEME_USER_COLORS["warning"])
            except Exception as e:
                self.log_callback(f" Error stopping hotkey thread: {e}", THEME_USER_COLORS["error"])

        hotkeys_config = []
        callbacks_map = {}
        
        mods, vk = parse_shortcut(search_str)
        if vk != 0:
            hotkeys_config.append({"id": 1, "modifiers": mods, "vk": vk})
            def on_search():
                try:
                    hwnd = win32gui.GetForegroundWindow()
                    title = win32gui.GetWindowText(hwnd)
                    if hwnd and ("Adobe Premiere Pro" in title or win32gui.GetClassName(hwnd) == "Premiere Pro"):
                        self.trigger_callback()
                except Exception:
                    pass
            callbacks_map[1] = on_search

        current_id = 2
        for chk in custom_hotkeys:
            ch_str = chk.get("keybind", "")
            mods, vk = parse_shortcut(ch_str)
            
            # Prefer the native virtual key code if saved (robust for international layouts)
            if "vk" in chk and chk["vk"] != 0:
                vk = chk["vk"]
                
            if vk != 0:
                hk_id = current_id
                hotkeys_config.append({"id": hk_id, "modifiers": mods, "vk": vk})
                
                def make_custom_callback(m_name, e_type):
                    def cb():
                        try:
                            hwnd = win32gui.GetForegroundWindow()
                            title = win32gui.GetWindowText(hwnd)
                            if hwnd and ("Adobe Premiere Pro" in title or win32gui.GetClassName(hwnd) == "Premiere Pro"):
                                if is_transition(e_type) and self.transition_callback:
                                    self.transition_callback(m_name, e_type)
                                elif is_preset(e_type):
                                    config = self.config_getter() if self.config_getter else {}
                                    last_used = self.last_used_getter() if self.last_used_getter else None

                                    skip_typing = (
                                        config.get("apply_last_without_name_enter", False) and
                                        last_used is not None and
                                        last_used.get("match_name") == m_name
                                    )

                                    res = PresetApplier.apply_preset_to_premiere(m_name, True, skip_typing=skip_typing)
                                    if isinstance(res, tuple):
                                        success, msg = res[0], res[1]
                                    else:
                                        success, msg = True, "Preset applied"

                                    if success:
                                        if skip_typing:
                                            self.log_callback(f" Preset applied (LAST USED): {m_name}", THEME_USER_COLORS["success"])
                                        else:
                                            self.log_callback(f" Preset applied: {m_name}", THEME_USER_COLORS["success"])
                                        save_last_used(m_name, e_type, m_name)
                                    else:
                                        self.log_callback(f" Failed to apply preset: {msg}", THEME_USER_COLORS["error"])
                                else:
                                    EffectApplier.apply_effect_to_premiere(m_name, e_type)
                                    self.log_callback(f" Effect applied: {m_name}", THEME_USER_COLORS["info"])
                                    save_last_used(m_name, e_type, m_name)
                        except Exception as e:
                            self.log_callback(f" Error in custom hotkey ({m_name}): {e}", THEME_USER_COLORS["error"])
                            try:
                                import ctypes
                                ctypes.windll.user32.BlockInput(False)
                            except: pass
                    return cb
                
                callbacks_map[hk_id] = make_custom_callback(chk.get("match_name"), chk.get("effect_type"))
                current_id += 1

        if bm_config.get("enabled", False):
            from Core.functions.better_motion import send_better_motion_direct, send_better_motion_reset

            # Better Transform top-level hotkey
            bt_data = bm_config.get("better_transform", {})
            if isinstance(bt_data, dict):
                bt_kb = bt_data.get("key", "")
                bt_vk = bt_data.get("vk", 0)
                if bt_kb:
                    mods, vk = parse_shortcut(bt_kb)
                    if bt_vk != 0:
                        vk = bt_vk
                    if vk != 0:
                        hk_id = current_id
                        hotkeys_config.append({"id": hk_id, "modifiers": mods, "vk": vk})

                        def make_bt_callback():
                            def cb():
                                try:
                                    hwnd = win32gui.GetForegroundWindow()
                                    title = win32gui.GetWindowText(hwnd)
                                    if hwnd and ("Adobe Premiere Pro" in title or win32gui.GetClassName(hwnd) == "Premiere Pro"):
                                        self.log_callback(" Better Transform triggered", THEME_USER_COLORS["info"])
                                        if self.bt_callback:
                                            self.bt_callback()
                                except Exception as e:
                                    self.log_callback(f" Error in Better Transform: {e}", THEME_USER_COLORS["error"])
                            return cb

                        callbacks_map[hk_id] = make_bt_callback()
                        current_id += 1

            for sec_key in ["position", "scale", "rotation", "opacity"]:
                if sec_key in bm_config:
                    sec_data = bm_config[sec_key]
                    for act_key, act_val in sec_data.items():
                        # Skip non-hotkey config values (e.g. "axis", "invert")
                        if not isinstance(act_val, (dict, str)):
                            continue
                        kb_str = ""
                        amount = 0
                        vk_val = 0
                        if isinstance(act_val, dict):
                            kb_str = act_val.get("key", "")
                            amount = act_val.get("amount", 0)
                            vk_val = act_val.get("vk", 0)
                        else:
                            kb_str = act_val

                        if kb_str:
                            mods, vk = parse_shortcut(kb_str)
                            if vk_val != 0:
                                vk = vk_val
                            if vk != 0:
                                hk_id = current_id
                                hotkeys_config.append({"id": hk_id, "modifiers": mods, "vk": vk})

                                def make_bm_callback(s_k, a_k, amt):
                                    def cb():
                                        try:
                                            hwnd = win32gui.GetForegroundWindow()
                                            title = win32gui.GetWindowText(hwnd)
                                            if hwnd and ("Adobe Premiere Pro" in title or win32gui.GetClassName(hwnd) == "Premiere Pro"):
                                                self.log_callback(f" Better Motion triggered: {s_k}.{a_k}", THEME_USER_COLORS["info"])
                                                if a_k == "adjust":
                                                    if self.bm_callback:
                                                        self.bm_callback(s_k)
                                                elif a_k == "reset":
                                                    send_better_motion_reset(s_k)
                                                else:
                                                    if s_k == "position":
                                                        amtX = amt if "x_" in a_k else 0
                                                        amtY = amt if "y_" in a_k else 0
                                                        send_better_motion_direct(s_k, amtX, amtY)
                                                    else:
                                                        send_better_motion_direct(s_k, amt)
                                        except Exception as e:
                                            self.log_callback(f" Error in Better Motion: {e}", THEME_USER_COLORS["error"])
                                    return cb

                                callbacks_map[hk_id] = make_bm_callback(sec_key, act_key, amount)
                                current_id += 1

        if hotkeys_config:
            self.hotkey_thread = HotkeyListener(hotkeys_config, callbacks_map, log_callback=self.log_callback)
            self.hotkey_thread.start()
            self.log_callback(f" Native shortcuts enabled ({len(hotkeys_config)} active).", THEME_USER_COLORS["info_text"])
