# Core/hotkeys.py
import os
import json
import ctypes
import threading
from ctypes import wintypes
import win32gui
from Modules.apply_effect import EffectApplier
from Modules.apply_preset import PresetApplier

class HotkeyListener(threading.Thread):
    def __init__(self, hotkeys, callbacks_map):
        super().__init__(daemon=True)
        self.hotkeys = hotkeys
        self.callbacks_map = callbacks_map
        self.thread_id = None

    def run(self):
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        user32 = ctypes.windll.user32
        
        for hk in self.hotkeys:
            user32.RegisterHotKey(None, hk["id"], hk["modifiers"], hk["vk"])
        
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:  # 0x0312 = WM_HOTKEY
                hk_id = msg.wParam
                if hk_id in self.callbacks_map:
                    self.callbacks_map[hk_id]()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        
        for hk in self.hotkeys:
            user32.UnregisterHotKey(None, hk["id"])

class GlobalHotkeyManager:
    def __init__(self, trigger_callback, log_callback, transition_callback=None):
        self.trigger_callback = trigger_callback
        self.log_callback = log_callback
        self.transition_callback = transition_callback
        self.hotkey_thread = None

    def parse_shortcut(self, shortcut_str):
        modifiers = 0
        vk = 0
        parts = shortcut_str.lower().split('+')
        for part in parts:
            part = part.strip()
            if part == 'ctrl': modifiers |= 0x0002
            elif part == 'shift': modifiers |= 0x0004
            elif part == 'alt': modifiers |= 0x0001
            elif part == 'win': modifiers |= 0x0008
            elif part == 'space': vk = 0x20
            elif len(part) == 1: vk = ord(part.upper())
            else:
                if part.startswith('f') and part[1:].isdigit():
                    vk = 0x70 + int(part[1:]) - 1
        return modifiers, vk

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
                self.log_callback(f"❌ Error reading keybinds: {e}", "#ff5555")

        if self.hotkey_thread and self.hotkey_thread.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.hotkey_thread.thread_id, 0x0012, 0, 0)
            self.hotkey_thread.join(timeout=1.0)

        hotkeys_config = []
        callbacks_map = {}
        
        mods, vk = self.parse_shortcut(search_str)
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
            mods, vk = self.parse_shortcut(ch_str)
            
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
                                if "Transition" in e_type and self.transition_callback:
                                    self.transition_callback(m_name, e_type)
                                elif "Preset" in e_type:
                                    # Force Quick Apply to True when invoked via Hotkey to guarantee execution
                                    res = PresetApplier.apply_preset_to_premiere(m_name, True)
                                    if isinstance(res, tuple):
                                        success, msg = res[0], res[1]
                                    else:
                                        success, msg = True, "Preset applied"

                                    if success:
                                        self.log_callback(f"✅ Preset applied: {m_name}", "#55ff55")
                                    else:
                                        self.log_callback(f"❌ Failed to apply preset: {msg}", "#ff5555")
                                else:
                                    EffectApplier.apply_effect_to_premiere(m_name, e_type)
                                    self.log_callback(f"⚡ Effect applied: {m_name}", "#55ccff")
                        except Exception as e:
                            self.log_callback(f"❌ Error in custom hotkey ({m_name}): {e}", "#ff5555")
                            # Ultimate safety to unlock input if something went wrong inside apply_preset
                            try:
                                import ctypes
                                ctypes.windll.user32.BlockInput(False)
                            except: pass
                    return cb
                
                callbacks_map[hk_id] = make_custom_callback(chk.get("match_name"), chk.get("effect_type"))
                current_id += 1

        if hotkeys_config:
            self.hotkey_thread = HotkeyListener(hotkeys_config, callbacks_map)
            self.hotkey_thread.start()
            self.log_callback(f"⌨️ Native shortcuts enabled ({len(hotkeys_config)} active).", "#aaaaaa")
