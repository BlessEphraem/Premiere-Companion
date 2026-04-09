# GUI/Widgets/BetterMotion.py
import time
import json
import os
import ctypes
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QCursor
from Core.theme_qss import THEME_USER_COLORS
from Core.functions.server import send_to_plugin

user32 = ctypes.windll.user32

_HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t)

class _MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("ptX",        ctypes.c_long),
        ("ptY",        ctypes.c_long),
        ("mouseData",  ctypes.c_ulong),
        ("flags",      ctypes.c_ulong),
        ("time",       ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_ulong),
    ]

LLMHF_INJECTED = 0x00000001
WH_MOUSE_LL    = 14

class _MSG(ctypes.Structure):
    """Minimal Win32 MSG struct for nativeEvent parsing."""
    _fields_ = [
        ("hwnd",    ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam",  ctypes.c_size_t),
        ("lParam",  ctypes.c_ssize_t),
        ("time",    ctypes.c_ulong),
        ("ptx",     ctypes.c_long),
        ("pty",     ctypes.c_long),
    ]

def _read_live_motion_setting():
    from Core.paths import get_data_path
    path = get_data_path("betterMotion_config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("live_motion", False)
        except: pass
    return False

class BetterMotionOverlay(QWidget):
    def __init__(self, prop_name):
        super().__init__()
        self.prop_name = prop_name
        self.initial_value = None
        self.live_mode = True
        self._axis, self._invert = "X", False
        self._load_axis_config(prop_name)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 1);")
        self._cleaned_up = False
        self._btn_lmb = False
        self._btn_rmb = False
        self._btn_mmb = False
        
        self.init_ui()

        self.orig_cursor_pos = QCursor.pos()
        self.is_ready = False
        self.delta_x, self.delta_y = 0, 0
        self.last_send_time = 0

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_loop)

        send_to_plugin({"action": "better_motion", "status": "start", "prop": self.prop_name, "live": True})

    def init_ui(self):
        from Core.theme_qss import get_bettermotion_overlay_style
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 50, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.container = QWidget(self)
        self.container.setStyleSheet(get_bettermotion_overlay_style(THEME_USER_COLORS))
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.title_label = QLabel(f"Adjusting {self.prop_name.capitalize()}")
        self.title_label.setStyleSheet(f"color: {THEME_USER_COLORS['accent']}; font-size: 24px; font-weight: bold; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.value_label = QLabel("—")
        self.value_label.setStyleSheet("color: white; font-size: 32px; font-weight: bold; background: transparent;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        self.sub_label = QLabel("Click to Confirm | Esc to Cancel")
        self.sub_label.setStyleSheet("color: #a1a1aa; font-size: 13px; background: transparent;")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_label)

        main_layout.addWidget(self.container)

    def _load_axis_config(self, prop):
        from Core.paths import get_data_path
        path = get_data_path("betterMotion_config.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f).get(prop, {})
                    axis_val = str(cfg.get("axis", "X")).lower()
                    self._axis = "Y" if axis_val in ("y", "vertical") else "X"
                    self._invert = bool(cfg.get("invert", False))
            except: pass

    def showEvent(self, event):
        super().showEvent(event)
        screen = self.screen() or QApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo)
        self.center_pos = geo.center()
        # Defer capture setup — showFullScreen() posts events that would release an
        # immediate grab.  Wait for the event loop to process the state change first.
        QTimer.singleShot(0, self._activate_capture)

    def _activate_capture(self):
        if self._cleaned_up:
            return
        self.showFullScreen()
        self.activateWindow()
        self.raise_()
        hwnd = int(self.winId())
        user32.SetForegroundWindow(hwnd)
        QCursor.setPos(self.center_pos)
        self._install_input_block()
        self.poll_timer.start(10)

    def _hide_cursor(self):
        """Replace the system arrow cursor with an invisible 1×1 cursor globally.
        This works regardless of which window owns WM_SETCURSOR."""
        if getattr(self, '_cursor_hidden', False):
            return
        AND_mask = (ctypes.c_ubyte * 4)(0xFF, 0xFF, 0xFF, 0xFF)
        XOR_mask = (ctypes.c_ubyte * 4)(0x00, 0x00, 0x00, 0x00)
        hInst = ctypes.windll.kernel32.GetModuleHandleW(None)
        blank = user32.CreateCursor(hInst, 0, 0, 1, 1, AND_mask, XOR_mask)
        if blank:
            user32.SetSystemCursor(blank, 32512)  # OCR_NORMAL — SetSystemCursor takes ownership of blank
            self._cursor_hidden = True

    def _restore_cursor(self):
        """Restore all system cursors to their theme defaults."""
        if getattr(self, '_cursor_hidden', False):
            ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0)  # SPI_SETCURSORS
            self._cursor_hidden = False

    def _install_input_block(self):
        """Block ALL mouse events from reaching other applications via WH_MOUSE_LL.
        The hook fires after Windows updates the cursor position, so QCursor.pos()
        and GetAsyncKeyState still work — only external apps are blocked."""
        def _cb(nCode, wParam, lParam):
            if nCode >= 0:
                # Track button state here — GetAsyncKeyState won't see events blocked by the hook
                if   wParam == 0x0201: self._btn_lmb = True   # WM_LBUTTONDOWN
                elif wParam == 0x0202: self._btn_lmb = False  # WM_LBUTTONUP
                elif wParam == 0x0204: self._btn_rmb = True   # WM_RBUTTONDOWN
                elif wParam == 0x0205: self._btn_rmb = False  # WM_RBUTTONUP
                elif wParam == 0x0207: self._btn_mmb = True   # WM_MBUTTONDOWN
                elif wParam == 0x0208: self._btn_mmb = False  # WM_MBUTTONUP
                if wParam != 0x0200:   # block everything except WM_MOUSEMOVE
                    return 1
            return user32.CallNextHookEx(None, nCode, wParam, lParam)
        self._hook_proc = _HOOKPROC(_cb)
        self._hook_handle = user32.SetWindowsHookExW(WH_MOUSE_LL, self._hook_proc, None, 0)

    def _remove_input_block(self):
        if getattr(self, '_hook_handle', None):
            user32.UnhookWindowsHookEx(self._hook_handle)
            self._hook_handle = None
            self._hook_proc = None

    def set_initial_value(self, value):
        self.initial_value = value
        if not self.is_ready:
            self._hide_cursor()
            self.grabMouse()
            self.is_ready = True
        self._update_value_display()

    def _update_value_display(self):
        if self.initial_value is None: return
        accent, info = THEME_USER_COLORS["accent"], THEME_USER_COLORS["info"]
        if self.prop_name == "position":
            self.value_label.setText(f"<span style='color:{accent}'>{int(self.delta_x)}</span> <span style='color:grey'>→</span> <span style='color:{info}'>{int(self.delta_y)}</span>")
        else:
            try:
                nv = round(float(self.initial_value) + self.delta_x, 2)
                self.value_label.setText(f"<span style='color:{accent}'>{self.initial_value}</span> <span style='color:grey'>→</span> <span style='color:{info}'>{nv}</span>")
            except: self.value_label.setText(str(int(self.delta_x)))

    def poll_loop(self):
        if self._cleaned_up:
            return

        if user32.GetAsyncKeyState(0x1B) & 0x8000:
            self.cancel()
            return

        curr = QCursor.pos()
        dx, dy = curr.x() - self.center_pos.x(), curr.y() - self.center_pos.y()
        
        if dx != 0 or dy != 0:
            QCursor.setPos(self.center_pos)
            if self.is_ready:
                if self._axis == "Y": dx, dy = dy, dx
                if self._invert: dx, dy = -dx, -dy
                shift = user32.GetAsyncKeyState(0x10) & 0x8000
                ctrl = user32.GetAsyncKeyState(0x11) & 0x8000
                mult = 2.0 if shift else (0.25 if ctrl else 1.0)
                self.delta_x += dx * mult
                self.delta_y += dy * mult
                self._update_value_display()
                if time.time() - self.last_send_time >= 0.03:
                    send_to_plugin({"action": "better_motion", "status": "moving", "deltaX": int(self.delta_x), "deltaY": int(self.delta_y)})
                    self.last_send_time = time.time()

        if not isinstance(self, BetterTransformOverlay):
            if self._btn_lmb:
                self.confirm()

    def cleanup(self, confirm=False):
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self.poll_timer.stop()
        try:
            self.releaseMouse()
        except Exception:
            pass
        self._remove_input_block()
        self._restore_cursor()
        QCursor.setPos(self.orig_cursor_pos)
        send_to_plugin({"action": "better_motion", "status": "moving", "deltaX": int(self.delta_x), "deltaY": int(self.delta_y)})
        send_to_plugin({"action": "better_motion", "status": "end", "prop": self.prop_name, "confirm": confirm, "deltaX": int(self.delta_x), "deltaY": int(self.delta_y)})
        self.close()
        QTimer.singleShot(10, self._final_clear)

    def _final_clear(self):
        try:
            from Core.functions.better_motion import clear_active_overlay
            clear_active_overlay()
        except: pass

    def confirm(self): self.cleanup(confirm=True)
    def cancel(self): self.cleanup(confirm=False)

class BetterTransformOverlay(BetterMotionOverlay):
    def __init__(self):
        super().__init__("position")
        self.current_mode = "position"
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def contextMenuEvent(self, event):
        event.accept()

    def mousePressEvent(self, event):
        event.accept()

    def mouseReleaseEvent(self, event):
        event.accept()

    def poll_loop(self):
        super().poll_loop()
        if self._cleaned_up:
            return
        lmb = self._btn_lmb
        rmb = self._btn_rmb
        mmb = self._btn_mmb

        if rmb and self.current_mode != "rotation":
            self._switch_mode("rotation")
        elif mmb and self.current_mode != "scale":
            self._switch_mode("scale")
        elif not rmb and not mmb and self.current_mode != "position":
            self._switch_mode("position")
        elif lmb:
            self.confirm()

    def _switch_mode(self, new_prop):
        if self.prop_name == new_prop: return
        send_to_plugin({"action": "better_motion", "status": "moving", "deltaX": int(self.delta_x), "deltaY": int(self.delta_y)})
        send_to_plugin({"action": "better_motion", "status": "end", "prop": self.prop_name, "confirm": True, "deltaX": int(self.delta_x), "deltaY": int(self.delta_y)})
        self.is_ready = False
        self.delta_x, self.delta_y = 0, 0
        self.prop_name, self.current_mode = new_prop, new_prop
        self.initial_value = None
        self.value_label.setText("—")
        self._load_axis_config(new_prop)
        self.title_label.setText(f"Adjusting {new_prop.capitalize()}")
        send_to_plugin({"action": "better_motion", "status": "start", "prop": self.prop_name, "live": True})
