# GUI/Pages/macro_editor_page.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox, 
                             QFrame, QCompleter, QWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from Core.paths import get_data_path
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
from Core.configs.labels_config import get_type_codes, is_video, is_audio, is_transition, is_preset, is_command
from Core.configs.macros_config import load_macros_config, save_macros_config
import json
import os

class MacroActionWidget(QWidget):
    def __init__(self, action_data, list_widget, parent_page):
        super().__init__()
        self.action_data = action_data
        self.list_widget = list_widget
        self.parent_page = parent_page

        layout = QHBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"], THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"])

        lbl_text = QLabel(f"[{action_data.get('type', '?')}] {action_data.get('displayName', '?')}")
        lbl_text.setObjectName("CardLabelSubtle")
        layout.addWidget(lbl_text, stretch=1)

        btn_up = QPushButton()
        btn_up.setIcon(icon("arrow-up"))
        btn_up.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
        btn_up.setObjectName("RegexMoveBtn")
        btn_up.clicked.connect(self.move_up)

        btn_down = QPushButton()
        btn_down.setIcon(icon("arrow-down"))
        btn_down.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
        btn_down.setObjectName("RegexMoveBtn")
        btn_down.clicked.connect(self.move_down)

        btn_del = QPushButton()
        btn_del.setIcon(icon("times-circle"))
        btn_del.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
        btn_del.setObjectName("RegexDeleteBtn")
        btn_del.clicked.connect(self.delete_action)

        layout.addWidget(btn_up)
        layout.addWidget(btn_down)
        layout.addWidget(btn_del)

    def move_up(self):
        row = self.list_widget.row(self.list_widget.itemAt(self.pos())) # Not reliable
        # Better: find idx in parent_page.actions
        idx = self.parent_page.actions.index(self.action_data)
        if idx > 0:
            self.parent_page.actions[idx], self.parent_page.actions[idx-1] = self.parent_page.actions[idx-1], self.parent_page.actions[idx]
            self.parent_page.load_actions_ui()

    def move_down(self):
        idx = self.parent_page.actions.index(self.action_data)
        if idx < len(self.parent_page.actions) - 1:
            self.parent_page.actions[idx], self.parent_page.actions[idx+1] = self.parent_page.actions[idx+1], self.parent_page.actions[idx]
            self.parent_page.load_actions_ui()

    def delete_action(self):
        self.parent_page.actions.remove(self.action_data)
        self.parent_page.load_actions_ui()

class MacroSearchInput(QLineEdit):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.setPlaceholderText("Search for Effect, Preset or Command...")
        self.completer_obj = QCompleter()
        self.completer_obj.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer_obj.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer_obj)
        self.update_completer()

    def update_completer(self):
        model = QStandardItemModel()
        from Core.functions.cmd_actions import get_dynamic_commands
        all_items = self.mw.all_effects + self.mw.all_presets + get_dynamic_commands()
        for item in all_items:
            e_type = item.get("type", "Unknown")
            clean_name = self.mw.cleaner.clean_name(item.get("displayName", ""), e_type)
            m_name = item.get("matchName", "")
            display_str = f"[{e_type}] {clean_name} ({m_name})"
            model.appendRow(QStandardItem(display_str))
        self.completer_obj.setModel(model)

class MacroEditorPage(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.setModal(True)
        self.setWindowTitle("Macro Editor")
        self.actions = []
        self.editing_name = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"])
        layout.setSpacing(THEME_SPACING["spacing_element"])

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Macro Name (e.g., My Awesome Macro)")
        self.name_input.setFixedHeight(THEME_SPACING["height_action_input"])
        layout.addWidget(self.name_input)

        add_frame = QFrame()
        add_frame.setObjectName("CardFrame")
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
        
        self.search_input = MacroSearchInput(self.mw)
        btn_add = QPushButton(" Add to Sequence")
        btn_add.setIcon(icon("plus"))
        btn_add.clicked.connect(self.add_action)
        
        add_layout.addWidget(self.search_input, 1)
        add_layout.addWidget(btn_add)
        layout.addWidget(add_frame)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton(" Save Macro")
        btn_save.setIcon(icon("save"))
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_macro)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def add_action(self):
        search_str = self.search_input.text().strip()
        if not search_str: return

        from Core.functions.cmd_actions import get_dynamic_commands
        all_items = self.mw.all_effects + self.mw.all_presets + get_dynamic_commands()
        
        found_item = None
        for item in all_items:
            e_type = item.get("type", "Unknown")
            m_name = item.get("matchName", "")
            clean_name = self.mw.cleaner.clean_name(item.get("displayName", ""), e_type)
            if search_str == f"[{e_type}] {clean_name} ({m_name})":
                found_item = {
                    "type": e_type,
                    "matchName": m_name,
                    "displayName": clean_name
                }
                break
        
        if found_item:
            self.actions.append(found_item)
            self.load_actions_ui()
            self.search_input.clear()
        else:
            QMessageBox.warning(self, "Invalid Selection", "Please select an item from the dropdown list.")

    def load_actions_ui(self):
        self.list_widget.clear()
        for action in self.actions:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 40))
            widget = MacroActionWidget(action, self.list_widget, self)
            self.list_widget.setItemWidget(item, widget)

    def load_macro(self, macro_data):
        self.editing_name = macro_data["name"]
        self.name_input.setText(self.editing_name)
        self.actions = list(macro_data.get("actions", []))
        self.load_actions_ui()

    def save_macro(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for the macro.")
            return
        if not self.actions:
            QMessageBox.warning(self, "Empty Macro", "Please add at least one action to the macro.")
            return

        config = load_macros_config()
        
        # Check for duplicate name (if not editing the same one)
        if name != self.editing_name and any(m["name"] == name for m in config["macros"]):
            QMessageBox.warning(self, "Duplicate Name", "A macro with this name already exists.")
            return

        new_macro = {"name": name, "actions": self.actions}
        
        if self.editing_name:
            config["macros"] = [m if m["name"] != self.editing_name else new_macro for m in config["macros"]]
        else:
            config["macros"].append(new_macro)
            
        save_macros_config(config)
        self.accept()
