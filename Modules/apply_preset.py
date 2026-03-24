# Modules/apply_preset.py
import os
import time
import json
from Core.paths import get_data_path
import pyautogui
import win32gui
import win32con
import win32api
import pynput
import ctypes
from PyQt6.QtWidgets import QApplication
from Modules.apply_effect import EffectApplier

class PresetApplier:
    CONFIG_PATH = get_data_path("quick_apply_config.json")

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

        # Relâcher Ctrl, Shift, Alt, Win (et leurs variantes Gauche/Droite pour être sûr)
        for vk in [0x10, 0x11, 0x12, 0x5B, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]:
            scan = user32.MapVirtualKeyW(vk, 0)
            ki = KEYBDINPUT(vk, scan, 0x0002, 0, None) # 0x0002 = KEYUP
            inp = INPUT(type=1, i=INPUT._I(ki=ki))
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    @staticmethod
    def send_shortcut(key_str):
        if not key_str: return
        import ctypes
        from ctypes import wintypes
        import time

        user32 = ctypes.windll.user32

        # Structures Windows natives pour SendInput
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

        # Mapping vers les Virtual Key Codes (VK)
        key_map = {
            "f4": 0x73, "f8": 0x77, "f": 0x46, "v": 0x56,
            "space": 0x20, "enter": 0x0D,
            "shift": 0x10, "ctrl": 0x11, 
            "alt": 0x12, "win": 0x5B
        }
        
        parts = [p.strip().lower() for p in key_str.split('+')]
        
        vks = []
        for p in parts:
            if p in key_map:
                vks.append(key_map[p])
            elif len(p) == 1:
                vks.append(ord(p.upper()))

        def send_key(vk, is_down):
            scan = user32.MapVirtualKeyW(vk, 0)
            flags = 0
            if not is_down:
                flags |= 0x0002 # KEYEVENTF_KEYUP
                
            ki = KEYBDINPUT(vk, scan, flags, 0, None)
            inp = INPUT(type=1, i=INPUT._I(ki=ki))
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

        # Envoi matériel atomique - DELAYS SÉCURISÉS POUR PREMIERE
        for vk in vks:
            send_key(vk, True)
            time.sleep(0.02)
        
        time.sleep(0.05)
        
        for vk in reversed(vks):
            send_key(vk, False)
            time.sleep(0.02)

    @staticmethod
    def capture_and_validate(delay_ms=200):
        PresetApplier.force_release_modifiers()
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

        # 🚀 ENVOI DES RACCOURCIS avec vrais Scan Codes
        PresetApplier.send_shortcut(bind_effect)
        time.sleep(delay)
        PresetApplier.send_shortcut(bind_search)
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
    def apply_preset_to_premiere(preset_name, is_quick_apply=False):
        try:
            if not is_quick_apply: return True, f"Preset '{preset_name}' selected."
            
            config = PresetApplier.load_config()
            if not config: return False, "Calibration missing."

            PresetApplier.force_release_modifiers()
            orig_x, orig_y = pyautogui.position()
            EffectApplier.focus_premiere()
            hwnd = win32gui.GetForegroundWindow()

            # Validation de la taille et position de Premiere
            rect = win32gui.GetWindowRect(hwnd)
            current_x, current_y = rect[0], rect[1]
            current_w, current_h = rect[2] - rect[0], rect[3] - rect[1]
            
            if (abs(current_x - config.get("main_x", 0)) > 10 or abs(current_y - config.get("main_y", 0)) > 10 or
                abs(current_w - config.get("main_w", 0)) > 10 or abs(current_h - config.get("main_h", 0)) > 10):
                return False, "Premiere's size or position has changed. Please recapture."

            # Respect strict du délai défini par l'utilisateur
            delay = config.get("delay_ms", 200) / 1000.0

            # 🚀 SEQUENCE D'APPLICATION NATIVE
            PresetApplier.send_shortcut(EffectApplier.get_keybind("Window > Effect"))
            time.sleep(delay)
            PresetApplier.send_shortcut(EffectApplier.get_keybind("Search Find Box"))
            time.sleep(delay)

            # Copier le nom dans le presse-papier de manière thread-safe
            import win32clipboard
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(preset_name, win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
            except Exception as e:
                print(f"Clipboard error: {e}")
                
            time.sleep(0.02)
            
            # Coller
            PresetApplier.send_shortcut("ctrl+v")
            # Délai critique pour laisser Premiere filtrer la liste après le coller
            time.sleep(delay)

            # Déplacement et Drag & Drop avec blocage matériel
            try:
                # 🔒 BLOQUE les entrées (souris + clavier) de l'utilisateur
                ctypes.windll.user32.BlockInput(True)
                
                # Mouvements rapides mais sûrs pour que Premiere enregistre le Drag (0.1s au lieu de 0.0s)
                pyautogui.moveTo(config["mouse_x"], config["mouse_y"], duration=0.1)
                pyautogui.mouseDown(button='left')
                time.sleep(0.05)
                pyautogui.moveTo(orig_x, orig_y, duration=0.1)
                # On ne relâche pas le bouton pour laisser le preset accroché à la souris
                
            except Exception as e:
                return False, f"Input control error: {e}"
            finally:
                # 🔓 DÉBLOQUE TOUJOURS les entrées
                ctypes.windll.user32.BlockInput(False)

            return True, "Preset ready to be dropped."
        except Exception as e:
            try: ctypes.windll.user32.BlockInput(False)
            except: pass
            return False, f"Critical apply error: {e}"