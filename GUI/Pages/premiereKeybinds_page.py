# GUI/premiereKeybinds_page.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout,
                             QPushButton, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from Core.paths import get_data_path
from Core.configs.keybinds_config import DEFAULT_KEYBINDS
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
import json
import os


from GUI.Widgets.hotkeyInputBox import KeybindCapture

class KeybindInput(KeybindCapture):
    pass


class PremiereKeybindsPage(QWidget):
    def __init__(self, main_window, embed_mode=False):
        super().__init__()
        self.mw = main_window
        self.embed_mode = embed_mode
        self.inputs = {}
        self.init_ui()
        self.load_keybinds()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["spacing_element"], THEME_SPACING["spacing_element"], THEME_SPACING["spacing_element"], THEME_SPACING["spacing_element"])
        layout.setSpacing(THEME_SPACING["spacing_element"])

        title = QLabel("Premiere Keybinds")
        title.setObjectName("SectionTitleFirst")
        layout.addWidget(title)

        desc = QLabel("Configure keyboard shortcuts for Premiere Pro navigation.")
        desc.setObjectName("CardLabelSubtle")
        layout.addWidget(desc)

        self.keybinds_frame = QFrame()
        self.keybinds_frame.setObjectName("CardFrame")
        keybinds_layout = QVBoxLayout(self.keybinds_frame)
        keybinds_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
        keybinds_layout.setSpacing(THEME_SPACING["spacing_element"])

        self.actions = list(DEFAULT_KEYBINDS.keys())
        for action in self.actions:
            row = QHBoxLayout()
            lbl = QLabel(action)
            lbl.setObjectName("CardLabel")
            inp = KeybindInput(DEFAULT_KEYBINDS.get(action, ""), action_name=action)
            inp.setFixedWidth(THEME_SPACING["width_input_keybind"])
            self.inputs[action] = inp
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(inp)
            keybinds_layout.addLayout(row)

        layout.addWidget(self.keybinds_frame)

        if not self.embed_mode:
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()

            btn_save = QPushButton()
            btn_save.setIcon(icon("save"))
            btn_save.setText(" Save")
            btn_save.clicked.connect(self.save_keybinds)
            btn_layout.addWidget(btn_save)

            layout.addLayout(btn_layout)

    def check_conflict(self, action_name, new_keybind):
        new_norm = new_keybind.strip().lower()
        for act, inp in self.inputs.items():
            if act != action_name and inp.text():
                if inp.text().strip().lower() == new_norm:
                    return act
        return None

    def load_keybinds(self):
        path = get_data_path("keybinds.json")
        if not os.path.exists(path) and os.path.exists(get_data_path("pr_keybinds.json")):
            path = get_data_path("pr_keybinds.json")
        
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for act, inp in self.inputs.items():
                        if act in data:
                            inp.setText(data[act])
            except Exception as e:
                self.mw.append_log(f"Error loading keybinds: {e}", THEME_USER_COLORS["error"])

    def save_keybinds(self):
        built_in_values = {}
        for act, inp in self.inputs.items():
            kb = inp.text().strip()
            if kb:
                kb_norm = kb.lower()
                if kb_norm in built_in_values:
                    QMessageBox.warning(
                        self,
                        "Hotkey Conflict",
                        f"The hotkey '{kb}' is already in use by '{built_in_values[kb_norm]}'. "
                        f"Please choose a different hotkey before saving."
                    )
                    return
                built_in_values[kb_norm] = act

        path = get_data_path("keybinds.json")
        os.makedirs(get_data_path(), exist_ok=True)
        try:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            data.update({act: inp.text() for act, inp in self.inputs.items()})
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.mw.append_log(" Premiere Keybinds saved!", THEME_USER_COLORS["success"])
            if hasattr(self.mw, 'update_global_hotkey'):
                self.mw.update_global_hotkey()
        except Exception as e:
            self.mw.append_log(f" Error saving keybinds: {e}", THEME_USER_COLORS["error"])