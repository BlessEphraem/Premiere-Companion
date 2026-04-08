# GUI/Pages/searchbar_page.py
import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QHBoxLayout, QSpinBox,
                             QPushButton, QFormLayout, QSlider, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from Core.paths import get_data_path
from Core.configs.search_config import SEARCHBAR_DEFAULTS
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
from GUI.Widgets.hotkeyInputBox import KeybindCapture
from Core.configs.keybinds_config import DEFAULT_SEARCH_BAR_KEY


class SearchBarPage(QDialog):
    CONFIG_PATH = get_data_path("searchbar_config.json")

    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.original_values = {}
        self.setModal(True)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"])

        title_layout = QHBoxLayout()
        title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_title = QLabel()
        lbl_title.setPixmap(icon_pixmap("search", size=THEME_SPACING["icon_large"]))
        lbl_title.setFixedSize(THEME_SPACING["icon_large"], THEME_SPACING["icon_large"])
        lbl_title.setScaledContents(True)
        lbl_title_2 = QLabel("SearchBar Configuration")
        lbl_title_2.setObjectName("PageTitle")
        title_layout.addWidget(lbl_title)
        title_layout.addWidget(lbl_title_2)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # ── Global Hotkey Section ─────────────────────────────────────────────
        hotkey_frame = QFrame()
        hotkey_frame.setObjectName("CardFrame")
        hotkey_card_layout = QVBoxLayout(hotkey_frame)
        hotkey_card_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
        
        hotkey_row = QHBoxLayout()
        lbl_hotkey = QLabel("Global Hotkey to Open SearchBar:")
        lbl_hotkey.setObjectName("CardLabelBold")
        
        self.search_keybind_input = KeybindCapture(action_name="Run Search Bar")
        self.search_keybind_input.setPlaceholderText("Press keybind")
        self.search_keybind_input.setFixedWidth(THEME_SPACING["width_input_keybind"])
        self.search_keybind_input.textChanged.connect(self._on_search_keybind_changed)
        self._load_search_keybind()
        
        hotkey_row.addWidget(lbl_hotkey)
        hotkey_row.addStretch()
        hotkey_row.addWidget(self.search_keybind_input)
        hotkey_card_layout.addLayout(hotkey_row)
        
        layout.addWidget(hotkey_frame)

        self.lbl_max_items = QLabel("Max item showed : 100")
        layout.addWidget(self.lbl_max_items)
        
        self.slider_max_items = QSlider(Qt.Orientation.Horizontal)
        self.slider_max_items.setRange(1, 256)
        self.slider_max_items.valueChanged.connect(lambda v: self.lbl_max_items.setText(f"Max item showed : {v}"))
        layout.addWidget(self.slider_max_items)

        self.lbl_max_recent = QLabel("Max item in recent : 3")
        layout.addWidget(self.lbl_max_recent)
        
        self.slider_max_recent = QSlider(Qt.Orientation.Horizontal)
        self.slider_max_recent.setRange(0, 5)
        self.slider_max_recent.valueChanged.connect(lambda v: self.lbl_max_recent.setText(f"Max item in recent : {v}"))
        layout.addWidget(self.slider_max_recent)

        self.lbl_width = QLabel("Bar Width : 600 px")
        layout.addWidget(self.lbl_width)
        
        self.slider_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_width.setRange(300, 1200)
        self.slider_width.valueChanged.connect(lambda v: self.lbl_width.setText(f"Bar Width : {v} px"))
        layout.addWidget(self.slider_width)

        self.lbl_height = QLabel("Bar Height : 420 px")
        layout.addWidget(self.lbl_height)
        
        self.slider_height = QSlider(Qt.Orientation.Horizontal)
        self.slider_height.setRange(200, 1000)
        self.slider_height.valueChanged.connect(lambda v: self.lbl_height.setText(f"Bar Height : {v} px"))
        layout.addWidget(self.slider_height)

        self.lbl_font = QLabel("Font Size : 15 px")
        layout.addWidget(self.lbl_font)
        
        self.slider_font = QSlider(Qt.Orientation.Horizontal)
        self.slider_font.setRange(10, 30)
        self.slider_font.valueChanged.connect(lambda v: self.lbl_font.setText(f"Font Size : {v} px"))
        layout.addWidget(self.slider_font)

        self.lbl_opacity = QLabel("Background Opacity : 85%")
        layout.addWidget(self.lbl_opacity)
        
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(50, 100)
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opacity.setText(f"Background Opacity : {v}%"))
        layout.addWidget(self.slider_opacity)

        blur_layout = QHBoxLayout()
        self.check_blur = QPushButton()
        self.check_blur.setCheckable(True)
        self.check_blur.setText("Blur Background")
        self.check_blur.setObjectName("Toggle")
        self.check_blur.setProperty("qa_state", "disabled")
        self.check_blur.style().unpolish(self.check_blur)
        self.check_blur.style().polish(self.check_blur)
        self.check_blur.clicked.connect(self._toggle_blur)
        
        self.lbl_blur_restart = QLabel("Restart required")
        self.lbl_blur_restart.setObjectName("SearchBarRestartLabel")
        self.lbl_blur_restart.hide()
        
        blur_layout.addWidget(self.check_blur)
        blur_layout.addWidget(self.lbl_blur_restart)
        blur_layout.addStretch()
        layout.addLayout(blur_layout)

        layout.addSpacing(10)

        self.check_last_empty = QPushButton()
        self.check_last_empty.setCheckable(True)
        self.check_last_empty.setText("Apply Last on Empty Enter: OFF")
        self.check_last_empty.setObjectName("Toggle")
        self.check_last_empty.setProperty("qa_state", "disabled")
        self.check_last_empty.clicked.connect(self._toggle_last_empty)
        layout.addWidget(self.check_last_empty)

        self.check_last_no_name = QPushButton()
        self.check_last_no_name.setCheckable(True)
        self.check_last_no_name.setText("Apply Last Without Name: OFF (Requires Above)")
        self.check_last_no_name.setObjectName("Toggle")
        self.check_last_no_name.setProperty("qa_state", "disabled")
        self.check_last_no_name.clicked.connect(self._toggle_last_no_name)
        layout.addWidget(self.check_last_no_name)

        self.lbl_last_info = QLabel("When search is empty, pressing Enter will just apply the last effect without typing its name.")
        self.lbl_last_info.setObjectName("RegexInfoLabel")
        self.lbl_last_info.hide()
        layout.addWidget(self.lbl_last_info)

        layout.addSpacing(10)
        layout.addStretch()

        btn_layout = QHBoxLayout()

        btn_reset = QPushButton()
        btn_reset.setIcon(icon("sync"))
        btn_reset.setText(" Reset to Defaults")
        btn_reset.setObjectName("AccentButton")
        btn_reset.clicked.connect(self.reset_config)

        btn_save = QPushButton()
        btn_save.setIcon(icon("save"))
        btn_save.setText(" Save Settings")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_config)

        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)



    def _load_search_keybind(self):
        kb_path = get_data_path("keybinds.json")
        key = DEFAULT_SEARCH_BAR_KEY
        if os.path.exists(kb_path):
            try:
                import json
                with open(kb_path, "r", encoding="utf-8") as f:
                    key = json.load(f).get("Run Search Bar", DEFAULT_SEARCH_BAR_KEY)
            except Exception:
                pass
        self.search_keybind_input.blockSignals(True)
        self.search_keybind_input.setText(key)
        self.search_keybind_input.blockSignals(False)

    def _on_search_keybind_changed(self, text):
        kb_path = get_data_path("keybinds.json")
        try:
            import json
            with open(kb_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data["Run Search Bar"] = text
        import os
        os.makedirs(get_data_path(), exist_ok=True)
        with open(kb_path, "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, indent=4)
        if hasattr(self.mw, "update_global_hotkey"):
            self.mw.update_global_hotkey()

    def check_conflict(self, action_name, new_keybind):
        if not new_keybind:
            return None
        new_norm = new_keybind.strip().lower()

        kb_path = get_data_path("keybinds.json")
        import os
        import json
        if os.path.exists(kb_path):
            try:
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb_data = json.load(f)
                for hk in kb_data.get("custom_hotkeys", []):
                    if hk.get("keybind", "").strip().lower() == new_norm:
                        return f"Custom Hotkey ({hk.get('match_name', '?')})"
            except Exception:
                pass

        bm_path = get_data_path("betterMotion_config.json")
        if os.path.exists(bm_path):
            try:
                with open(bm_path, "r", encoding="utf-8") as f:
                    bm = json.load(f)
                for sec_key in ("position", "scale", "rotation", "opacity"):
                    for act_key, act_val in bm.get(sec_key, {}).items():
                        k = act_val.get("key", "") if isinstance(act_val, dict) else act_val
                        if k and k.strip().lower() == new_norm:
                            return f"Better Motion: {sec_key}.{act_key}"
            except Exception:
                pass

        return None
            
    def load_config(self):
        default_config = SEARCHBAR_DEFAULTS.copy()
        
        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_config.update(data)
            except Exception:
                pass

        for key, val in default_config.items():
            self.original_values[key] = val

        self.slider_max_items.setValue(default_config.get("max_items", 100))
        self.slider_max_recent.setValue(default_config.get("max_recent", 3))
        self.slider_width.setValue(default_config.get("window_width", 600))
        self.slider_height.setValue(default_config.get("window_height", 420))
        self.slider_font.setValue(default_config.get("font_size", 15))
        self.slider_opacity.setValue(int(default_config.get("bg_opacity", 0.85) * 100))
        blur_state = default_config.get("blur_background", False)
        self.check_blur.setChecked(blur_state)
        self.check_blur.setProperty("qa_state", "enabled" if blur_state else "disabled")
        self.check_blur.style().unpolish(self.check_blur)
        self.check_blur.style().polish(self.check_blur)
        self._update_blur_button_text()

        last_empty_state = default_config.get("apply_last_on_empty_enter", False)
        self.check_last_empty.setChecked(last_empty_state)
        self.check_last_no_name.setEnabled(last_empty_state)
        
        last_no_name_state = default_config.get("apply_last_without_name_enter", False)
        self.check_last_no_name.setChecked(last_no_name_state)
        
        self._update_last_empty_button()
        self._update_last_no_name_button()

    def reset_config(self):
        self.lbl_blur_restart.hide()
        self.lbl_last_info.hide()
        
        reply = QMessageBox.question(
            self,
            "Reset SearchBar Settings",
            "Reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.slider_max_items.setValue(SEARCHBAR_DEFAULTS["max_items"])
            self.slider_max_recent.setValue(SEARCHBAR_DEFAULTS["max_recent"])
            self.slider_width.setValue(SEARCHBAR_DEFAULTS["window_width"])
            self.slider_height.setValue(SEARCHBAR_DEFAULTS["window_height"])
            self.slider_font.setValue(SEARCHBAR_DEFAULTS["font_size"])
            self.slider_opacity.setValue(int(SEARCHBAR_DEFAULTS["bg_opacity"] * 100))
            self.check_blur.setChecked(SEARCHBAR_DEFAULTS["blur_background"])
            self.check_blur.setProperty("qa_state", "enabled" if SEARCHBAR_DEFAULTS["blur_background"] else "disabled")
            self.check_blur.style().unpolish(self.check_blur)
            self.check_blur.style().polish(self.check_blur)
            self._update_blur_button_text()
            
            self.check_last_empty.setChecked(SEARCHBAR_DEFAULTS["apply_last_on_empty_enter"])
            self.check_last_no_name.setChecked(SEARCHBAR_DEFAULTS["apply_last_without_name_enter"])
            self._update_last_empty_button()
            self._update_last_no_name_button()
            
            self._save_to_file(SEARCHBAR_DEFAULTS)
            self.mw.append_log(" SearchBar settings reset to defaults!", THEME_USER_COLORS["success"])
            self.accept()

    def save_config(self):
        self.lbl_blur_restart.hide()
        
        data = {
            "max_items": self.slider_max_items.value(),
            "max_recent": self.slider_max_recent.value(),
            "window_width": self.slider_width.value(),
            "window_height": self.slider_height.value(),
            "font_size": self.slider_font.value(),
            "bg_opacity": self.slider_opacity.value() / 100.0,
            "blur_background": self.check_blur.isChecked(),
            "apply_last_on_empty_enter": self.check_last_empty.isChecked(),
            "apply_last_without_name_enter": self.check_last_no_name.isChecked()
        }

        has_changes = False
        for key, val in data.items():
            original = self.original_values.get(key)
            if val != original:
                has_changes = True
                break

        if not has_changes:
            self.mw.append_log(" No changes to save.", THEME_USER_COLORS["success"])
            return

        self._save_to_file(data)
        self.mw.append_log(" SearchBar settings saved!", THEME_USER_COLORS["success"])
        self.accept()

    def _save_to_file(self, data):
        os.makedirs(get_data_path(), exist_ok=True)
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def _toggle_blur(self):
        self._update_blur_button_text()
        
        if self.check_blur.isChecked():
            self.check_blur.setProperty("qa_state", "enabled")
            self.lbl_blur_restart.show()
        else:
            self.check_blur.setProperty("qa_state", "disabled")
            self.lbl_blur_restart.hide()
        
        self.check_blur.style().unpolish(self.check_blur)
        self.check_blur.style().polish(self.check_blur)

    def _update_blur_button_text(self):
        if self.check_blur.isChecked():
            self.check_blur.setText("Blur: ON")
        else:
            self.check_blur.setText("Blur: OFF")

    def _check_restart_needed(self):
        current_setting = self.check_blur.isChecked()
        applied_setting = False
        if hasattr(self.mw, 'search_bar_overlay') and self.mw.search_bar_overlay is not None:
            if hasattr(self.mw.search_bar_overlay, 'config'):
                applied_setting = self.mw.search_bar_overlay.config.get("blur_background", False)
        if current_setting != applied_setting:
            self.lbl_blur_restart.show()
        else:
            self.lbl_blur_restart.hide()

    def _toggle_last_empty(self):
        self._update_last_empty_button()

    def _update_last_empty_button(self):
        is_checked = self.check_last_empty.isChecked()
        self.check_last_empty.setProperty("qa_state", "enabled" if is_checked else "disabled")
        self.check_last_empty.style().unpolish(self.check_last_empty)
        self.check_last_empty.style().polish(self.check_last_empty)
        self.check_last_empty.setText(f"Apply Last on Empty Enter: {'ON' if is_checked else 'OFF'}")

        self.check_last_no_name.setEnabled(is_checked)
        if not is_checked:
            self.check_last_no_name.setChecked(False)
            self.check_last_no_name.setProperty("qa_state", "disabled")
            self.check_last_no_name.style().unpolish(self.check_last_no_name)
            self.check_last_no_name.style().polish(self.check_last_no_name)
            self.check_last_no_name.setText("Apply Last Without Name: OFF (Requires Above)")
        self._update_last_no_name_button()

    def _toggle_last_no_name(self):
        self._update_last_no_name_button()

    def _update_last_no_name_button(self):
        is_checked = self.check_last_no_name.isChecked()
        self.check_last_no_name.setProperty("qa_state", "enabled" if is_checked else "disabled")
        self.check_last_no_name.style().unpolish(self.check_last_no_name)
        self.check_last_no_name.style().polish(self.check_last_no_name)
        self.check_last_no_name.setText(f"Apply Last Without Name: {'ON' if is_checked else 'OFF'} (Requires Above)")
        self.lbl_last_info.setVisible(is_checked)
