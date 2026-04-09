# Modules/apply_effect.py
import socket
import json
import os
import time
import ctypes
from Core.paths import get_data_path
from Core.configs.port_config import DEFAULT_PORTS
from Core.configs.keybinds_config import DEFAULT_KEYBINDS
from ctypes import wintypes
import pyautogui

class EffectApplier:
    @staticmethod
    def force_release_modifiers():
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = (("wVk", wintypes.WORD),
                        ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD),
                        ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)))

        class INPUT(ctypes.Structure):
            class _I(ctypes.Union):
                _fields_ = (("ki", KEYBDINPUT),
                            ("mi", ctypes.c_byte * 28),
                            ("hi", ctypes.c_byte * 32))
            _anonymous_ = ("i",)
            _fields_ = (("type", wintypes.DWORD),
                        ("i", _I))

        # Relâcher Ctrl, Shift, Alt, Win (et leurs variantes)
        for vk in [0x10, 0x11, 0x12, 0x5B, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]:
            scan = user32.MapVirtualKeyW(vk, 0)
            ki = KEYBDINPUT(vk, scan, 0x0002, 0, None) # 0x0002 = KEYUP
            inp = INPUT(type=1, i=INPUT._I(ki=ki))
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    @staticmethod
    def get_keybind(action_name):
        from Core.paths import get_data_path
        path = get_data_path("keybinds.json")
        legacy_path = get_data_path("pr_keybinds.json")

        path_to_load = path
        if not os.path.exists(path) and os.path.exists(legacy_path):
            path_to_load = legacy_path

        if os.path.exists(path_to_load):
            try:
                with open(path_to_load, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get(action_name)
            except Exception:
                pass

        defaults = DEFAULT_KEYBINDS.copy()
        return defaults.get(action_name, "")

    @staticmethod
    def press_shortcut(sequence_str):
        if not sequence_str:
            return
        keys = sequence_str.lower().split('+')
        mapped_keys = [k if k != 'meta' else 'win' for k in keys]
        
        for k in mapped_keys:
            pyautogui.keyDown(k)
        for k in reversed(mapped_keys):
            pyautogui.keyUp(k)

    @staticmethod
    def focus_premiere():
        EffectApplier.force_release_modifiers()
        try:
            user32 = ctypes.windll.user32
            hwnds = []
            def callback(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    if "Adobe Premiere Pro" in buff.value:
                        hwnds.append(hwnd)
                return True
            
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(EnumWindowsProc(callback), 0)
            
            if hwnds:
                hwnd = hwnds[0]
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9) 
                else:
                    user32.ShowWindow(hwnd, 5) 
                    
                user32.SetForegroundWindow(hwnd)
                time.sleep(0.1)
        except Exception:
            pass

    @staticmethod
    def apply_effect_to_premiere(match_name, effect_type, alignment="both"):
        EffectApplier.focus_premiere()
        time.sleep(0.1)

        # Le plugin JS attend EXPLICITEMENT ces chaines dans sa condition includes()
        # Ne PAS changer en 'video' ou 'transition'.
        payload = {
            "action": "apply_effect",
            "matchName": match_name,
            "type": effect_type,
            "alignment": alignment
        }
        
        try:
            port_path = get_data_path("port_settings.json")
            tcp_port = DEFAULT_PORTS["tcp_port"]
            if os.path.exists(port_path):
                with open(port_path, "r") as f:
                    tcp_port = json.load(f).get("tcp_port", DEFAULT_PORTS["tcp_port"])
                    
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(2.0)
            client.connect(("127.0.0.1", tcp_port))
            client.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            client.close()
        except Exception as e:
            raise Exception(f"Local server unreachable: {e}")