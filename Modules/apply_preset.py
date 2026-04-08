# Modules/apply_preset.py
import os
import time
import json
from Core.paths import get_data_path
from Core.functions.keybinds_send import force_release_modifiers, send_shortcut_multi
import pyautogui
import win32gui
import win32con
import win32api
import win32clipboard
import win32process
import pynput
import ctypes
from PyQt6.QtWidgets import QApplication
from Modules.apply_effect import EffectApplier

class PresetApplier:
    CONFIG_PATH = get_data_path("quickApply_config.json")

    @staticmethod
    def load_config():
        if os.path.exists(PresetApplier.CONFIG_PATH):
            try:
                with open(PresetApplier.CONFIG_PATH, 'r') as f:
                    return json.load(f)
            except: pass
        return None

    @staticmethod
    def save_config(data):
        os.makedirs(get_data_path(), exist_ok=True)
        old_config = PresetApplier.load_config() or {}
        old_config.update(data)
        with open(PresetApplier.CONFIG_PATH, 'w') as f:
            json.dump(old_config, f, indent=4)

    @staticmethod
    def capture_and_validate(delay_ms=200):
        force_release_modifiers()
        EffectApplier.focus_premiere()
        time.sleep(0.3) # On laisse le temps au focus de se stabiliser

        hwnd = win32gui.GetForegroundWindow()
        if "Adobe Premiere Pro" not in win32gui.GetWindowText(hwnd):
            return False, "Premiere Pro is not in the foreground.", None

        mx, my = pyautogui.position()
        rect = win32gui.GetWindowRect(hwnd)
        
        # On récupère tes vrais raccourcis depuis ton JSON
        bind_effect = EffectApplier.get_keybind("Window > Effect")
        bind_search = EffectApplier.get_keybind("Search Find Box")

        config = PresetApplier.load_config() or {}
        delay = config.get("delay_ms", delay_ms) / 1000.0

        # ENVOI DES RACCOURCIS avec vrais Scan Codes
        send_shortcut_multi(bind_effect)
        time.sleep(delay)
        send_shortcut_multi(bind_search)
        time.sleep(delay)

        # Vérification du focus sur la boîte de recherche de Premiere
        try:
            import win32process
            import ctypes
            from ctypes import wintypes
            
            class GUITHREADINFO(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD), ("hwndActive", wintypes.HWND),
                            ("hwndFocus", wintypes.HWND), ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
                            ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND), ("rcCaret", wintypes.RECT)]
            
            tid, _ = win32process.GetWindowThreadProcessId(hwnd)
            gti = GUITHREADINFO()
            gti.cbSize = ctypes.sizeof(GUITHREADINFO)
            
            # Boucle de vérification au cas où l'UI de Premiere est lente
            class_name = "Unknown"
            for _ in range(10):
                ctypes.windll.user32.GetGUIThreadInfo(tid, ctypes.byref(gti))
                focused_hwnd = gti.hwndFocus
                class_name = win32gui.GetClassName(focused_hwnd) if focused_hwnd else ""
                
                if "Edit" in class_name:
                    data = {
                        "mouse_x": mx, "mouse_y": my,
                        "main_x": rect[0], "main_y": rect[1],
                        "main_w": rect[2]-rect[0], "main_h": rect[3]-rect[1],
                        "delay_ms": config.get("delay_ms", delay_ms)
                    }
                    return True, "Capture validated!", data
                time.sleep(0.05)
                
            return False, f"Search bar is not active (Class: {class_name})", None
        except:
            return False, "Error during focus validation.", None

    @staticmethod
    def apply_preset_to_premiere(preset_name, is_quick_apply=False, keep_on_mouse=None, skip_typing=False):
        input_was_blocked = False
        try:
            if not is_quick_apply: return True, f"Preset '{preset_name}' selected."
            
            config = PresetApplier.load_config()
            if not config: return False, "Calibration missing."

            if keep_on_mouse is None:
                keep_on_mouse = config.get("keep_on_mouse", False)

            force_release_modifiers()
            orig_x, orig_y = pyautogui.position()
            EffectApplier.focus_premiere()
            hwnd = win32gui.GetForegroundWindow()

            rect = win32gui.GetWindowRect(hwnd)
            current_x, current_y = rect[0], rect[1]
            current_w, current_h = rect[2] - rect[0], rect[3] - rect[1]
            
            if (abs(current_x - config.get("main_x", 0)) > 10 or abs(current_y - config.get("main_y", 0)) > 10 or
                abs(current_w - config.get("main_w", 0)) > 10 or abs(current_h - config.get("main_h", 0)) > 10):
                return False, "Premiere's size or position has changed. Please recapture."

            delay = config.get("delay_ms", 200) / 1000.0

            send_shortcut_multi(EffectApplier.get_keybind("Window > Effect"))
            time.sleep(delay)
            send_shortcut_multi(EffectApplier.get_keybind("Search Find Box"))
            
            from ctypes import wintypes
            class GUITHREADINFO(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD), ("hwndActive", wintypes.HWND),
                            ("hwndFocus", wintypes.HWND), ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
                            ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND), ("rcCaret", wintypes.RECT)]
            
            tid, _ = win32process.GetWindowThreadProcessId(hwnd)
            gti = GUITHREADINFO()
            gti.cbSize = ctypes.sizeof(GUITHREADINFO)
            
            focus_found = False
            for _ in range(10):
                ctypes.windll.user32.GetGUIThreadInfo(tid, ctypes.byref(gti))
                focused_hwnd = gti.hwndFocus
                class_name = win32gui.GetClassName(focused_hwnd) if focused_hwnd else ""
                if "Edit" in class_name:
                    focus_found = True
                    break
                time.sleep(0.05)
                
            if not focus_found:
                return False, "Search box did not receive focus in time."

            if not skip_typing:
                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(preset_name, win32clipboard.CF_UNICODETEXT)
                    win32clipboard.CloseClipboard()
                except Exception:
                    return False, "Erreur : impossible d'accéder au presse-papier."
                    
                time.sleep(0.01)
                
                send_shortcut_multi("ctrl+v")
                time.sleep(delay)

            ctypes.windll.user32.BlockInput(True)
            input_was_blocked = True
            
            pyautogui.moveTo(config["mouse_x"], config["mouse_y"], duration=0.1)
            pyautogui.mouseDown(button='left')
            time.sleep(0.05)
            pyautogui.moveTo(orig_x, orig_y, duration=0.1)

            if keep_on_mouse:
                return True, "Preset ready to be dropped."
            else:
                time.sleep(0.05)
                pyautogui.mouseUp(button='left')
                return True, "Preset ready - keep on mouse."
        except Exception as e:
            return False, f"Critical apply error: {e}"
        finally:
            if input_was_blocked:
                try:
                    ctypes.windll.user32.BlockInput(False)
                except Exception:
                    pass