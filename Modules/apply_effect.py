# Modules/apply_effect.py
import socket
import json
import os
import time
import ctypes
from ctypes import wintypes
import pyautogui

class EffectApplier:
    @staticmethod
    def get_keybind(action_name):
        path = os.path.join("Data", "pr_keybinds.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get(action_name)
            except Exception:
                pass
        
        defaults = {
            "Window > Timelines": "Shift+3",
            "Window > Effect": "Shift+2",
            "Search Find Box": "Shift+F"
        }
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
        except Exception as e:
            print(f"Focus error: {e}")

    @staticmethod
    def apply_effect_to_premiere(match_name, effect_type, alignment="center"):
        # On autorise désormais les transitions !
        # On vérifie de manière souple si le mot "Transition", "FxVideo" ou "FxAudio" est dans le type
        valid = False
        for allowed in ["FxVideo", "FxAudio", "Transition"]:
            if allowed in effect_type:
                valid = True
                break
                
        if not valid:
            raise ValueError(f"Unsupported effect type: {effect_type}")

        EffectApplier.focus_premiere()

        timeline_shortcut = EffectApplier.get_keybind("Window > Timelines")
        EffectApplier.press_shortcut(timeline_shortcut)
        time.sleep(0.2)

        # On inclut l'alignement dans le payload envoyé à Premiere Pro
        payload = {
            "action": "apply_effect",
            "matchName": match_name,
            "type": effect_type,
            "alignment": alignment
        }
        
        try:
            port_path = os.path.join("Data", "port_settings.json")
            tcp_port = 8091
            if os.path.exists(port_path):
                with open(port_path, "r") as f:
                    tcp_port = json.load(f).get("tcp_port", 8091)
                    
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(2.0)
            client.connect(("127.0.0.1", tcp_port))
            client.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            client.close()
        except Exception as e:
            raise Exception(f"Local server unreachable: {e}")