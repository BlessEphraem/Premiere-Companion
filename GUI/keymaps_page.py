# GUI/keymaps_page.py
import os
import json
import re
from Core.paths import get_data_path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                             QPushButton, QScrollArea, QLineEdit, QCompleter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QStandardItemModel, QStandardItem

class KeybindInput(QLineEdit):
    def __init__(self, default_key="", default_vk=0):
        super().__init__()
        self.setText(default_key)
        self.vk = default_vk
        self.setReadOnly(True)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        if key in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return
        
        self.vk = event.nativeVirtualKey()
        key_sequence = QKeySequence(modifiers.value | key)
        self.setText(key_sequence.toString())
        self.clearFocus()

class CustomSearchInput(QLineEdit):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.filter_types = ["All", "FxVideo", "FxAudio", "Transition", "Preset"]
        self.current_filter_idx = 0
        self.setPlaceholderText("Search (All)...")
        
        self.completer_obj = QCompleter()
        self.completer_obj.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer_obj.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer_obj)

    def set_filter(self, filter_type):
        if filter_type in self.filter_types:
            self.current_filter_idx = self.filter_types.index(filter_type)
            self.setPlaceholderText(f"Search ({filter_type})...")
            self.setProperty("filterType", filter_type)
            self.style().unpolish(self)
            self.style().polish(self)
            self.update_completer()

    def focusInEvent(self, event):
        self.update_completer()
        super().focusInEvent(event)

    def update_completer(self):
        model = QStandardItemModel()
        all_items = self.mw.all_effects + self.mw.all_presets
        current_type = self.filter_types[self.current_filter_idx]

        for item in all_items:
            e_type = item.get("type", "Unknown")
            
            # Simplified and robust filtering
            if current_type != "All":
                is_transition = "Transition" in e_type
                is_preset = "Preset" in e_type
                is_video = "FxVideo" in e_type and not is_transition
                is_audio = "FxAudio" in e_type and not is_transition

                if current_type == "FxVideo" and not is_video: continue
                if current_type == "FxAudio" and not is_audio: continue
                if current_type == "Transition" and not is_transition: continue
                if current_type == "Preset" and not is_preset: continue
            
            clean_name = self.mw.cleaner.clean_name(item.get("displayName", ""), e_type)
            m_name = item.get("matchName", "")
            display_str = f"[{e_type}] {clean_name} ({m_name})"
            model.appendRow(QStandardItem(display_str))
            
        self.completer_obj.setModel(model)

class KeymapsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.inputs = {}
        self.custom_hotkeys = []
        self.filter_options = ["All", "FxVideo", "FxAudio", "Transition", "Preset"]
        self.current_filter_idx = 0
        self.init_ui()
        self.load_keybinds()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_title = QLabel("⌨️ Keymaps")
        lbl_title.setObjectName("PageTitle")
        layout.addWidget(lbl_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TransparentScroll")

        container = QWidget()
        container.setObjectName("TransparentContainer")
        self.form_layout = QVBoxLayout(container)

        # 1. Premiere Keybinds
        lbl_premiere = QLabel("Premiere Keybinds")
        lbl_premiere.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px; color: white;")
        self.form_layout.addWidget(lbl_premiere)

        actions_premiere = {
            "Window > Timelines": "Shift+3",
            "Window > Effect": "Shift+2",
            "Search Find Box": "Shift+F"
        }

        for action, default in actions_premiere.items():
            self.add_keybind_row(action, default)

        # 2. Hotkeys Section
        lbl_hotkeys = QLabel("Hotkeys")
        lbl_hotkeys.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px; color: white;")
        self.form_layout.addWidget(lbl_hotkeys)

        self.add_keybind_row("Run Search Bar", "Ctrl+Space")

        # 3. Custom Hotkeys
        lbl_custom = QLabel("Custom")
        lbl_custom.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px; color: white;")
        self.form_layout.addWidget(lbl_custom)

        add_layout = QHBoxLayout()
        self.custom_key_input = KeybindInput()
        self.custom_key_input.setPlaceholderText("Press Keybind")
        self.custom_key_input.setFixedWidth(150)
        
        self.custom_search = CustomSearchInput(self.mw)
        
        # --- Filter Cycle Button
        self.btn_filter = QPushButton("[All]")
        self.btn_filter.setObjectName("NavButton") 
        self.btn_filter.setFixedWidth(100)
        self.btn_filter.clicked.connect(self.cycle_filter_ui)
        
        btn_add = QPushButton("➕ Add")
        btn_add.setObjectName("PrimaryButton")
        btn_add.clicked.connect(self.add_custom_ui)

        add_layout.addWidget(self.custom_key_input)
        add_layout.addWidget(self.custom_search)
        add_layout.addWidget(self.btn_filter)
        add_layout.addWidget(btn_add)
        self.form_layout.addLayout(add_layout)

        # Container for the custom hotkeys list
        self.custom_list_container = QWidget()
        self.custom_list_layout = QVBoxLayout(self.custom_list_container)
        self.custom_list_layout.setContentsMargins(0, 10, 0, 0)
        self.form_layout.addWidget(self.custom_list_container)

        self.form_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_save = QPushButton("💾 Save Keybinds")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_keybinds)
        layout.addWidget(btn_save)

    def cycle_filter_ui(self):
        self.current_filter_idx = (self.current_filter_idx + 1) % len(self.filter_options)
        f_type = self.filter_options[self.current_filter_idx]
        self.btn_filter.setText(f"[{f_type}]")
        self.custom_search.set_filter(f_type)

    def add_keybind_row(self, action, default):
        frame = QFrame()
        frame.setObjectName("CardFrame")
        hbox = QHBoxLayout(frame)

        lbl = QLabel(action)
        lbl.setObjectName("CardLabel")
        inp = KeybindInput(default)
        inp.setFixedWidth(150)

        self.inputs[action] = inp
        hbox.addWidget(lbl)
        hbox.addStretch()
        hbox.addWidget(inp)
        self.form_layout.addWidget(frame)

    def render_custom_hotkeys(self):
        for i in reversed(range(self.custom_list_layout.count())):
            w = self.custom_list_layout.itemAt(i).widget()
            if w: w.deleteLater()

        for idx, chk in enumerate(self.custom_hotkeys):
            frame = QFrame()
            frame.setObjectName("CardFrame")
            hbox = QHBoxLayout(frame)
            hbox.setContentsMargins(10, 5, 10, 5)

            lbl = QLabel(f"{chk['keybind']} ➔ [{chk['effect_type']}] {chk['match_name']}")
            lbl.setObjectName("CardLabel")
            lbl.setStyleSheet("color: #ccc; font-size: 14px;")
            
            btn_del = QPushButton("❌")
            btn_del.setObjectName("RegexDeleteBtn")
            btn_del.setFixedSize(36, 36)
            btn_del.clicked.connect(lambda checked, i=idx: self.delete_custom(i))

            hbox.addWidget(lbl)
            hbox.addStretch()
            hbox.addWidget(btn_del)
            self.custom_list_layout.addWidget(frame)

    def add_custom_ui(self):
        kb = self.custom_key_input.text().strip()
        search_str = self.custom_search.text().strip()
        if not kb or not search_str:
            return
            
        all_items = self.mw.all_effects + self.mw.all_presets
        found_item = None
        
        for item in all_items:
            e_type = item.get("type", "Unknown")
            m_name = item.get("matchName", "")
            
            # Robust matching: The completer formats it as "[Type] CleanName (matchName)"
            if m_name and search_str.endswith(f"({m_name})") and search_str.startswith(f"[{e_type}]"):
                found_item = {"type": e_type, "match_name": m_name}
                break

        if found_item:
            self.custom_hotkeys.append({
                "keybind": kb,
                "vk": self.custom_key_input.vk,
                "effect_type": found_item["type"],
                "match_name": found_item["match_name"]
            })
            self.render_custom_hotkeys()
            self.custom_key_input.clear()
            self.custom_key_input.vk = 0
            self.custom_search.clear()
            self.save_keybinds()
        else:
            self.mw.append_log("❌ Invalid effect format. Select from the dropdown.", "#ff5555")

    def delete_custom(self, index):
        if 0 <= index < len(self.custom_hotkeys):
            self.custom_hotkeys.pop(index)
            self.render_custom_hotkeys()
            self.save_keybinds()

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
                            
                    self.custom_hotkeys = data.get("custom_hotkeys", [])
                    self.render_custom_hotkeys()
            except Exception as e:
                self.mw.append_log(f"Error reading keybinds: {e}", "#ff5555")

    def save_keybinds(self):
        data = {act: inp.text() for act, inp in self.inputs.items()}
        data["custom_hotkeys"] = self.custom_hotkeys

        os.makedirs(get_data_path(), exist_ok=True)
        path = get_data_path("keybinds.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.mw.append_log("✅ Keymaps saved!", "#55ff55")
            self.mw.update_global_hotkey()
        except Exception as e:
            self.mw.append_log(f"❌ Error saving keybinds: {e}", "#ff5555")
