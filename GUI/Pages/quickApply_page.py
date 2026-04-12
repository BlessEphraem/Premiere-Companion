# GUI/quickApply_window.py
import os
import time
import json
import win32gui
import win32con
import win32api
import pyautogui
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QMessageBox, QSlider)
from PyQt6.QtCore import Qt, QTimer
from Modules.apply_preset import PresetApplier
from Core.functions.keybinds_send import send_shortcut_multi
from Modules.apply_effect import EffectApplier
from Core.functions.icon_loader import icon
from Core.theme_qss import THEME_USER_COLORS, THEME_SPACING

class QuickApplyWizard(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setModal(True)
        self.captured_data = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(THEME_SPACING["spacing_element"])

        config = PresetApplier.load_config() or {}

        # --- PREMIERE KEYBINDS SECTION ---
        from GUI.Widgets.premiereKeybindsWidget import PremiereKeybindsWidget
        self.keybinds_section = PremiereKeybindsWidget(self.main_window)
        layout.addWidget(self.keybinds_section)

        # --- LATENCY SECTION ---
        layout.addWidget(QLabel("<b>1. Latency (ms)</b>"))
        self.lbl_delay = QLabel(f"Delay : {config.get('delay_ms', 200)} ms")
        layout.addWidget(self.lbl_delay)

        self.slider_delay = QSlider(Qt.Orientation.Horizontal)
        self.slider_delay.setRange(50, 1000)
        self.slider_delay.setValue(config.get("delay_ms", 200))
        self.slider_delay.valueChanged.connect(lambda v: self.lbl_delay.setText(f"Delay : {v} ms"))
        layout.addWidget(self.slider_delay)

        # --- CALIBRATION SECTION ---
        layout.addWidget(QLabel("<b>2. Mouse Position Calibration (Edit1 Check)</b>"))
        lbl_info = QLabel("<b>Search for a unique preset, press 'Capture', and move your mouse above the Preset icon</b>"
                          "<br><b>It will : Focus Premiere > Focus Effects Panel > Focus Search Box.</b>")
        lbl_info.setWordWrap(True)
        lbl_info.setObjectName("QuickApplyInfoLabel")
        layout.addWidget(lbl_info)

        self.btn_capture = QPushButton()
        self.btn_capture.setIcon(icon("rocket"))
        self.btn_capture.setText(" Start Calibration (5s)")
        self.btn_capture.clicked.connect(self.start_capture)
        layout.addWidget(self.btn_capture)

        # --- Retrieve label state ---
        self.lbl_coord = QLabel("Status : Waiting...")
        self.lbl_coord.setObjectName("CoordLabel")
        
        btn_layout = QHBoxLayout()
        self.btn_test = QPushButton()
        self.btn_test.setIcon(icon("circle"))
        self.btn_test.setText(" Test Position")
        self.btn_test.setFixedWidth(THEME_SPACING["width_button_medium"])
        self.btn_test.clicked.connect(self.test_position)
        self.btn_test.setEnabled(False)
        
        # Saved Mouse Data Verification
        if "mouse_x" in config and "mouse_y" in config:
            self.captured_data = config
            self.lbl_coord.setText(f" Ready ! Coords : {config['mouse_x']}, {config['mouse_y']}")
            self.lbl_coord.setProperty("state", "saved")
            self.btn_test.setEnabled(True)
        else:
            self.lbl_coord.setProperty("state", "undefined")

        current_keep = config.get("keep_on_mouse", False)
        
        # --- KEEP ON MOUSE SECTION ---
        layout.addWidget(QLabel("<b>3. Preset Release Mode</b>"))
        lbl_keep_info = QLabel("Choose what happens after preset is attached to mouse:")
        lbl_keep_info.setObjectName("QuickApplyInfoLabel")
        layout.addWidget(lbl_keep_info)
        
        hbox_keep = QHBoxLayout()
        hbox_keep.setSpacing(THEME_SPACING["spacing_element"])
        self.btn_toggle_keep = QPushButton()
        self.btn_toggle_keep.setObjectName("Toggle")
        
        self.btn_toggle_keep.setProperty("qa_state", "enabled" if current_keep else "disabled")
        self.btn_toggle_keep.style().unpolish(self.btn_toggle_keep)
        self.btn_toggle_keep.style().polish(self.btn_toggle_keep)
        self.update_keep_ui()
        
        self.btn_toggle_keep.clicked.connect(self.toggle_keep_mode)
        
        hbox_keep.addWidget(self.btn_toggle_keep)
        hbox_keep.addStretch()
        layout.addLayout(hbox_keep)

        layout.addWidget(self.lbl_coord)

        btn_save = QPushButton()
        btn_save.setIcon(icon("save"))
        btn_save.setText(" Save Configuration")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_config)
        
        btn_layout.addWidget(self.btn_test)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def start_capture(self):
        self.btn_capture.setText("Calibration in 5s...")
        self.btn_capture.setEnabled(False)
        QTimer.singleShot(5000, self.perform_capture)

    def perform_capture(self):
        # 1. Make Premiere Active
        EffectApplier.focus_premiere()
        time.sleep(0.5)

        # 2. Retrieve input from keymap
        eff_key = EffectApplier.get_keybind("Window > Effect")
        find_key = EffectApplier.get_keybind("Search Find Box")
        
        delay = self.slider_delay.value() / 1000.0
        
        # Send Input
        send_shortcut_multi(eff_key)
        time.sleep(delay)
        send_shortcut_multi(find_key)
        time.sleep(delay)

        # 3. Focused Control Verification (Edit1)
        hwnd = win32gui.GetForegroundWindow()
        
        if "Premiere Pro" not in win32gui.GetWindowText(hwnd):
            self.fail_capture("Premiere Pro wasn't active.")
            return

        # We use GetGUIThreadInfo to find the focused control in Premiere
        try:
            import ctypes
            from ctypes import wintypes
            class GUITHREADINFO(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD), ("hwndActive", wintypes.HWND),
                            ("hwndFocus", wintypes.HWND), ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
                            ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND), ("rcCaret", wintypes.RECT)]
            
            guiInfo = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
            ctypes.windll.user32.GetGUIThreadInfo(0, ctypes.byref(guiInfo))
            focused_hwnd = guiInfo.hwndFocus
            class_name = win32gui.GetClassName(focused_hwnd)
        except:
            class_name = "Unknown"

        # Strict Verification : Should find an "Edit" control box
        if "Edit" not in class_name:
            self.fail_capture(f"Erreur Focus : the Search Box is unreachable, make sure your Keymaps are corrects. (Classe: {class_name}).")
            return

        # 4. Succès : On enregistre
        rect = win32gui.GetWindowRect(hwnd)
        x, y = pyautogui.position()
        
        self.captured_data = {
            "mouse_x": x, "mouse_y": y,
            "main_x": rect[0], "main_y": rect[1],
            "main_w": rect[2] - rect[0], "main_h": rect[3] - rect[1],
            "delay_ms": self.slider_delay.value()
        }
        
        self.lbl_coord.setText(f" Done ! Mouse: {x},{y} | Class: {class_name}")
        self.lbl_coord.setProperty("state", "saved")
        self.lbl_coord.style().unpolish(self.lbl_coord)
        self.lbl_coord.style().polish(self.lbl_coord)
        self.btn_capture.setText(" Retry")
        self.btn_capture.setEnabled(True)
        self.btn_test.setEnabled(True)

    def fail_capture(self, msg):
        self.lbl_coord.setText(f" {msg}")
        self.lbl_coord.setProperty("state", "undefined")
        self.btn_capture.setText(" Retry")
        self.btn_capture.setEnabled(True)
        QMessageBox.critical(self, "Calibration Error", msg)

    def test_position(self):
        if not self.captured_data: return
        EffectApplier.focus_premiere()
        time.sleep(0.5)
        pyautogui.moveTo(self.captured_data["mouse_x"], self.captured_data["mouse_y"], duration=0.5)

    def toggle_keep_mode(self):
        current = self.btn_toggle_keep.property("qa_state")
        new_state = "disabled" if current == "enabled" else "enabled"
        self.btn_toggle_keep.setProperty("qa_state", new_state)
        self.btn_toggle_keep.style().unpolish(self.btn_toggle_keep)
        self.btn_toggle_keep.style().polish(self.btn_toggle_keep)
        self.update_keep_ui()

    def update_keep_ui(self):
        current = self.btn_toggle_keep.property("qa_state")
        is_keep = current == "enabled"
        self.btn_toggle_keep.setText("Keep on mouse" if is_keep else "Release at mouse")

    def save_config(self):
        data = self.captured_data if self.captured_data else (PresetApplier.load_config() or {})
        data["delay_ms"] = self.slider_delay.value()
        
        current = self.btn_toggle_keep.property("qa_state")
        data["keep_on_mouse"] = current == "enabled"
        
        PresetApplier.save_config(data)
        self.keybinds_section.save_keybinds()
        self.main_window.append_log(f" Config QuickApply saved (Delay: {data['delay_ms']}ms)", THEME_USER_COLORS["success"])
        if hasattr(self.main_window, 'reload_commands'):
            self.main_window.reload_commands()
        self.accept()