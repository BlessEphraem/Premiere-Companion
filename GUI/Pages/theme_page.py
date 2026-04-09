# GUI/theme_page.py
import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout,
                              QPushButton, QLineEdit, QScrollArea, QApplication, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase
from Core.paths import get_data_path
from Core.theme_qss import (THEME_USER_COLORS, THEME_SCHEMA, THEME_SCHEMA_SECTIONS,
                              THEME_SPACING, generate_theme_qss)
from Core.functions.icon_loader import icon, icon_pixmap

# Keys that accept old theme.json names → migrate to new names on load.
_KEY_MIGRATIONS = {
    "bg_secondary": "btn_bg",
    "border":       "hover",
    "primary_btn":  "btn_accent_1",
    "accent_btn":   "btn_accent_2",
    "yellow_btn":   "btn_accent_3",
    "icon_default": "icon_color",
}

# All keys whose values must be valid colors (hex or CSS name).
_COLOR_KEYS = frozenset({
    "accent", "bg", "btn_bg", "input_bg", "list_bg", "console_bg",
    "hover", "text_main", "text_subtle", "info_text",
    "success", "label_audio", "error", "label_video", "info", "label_transition",
    "warning", "btn_accent_1", "btn_accent_2", "btn_accent_3", "icon_color",
    # Search Bar
    "sb_bg", "sb_border", "sb_input_text", "sb_item_text",
    "sb_item_hover", "sb_recent_icon", "sb_last_used",
})

# Keys where "none" is also an accepted value (transparent backgrounds).
_BG_COLOR_KEYS = frozenset({"bg", "btn_bg", "input_bg", "list_bg", "console_bg", "card_bg", "sb_bg"})


class ThemePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.theme_path = get_data_path("theme.json")
        self.inputs = {}
        self.error_labels = {}
        self.available_fonts = [
            "Satoshi", "Inter", "Segoe UI", "Arial", "Roboto",
            "Ubuntu", "Helvetica Neue", "System Default",
        ]
        for font in QFontDatabase.families():
            if font not in self.available_fonts:
                self.available_fonts.append(font)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
        )

        title_layout = QHBoxLayout()
        title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_icon = QLabel()
        lbl_icon.setPixmap(icon_pixmap("palette", size=THEME_SPACING["icon_large"]))
        lbl_icon.setFixedSize(THEME_SPACING["icon_large"], THEME_SPACING["icon_large"])
        lbl_icon.setScaledContents(True)
        lbl_title = QLabel("Theme Configuration")
        lbl_title.setObjectName("PageTitle")
        title_layout.addWidget(lbl_icon)
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        lbl_info = QLabel(
            "Use HEX colors (e.g. #FF1796), CSS names (e.g. blue), "
            "or 'none' for transparent backgrounds."
        )
        lbl_info.setObjectName("CardLabelSubtle")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TransparentScroll")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("TransparentContainer")
        vbox = QVBoxLayout(scroll_content)
        vbox.setContentsMargins(
            THEME_SPACING["spacing_element"], THEME_SPACING["spacing_element"],
            THEME_SPACING["spacing_element"], THEME_SPACING["spacing_element"],
        )
        vbox.setSpacing(THEME_SPACING["spacing_element"])

        # Load current saved values
        current_data = {}
        if os.path.exists(self.theme_path):
            try:
                with open(self.theme_path, "r", encoding="utf-8") as f:
                    current_data = json.load(f)
            except Exception:
                pass

        self.original_values = {}
        first_section = True

        for section_title, entries in THEME_SCHEMA_SECTIONS:
            # Section header
            lbl_section = QLabel(section_title)
            lbl_section.setObjectName("ThemeSectionTitle")
            if first_section:
                lbl_section.setContentsMargins(0, 0, 0, 0)
                first_section = False
            vbox.addWidget(lbl_section)

            for key, label_text, default_val in entries:
                row_container = QWidget()
                row_layout = QVBoxLayout(row_container)
                row_layout.setContentsMargins(
                    THEME_SPACING["spacing_element"], THEME_SPACING["spacing_element"],
                    THEME_SPACING["spacing_element"], THEME_SPACING["spacing_element"],
                )
                row_layout.setSpacing(THEME_SPACING["spacing_tight"])

                frame = QFrame()
                frame.setObjectName("CardFrame")
                hbox = QHBoxLayout(frame)
                hbox.setContentsMargins(
                    THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"],
                    THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"],
                )

                lbl = QLabel(label_text)
                lbl.setObjectName("CardLabel")

                val = current_data.get(key, default_val)
                self.original_values[key] = val
                inp = QLineEdit(val)
                inp.setFixedWidth(THEME_SPACING["width_button_medium"])
                inp.setObjectName(f"ThemeInput_{key}")
                inp.editingFinished.connect(lambda k=key, i=inp: self.validate_on_blur(k, i))

                self.inputs[key] = inp

                hbox.addWidget(lbl)
                hbox.addStretch()
                hbox.addWidget(inp)

                error_lbl = QLabel()
                error_lbl.setObjectName("ThemeErrorLabel")
                error_lbl.setVisible(False)
                self.error_labels[key] = error_lbl

                row_layout.addWidget(frame)
                row_layout.addWidget(error_lbl)
                vbox.addWidget(row_container)

        vbox.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()

        btn_reset = QPushButton()
        btn_reset.setIcon(icon("sync"))
        btn_reset.setText(" Reset to Defaults")
        btn_reset.setObjectName("AccentButton")
        btn_reset.clicked.connect(self.reset_theme)

        btn_save = QPushButton()
        btn_save.setIcon(icon("save"))
        btn_save.setText(" Save Theme")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_theme)

        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    # ── Validation ─────────────────────────────────────────────────────────────

    def validate_color(self, color_str, is_bg_color=False):
        color_str = color_str.strip().lower()
        CSS_COLORS = {
            "black", "white", "red", "green", "blue", "yellow", "cyan", "magenta",
            "gray", "grey", "orange", "purple", "pink", "brown", "lime", "navy",
            "teal", "olive", "maroon", "silver",
        }
        if color_str == "none" and is_bg_color:
            return True
        if color_str in CSS_COLORS:
            return True
        hex_val = color_str.lstrip('#')
        return len(hex_val) == 6 and all(c in '0123456789abcdefABCDEF' for c in hex_val)

    def validate_on_blur(self, key, inp):
        val = inp.text().strip()
        if key in _COLOR_KEYS:
            is_bg = key in _BG_COLOR_KEYS
            if val and not self.validate_color(val, is_bg):
                self.error_labels[key].setText("Invalid color. Use #RRGGBB or CSS name (e.g. blue)")
                self.error_labels[key].setVisible(True)
            else:
                self.error_labels[key].setVisible(False)

    # ── Reset / Save ────────────────────────────────────────────────────────────

    def reset_theme(self):
        reply = QMessageBox.question(
            self, "Reset Theme", "Reset all theme colors to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for _, entries in THEME_SCHEMA_SECTIONS:
                for key, _, default_val in entries:
                    self.inputs[key].setText(default_val)
                    self.original_values[key] = default_val

            theme_data = {key: default_val
                          for _, entries in THEME_SCHEMA_SECTIONS
                          for key, _, default_val in entries}
            os.makedirs(get_data_path(), exist_ok=True)
            try:
                with open(self.theme_path, "w", encoding="utf-8") as f:
                    json.dump(theme_data, f, indent=4)
                self.reload_theme()
                self.mw.append_log(" Theme reset to defaults!", THEME_USER_COLORS["success"])
            except Exception as e:
                self.mw.append_log(f" Error resetting theme: {e}", THEME_USER_COLORS["error"])

    def save_theme(self):
        theme_data = {}
        invalid_items = []

        for _, entries in THEME_SCHEMA_SECTIONS:
            for key, _, default_val in entries:
                val = self.inputs[key].text().strip()
                theme_data[key] = val if val else default_val
                if key in _COLOR_KEYS:
                    is_bg = key in _BG_COLOR_KEYS
                    if val and not self.validate_color(val, is_bg):
                        invalid_items.append(key)

        for key in invalid_items:
            self.error_labels[key].setText("Invalid color. Use #RRGGBB or CSS name (e.g. blue)")
            self.error_labels[key].setVisible(True)

        if invalid_items:
            return

        # Check if anything changed
        has_changes = any(
            self.inputs[key].text().strip() != self.original_values.get(key, default_val)
            for _, entries in THEME_SCHEMA_SECTIONS
            for key, _, default_val in entries
        )
        if not has_changes:
            self.mw.append_log(" No changes to save.", THEME_USER_COLORS["success"])
            return

        os.makedirs(get_data_path(), exist_ok=True)
        try:
            with open(self.theme_path, "w", encoding="utf-8") as f:
                json.dump(theme_data, f, indent=4)
            self.reload_theme()
            self.mw.append_log(" Theme saved and applied!", THEME_USER_COLORS["success"])
        except Exception as e:
            self.mw.append_log(f" Error saving theme: {e}", THEME_USER_COLORS["error"])

    # ── Reload ──────────────────────────────────────────────────────────────────

    def reload_theme(self):
        from Core.paths import get_app_path, get_data_path
        from Core.theme_qss import THEME_USER_COLORS
        from Core.functions import icon_loader
        import json
        import os

        colors = THEME_USER_COLORS.copy()
        theme_path = get_data_path("theme.json")
        if os.path.exists(theme_path):
            try:
                with open(theme_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Migrate old key names silently
                for old_key, new_key in _KEY_MIGRATIONS.items():
                    if old_key in loaded and new_key not in loaded:
                        loaded[new_key] = loaded.pop(old_key)
                colors.update(loaded)
            except Exception:
                pass

        base_dir = get_app_path()
        font_path = os.path.join(base_dir, "Assets", "Satoshi-Variable.ttf")
        loaded_font = None
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    loaded_font = families[0]

        dynamic_qss = generate_theme_qss(colors, loaded_font)
        QApplication.instance().setStyleSheet("")
        QApplication.instance().setStyleSheet(dynamic_qss)

        # Invalidate icon cache so next icon() calls pick up the new color
        icon_loader.reload_theme()

        if hasattr(self.mw, 'btn_home'):
            try:
                from GUI.Widgets.Menu import get_app_icon
                self.mw.btn_home.setIcon(get_app_icon())
            except Exception as e:
                print(f"Error updating app icon: {e}")
