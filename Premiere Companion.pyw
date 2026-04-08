# Premiere Companion.pyw
import sys
import os
import ctypes
import time
import traceback

# Configuration du log de crash pour voir l'erreur
def log_crash(e):
    with open("crash_log.txt", "w") as f:
        f.write(str(e) + "\n")
        f.write(traceback.format_exc())

# On s'assure d'être dans le bon répertoire avant d'importer nos modules
if hasattr(sys, '_MEIPASS'):
    current_dir = os.path.dirname(sys.executable)
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Debug log file
DEBUG_LOG = os.path.join(current_dir, "debug_startup.log")

def debug_log(msg):
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except: pass
    print(f"[DEBUG] {msg}")

try:
    from Core.configs.betterMotion_config import DEFAULT_BM_CONFIG
    from Core.configs.commands_config import DEFAULT_COMMANDS_CONFIG
    from Core.configs.priority_ignore_config import DEFAULT_PRIORITY_IGNORE_CONFIG
    from Core.configs.cmd_actions_config import DEFAULT_CMD_ACTIONS_CONFIG
    from Core.theme_qss import THEME_USER_COLORS, generate_theme_qss
    from Core.paths import get_data_path, get_app_path
    
    WINDOW_TITLE = THEME_USER_COLORS["app_title"]
    LOCK_FILE = "premiere_companion.lock"

    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    if not is_admin():
        if hasattr(sys, '_MEIPASS'):
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1)
        os._exit(0)

    # Imports lourds après UAC
    from GUI.Pages.effects_page import EffectsPage
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon, QFontDatabase, QFont
    import json

    # Centraliser pycache
    CACHE_DIR = get_data_path("__pycache__")
    if not os.path.exists(CACHE_DIR):
        try: os.makedirs(CACHE_DIR)
        except: pass
    sys.pycache_prefix = os.path.abspath(CACHE_DIR)

except Exception as e:
    log_crash(e)
    sys.exit(1)


def _is_process_running(pid):
    try:
        PROCESS_QUERY_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, int(pid))
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
    except:
        pass
    return False


def _activate_window_by_title():
    try:
        SW_RESTORE = 9
        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        GetWindowTextW = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible
        IsIconic = ctypes.windll.user32.IsIconic
        ShowWindow = ctypes.windll.user32.ShowWindow
        SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
        BringWindowToTop = ctypes.windll.user32.BringWindowToTop
        
        found_hwnd = None
        
        def enum_callback(hwnd, lParam):
            nonlocal found_hwnd
            if IsWindowVisible(hwnd):
                length = GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buff, length + 1)
                    if WINDOW_TITLE in buff.value:
                        if IsIconic(hwnd):
                            ShowWindow(hwnd, SW_RESTORE)
                        found_hwnd = hwnd
            return True
        
        EnumWindows(EnumWindowsProc(enum_callback), 0)
        if found_hwnd:
            time.sleep(0.05)
            BringWindowToTop(found_hwnd)
            SetForegroundWindow(found_hwnd)
    except: pass


def _check_existing_instance():
    lock_path = os.path.join(get_data_path(), LOCK_FILE)
    if os.path.exists(lock_path):
        try:
            with open(lock_path, 'r') as f:
                old_pid = f.read().strip()
            if old_pid and _is_process_running(old_pid):
                _activate_window_by_title()
                return True
            else:
                try: os.remove(lock_path)
                except: pass
        except: pass
    return False


def _write_lock():
    lock_path = os.path.join(get_data_path(), LOCK_FILE)
    try:
        with open(lock_path, 'w') as f:
            f.write(str(os.getpid()))
    except: pass


def get_theme_colors():
    defaults = THEME_USER_COLORS.copy()
    theme_path = get_data_path("theme.json")
    if not os.path.exists(theme_path):
        os.makedirs(os.path.dirname(theme_path), exist_ok=True)
        with open(theme_path, "w", encoding="utf-8") as f:
            json.dump(defaults, f, indent=4)
    else:
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
        except: pass
    return defaults


CONFIG_DEFAULTS = {
    "settings.json": {"console_visible": True},
    "port_settings.json": {"auto_connect": False},
    "keybinds.json": {
        "Window > Timelines": "Shift+3",
        "Window > Effect": "Shift+2",
        "Search Find Box": "Shift+F"
    },
    "betterMotion_config.json": DEFAULT_BM_CONFIG,
    "commands_config.json": DEFAULT_COMMANDS_CONFIG,
    "priority_ignore_config.json": DEFAULT_PRIORITY_IGNORE_CONFIG,
    "cmd_actions_config.json": DEFAULT_CMD_ACTIONS_CONFIG,
    "quickApply_config.json": {"quick_apply_enabled": False},
    "searchbar_config.json": {
        "max_items": 100,
        "max_recent": 3,
        "window_width": 600,
        "window_height": 420,
        "font_size": 15,
        "bg_opacity": 0.85,
        "blur_background": False,
        "apply_last_on_empty_enter": False,
        "apply_last_without_name_enter": False
    }
}


def ensure_config_defaults():
    for filename, defaults in CONFIG_DEFAULTS.items():
        path = get_data_path(filename)
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(defaults, f, indent=4)
        else:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                updated = False
                for key, value in defaults.items():
                    if key not in data:
                        data[key] = value
                        updated = True
                if updated:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
            except: pass


def load_custom_fonts():
    base_dir = get_app_path()
    font_path = os.path.join(base_dir, "Assets", "Satoshi-Variable.ttf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
    return None


def main():
    ensure_config_defaults()
    if _check_existing_instance():
        sys.exit(0)
    _write_lock()

    myappid = 'ephraem.premierecompanion'
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except: pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Load icon
    base_dir = get_app_path()
    icon_path = os.path.join(base_dir, "Assets", "icons", "icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(base_dir, "icon.ico")

    app_icon = None
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    # Font rendering
    font = QFont()
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)

    # Load custom font
    loaded_font = load_custom_fonts()

    # Get theme colors
    colors = get_theme_colors()

    # Generate QSS
    dynamic_qss = generate_theme_qss(colors, loaded_font)
    app.setStyleSheet(dynamic_qss)

    # --- SPLASH SCREEN ---
    from GUI.Widgets.splash import SplashScreen
    splash = SplashScreen(colors)
    splash.show()
    app.processEvents()

    # Initialize window
    splash.update_progress(90, "Initializing")
    window = EffectsPage()
    window.setWindowTitle(WINDOW_TITLE)
    if app_icon:
        window.setWindowIcon(app_icon)

    splash.update_progress(100, "Ready!")
    splash.close()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
