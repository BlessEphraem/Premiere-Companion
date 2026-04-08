# GUI/Widgets/BetterMotion.py
import time
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor
from Core.theme_qss import THEME_USER_COLORS
from Core.functions.server import send_to_plugin

def _read_live_motion_setting():
    from Core.paths import get_data_path
    path = get_data_path("betterMotion_config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("live_preview", False)
        except:
            pass
    return False

class BetterMotionOverlay(QWidget):
    """
    Base class for Better Motion floating HUD.
    Features:
    - Always on top, frameless, mouse/keyboard grabbed.
    - Tracks mouse deltas and sends to Premiere via WebSocket.
    - ESC to cancel, Enter/LMB to confirm.
    """
    def __init__(self, prop_name):
        super().__init__()
        self.prop_name = prop_name
        self.initial_value = None
        self.live_mode = _read_live_motion_setting()
        self._axis = None
        self._invert = False
        self._load_axis_config(prop_name)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # UI Setup
        self.init_ui()

        self.orig_cursor_pos = QCursor.pos()
        self.center_pos = self.get_screen_center()
        self.last_mouse_pos = self.center_pos
        self.is_ready = False

        self.delta_x = 0
        self.delta_y = 0

        self.last_send_time = 0
        self.send_interval = 1.0 / 20.0  # Reduced from 30fps to 20fps to prevent overloading Premiere

        send_to_plugin({
            "action": "better_motion",
            "status": "start",
            "prop": self.prop_name,
            "live": self.live_mode
        })

    def init_ui(self):
        from Core.theme_qss import get_bettermotion_overlay_style
        self.container = QWidget(self)
        self.container.setObjectName("BetterMotionContainer")
        self.container.setStyleSheet(get_bettermotion_overlay_style(THEME_USER_COLORS))
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.title_label = QLabel(f"Adjusting {self.prop_name.capitalize()}")
        self.title_label.setStyleSheet(f"color: {THEME_USER_COLORS.get('accent', '#FF1796')}; font-size: 24px; font-weight: bold; background: transparent; border: none;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.value_label = QLabel("—")
        self.value_label.setStyleSheet("color: white; font-size: 32px; font-weight: bold; background: transparent; border: none;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        self.desc_label = QLabel("Move mouse to change value")
        self.desc_label.setStyleSheet(f"color: {THEME_USER_COLORS.get('text_subtle', '#a1a1aa')}; font-size: 15px; background: transparent; border: none;")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.desc_label)

        self.sub_label = QLabel("Click or Enter to Confirm | Esc to Cancel")
        self.sub_label.setStyleSheet(f"color: {THEME_USER_COLORS.get('text_subtle', '#a1a1aa')}; font-size: 13px; background: transparent; border: none;")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_label)

        self.container.adjustSize()
        self.setFixedSize(self.container.size())
        self.center_on_screen()

    def _load_axis_config(self, prop):
        from Core.paths import get_data_path
        path = get_data_path("betterMotion_config.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f).get(prop, {})
                    self._axis = cfg.get("axis", "X")
                    self._invert = cfg.get("invert", False)
            except: pass

    def get_screen_center(self):
        screen = QApplication.primaryScreen().geometry()
        return screen.center()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())

    def showEvent(self, event):
        super().showEvent(event)
        self.setMouseTracking(True)
        self.activateWindow()
        self.setFocus()

    def set_initial_value(self, value):
        self.initial_value = value
        if not self.is_ready:
            QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
            QCursor.setPos(self.center_pos)
            self.grabMouse()
            self.grabKeyboard()
            self.is_ready = True
        self._update_value_display()

    def _update_value_display(self):
        if self.initial_value is None:
            self.value_label.setText("—")
            return

        accent = THEME_USER_COLORS["accent"]
        info = THEME_USER_COLORS["info"]

        if self.prop_name == "position":
            # value is like {x: 0.5, y: 0.5}
            orig_x = self.initial_value.get("x", 0.5)
            orig_y = self.initial_value.get("y", 0.5)
            
            # Use seq dims for pixel-like display if possible (hardcoded for now)
            # or just show offset
            self.value_label.setText(
                f"<span style='color:{accent}'>{self.delta_x}</span>"
                f"<span style='color:{THEME_USER_COLORS['text_subtle']}'> → </span>"
                f"<span style='color:{info}'>{self.delta_y}</span>"
            )
        else:
            # scalar value
            try:
                cur = float(self.initial_value)
                new_v = round(cur + self.delta_x, 2)
                self.value_label.setText(
                    f"<span style='color:{accent}'>{cur}</span>"
                    f"<span style='color:{THEME_USER_COLORS['text_subtle']}'> → </span>"
                    f"<span style='color:{info}'>{new_v}</span>"
                )
            except:
                self.value_label.setText(str(self.delta_x))

    def mouseMoveEvent(self, event):
        if not getattr(self, 'is_ready', False):
            return
        pos = event.globalPosition().toPoint()
        diff = pos - self.center_pos
        if diff.manhattanLength() > 0:
            dx = diff.x()
            dy = diff.y()
            
            if self._axis == "Y":
                # Swap roles
                dx, dy = dy, dx
            
            if self._invert:
                dx = -dx
                dy = -dy

            self.delta_x += dx
            self.delta_y += dy
            
            self._update_value_display()
            QCursor.setPos(self.center_pos)

            now = time.time()
            if now - self.last_send_time >= self.send_interval:
                self.send_update()
                self.last_send_time = now

    def send_update(self):
        if not self.live_mode: return
        send_to_plugin({
            "action": "better_motion",
            "status": "moving",
            "deltaX": self.delta_x,
            "deltaY": self.delta_y
        })

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.confirm()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.confirm()
        super().keyPressEvent(event)

    def confirm(self):
        self.cleanup(confirm=True)

    def cancel(self):
        self.cleanup(confirm=False)

    def cleanup(self, confirm=False):
        self.releaseMouse()
        self.releaseKeyboard()
        QApplication.restoreOverrideCursor()
        QCursor.setPos(self.orig_cursor_pos)

        send_to_plugin({
            "action": "better_motion",
            "status": "end",
            "prop": self.prop_name,
            "confirm": confirm,
            "deltaX": self.delta_x,
            "deltaY": self.delta_y
        })
        self.close()
        
        # Allow global hotkeys again
        from Core.functions.better_motion import clear_active_overlay
        clear_active_overlay()

class BetterTransformOverlay(BetterMotionOverlay):
    """
    Combined Position/Rotation/Scale overlay.
    - Default mode: position (move mouse freely)
    - Hold RMB: switch to rotation mode
    - Hold MMB: switch to scale mode
    - Release RMB/MMB: return to position mode
    - LMB / Enter / Space: confirm & exit
    - Esc: cancel current mode & exit
    Axis and invert for Scale/Rotation are read from betterMotion_config.json.
    """
    def __init__(self):
        super().__init__("position")  # base loads axis config for "position"
        self.current_mode = "position"
        self._update_mode_display("position")

    def _switch_mode(self, new_prop):
        # Commit changes for the current mode
        send_to_plugin({
            "action": "better_motion",
            "status": "end",
            "prop": self.prop_name,
            "confirm": True,
            "deltaX": self.delta_x,
            "deltaY": self.delta_y
        })
        # Reset delta accumulator and reload axis config for new mode
        self.delta_x = 0
        self.delta_y = 0
        self.prop_name = new_prop
        self.current_mode = new_prop
        self.initial_value = None
        self.value_label.setText("—")
        self._load_axis_config(new_prop)  # update self._axis / self._invert
        self._update_mode_display(new_prop)
        
        # Ask for the new property's initial value
        send_to_plugin({
            "action": "better_motion",
            "status": "start",
            "prop": new_prop,
            "live": self.live_mode
        })

    def _update_mode_display(self, prop):
        self.title_label.setText(f"Adjusting {prop.capitalize()}")
        self.title_label.style().unpolish(self.title_label)
        self.title_label.style().polish(self.title_label)

    def mousePressEvent(self, event):
        btn = event.button()
        if btn == Qt.MouseButton.RightButton:
            if self.current_mode != "rotation":
                self._switch_mode("rotation")
        elif btn == Qt.MouseButton.MiddleButton:
            if self.current_mode != "scale":
                self._switch_mode("scale")
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        btn = event.button()
        if btn == Qt.MouseButton.RightButton:
            if self.current_mode == "rotation":
                self._switch_mode("position")
        elif btn == Qt.MouseButton.MiddleButton:
            if self.current_mode == "scale":
                self._switch_mode("position")
        super().mouseReleaseEvent(event)
