# Core/hotkeys.py
import os
import json
import ctypes
import threading
from ctypes import wintypes
import win32gui

class HotkeyListener(threading.Thread):
    def __init__(self, vk, modifiers, callback):
        super().__init__(daemon=True)
        self.vk = vk
        self.modifiers = modifiers
        self.callback = callback
        self.thread_id = None

    def run(self):
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        user32 = ctypes.windll.user32
        
        if not user32.RegisterHotKey(None, 1, self.modifiers, self.vk):
            return
        
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:  # 0x0312 = WM_HOTKEY
                self.callback()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        
        user32.UnregisterHotKey(None, 1)


class GlobalHotkeyManager:
    def __init__(self, trigger_callback, log_callback):
        self.trigger_callback = trigger_callback
        self.log_callback = log_callback
        self.hotkey_thread = None

    def update_global_hotkey(self):
        kb_path = os.path.join("Data", "pr_keybinds.json")
        shortcut_str = "Ctrl+Space"

        if os.path.exists(kb_path):
            try:
                with open(kb_path, "r") as f:
                    keybinds = json.load(f)
                shortcut_str = keybinds.get("Run Search Bar", "Ctrl+Space")
            except Exception as e:
                self.log_callback(f"❌ Error reading keybinds: {e}", "#ff5555")

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

        if vk == 0: return

        if self.hotkey_thread and self.hotkey_thread.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.hotkey_thread.thread_id, 0x0012, 0, 0)

        def on_trigger():
            try:
                hwnd = win32gui.GetForegroundWindow()
                if hwnd and win32gui.GetClassName(hwnd) == "Premiere Pro":
                    self.trigger_callback()
            except Exception:
                pass

        # Lance le thread d'écoute natif
        self.hotkey_thread = HotkeyListener(vk, modifiers, on_trigger)
        self.hotkey_thread.start()
        self.log_callback(f"⌨️ Native shortcut enabled: {shortcut_str}", "#aaaaaa")