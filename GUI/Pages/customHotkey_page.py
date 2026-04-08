# GUI/customHotkey_page.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox, QFrame, QCompleter)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from Core.paths import get_data_path
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
from Core.configs.labels_config import get_type_codes, is_video, is_audio, is_transition, is_preset
import json
import os


from GUI.Widgets.hotkeyInputBox import KeybindCapture

class CustomKeybindInput(KeybindCapture):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Press Keybind")


class CustomHotkeyItemWidget(QWidget):
    def __init__(self, hotkey_data, list_widget, parent_page):
        super().__init__()
        self.hotkey_data = hotkey_data
        self.list_widget = list_widget
        self.parent_page = parent_page

        layout = QHBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"], THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"])

        display_text = f"{hotkey_data.get('keybind', '')}  |  [{hotkey_data.get('effect_type', '?')}] {hotkey_data.get('match_name', '?')}"
        lbl_text = QLabel(display_text)
        lbl_text.setObjectName("CardLabelSubtle")
        layout.addWidget(lbl_text, stretch=1)

        btn_del = QPushButton()
        btn_del.setIcon(icon("times-circle"))
        btn_del.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
        btn_del.setObjectName("RegexDeleteBtn")
        btn_del.clicked.connect(self.delete_hotkey)

        layout.addWidget(btn_del)

    def delete_hotkey(self):
        self.parent_page.custom_hotkeys.remove(self.hotkey_data)
        self.parent_page.save_and_reload()


class CustomSearchInput(QLineEdit):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.filter_types = ["All"] + get_type_codes()
        self.current_filter_idx = 0
        self.setPlaceholderText("Search (All)...")

        self.completer_obj = QCompleter()
        self.completer_obj.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer_obj.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer_obj)
        self.update_completer()

    def _is_qa_enabled(self):
        try:
            from Modules.apply_preset import PresetApplier
            cfg = PresetApplier.load_config()
            return bool(cfg and cfg.get("quick_apply_enabled", False))
        except Exception:
            return False

    def set_filter(self, filter_type):
        if filter_type in self.filter_types:
            self.current_filter_idx = self.filter_types.index(filter_type)
            self.setPlaceholderText(f"Search ({filter_type})...")
            self.update_completer()

    def update_completer(self):
        qa_enabled = self._is_qa_enabled()
        model = QStandardItemModel()
        all_items = self.mw.all_effects + self.mw.all_presets
        current_type = self.filter_types[self.current_filter_idx]

        for item in all_items:
            e_type = item.get("type", "Unknown")

            # Presets require QuickApply — hide them entirely if it's not configured/enabled
            if is_preset(e_type) and not qa_enabled:
                continue

            if current_type != "All":
                should_include = False
                if is_video(e_type) and current_type == "FX.V": should_include = True
                elif is_audio(e_type) and current_type == "FX.A": should_include = True
                elif is_transition(e_type) and current_type == "TR.V": should_include = True
                elif is_preset(e_type) and current_type == "PRST": should_include = True
                if not should_include: continue

            clean_name = self.mw.cleaner.clean_name(item.get("displayName", ""), e_type)
            m_name = item.get("matchName", "")
            display_str = f"[{e_type}] {clean_name} ({m_name})"
            model.appendRow(QStandardItem(display_str))

        self.completer_obj.setModel(model)


class CustomHotkeyPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.custom_hotkeys = []
        self.filter_options = ["All"] + get_type_codes()
        self.current_filter_idx = 0
        self.init_ui()
        self.load_custom_hotkeys()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"])
        main_layout.setSpacing(THEME_SPACING["spacing_element"])

        title = QLabel("Custom Hotkeys")
        title.setObjectName("SectionTitleFirst")
        main_layout.addWidget(title)

        desc = QLabel("Add custom keyboard shortcuts to quickly apply effects and presets.")
        desc.setObjectName("CardLabelSubtle")
        main_layout.addWidget(desc)

        add_frame = QFrame()
        add_frame.setObjectName("CardFrame")
        add_layout = QVBoxLayout(add_frame)
        add_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
        add_layout.setSpacing(THEME_SPACING["spacing_element"])

        input_row = QHBoxLayout()
        
        self.key_input = CustomKeybindInput()
        self.key_input.setFixedWidth(THEME_SPACING["width_input_keybind"])
        
        self.search_input = CustomSearchInput(self.mw)
        
        self.btn_filter = QPushButton("[All]")
        self.btn_filter.setObjectName("NavButton") 
        self.btn_filter.setFixedWidth(THEME_SPACING["width_button_small"])
        self.btn_filter.clicked.connect(self.cycle_filter)
        
        btn_add = QPushButton()
        btn_add.setIcon(icon("plus"))
        btn_add.setText(" Add")
        btn_add.clicked.connect(self.add_hotkey)

        input_row.addWidget(self.key_input)
        input_row.addWidget(self.search_input)
        input_row.addWidget(self.btn_filter)
        input_row.addWidget(btn_add)
        add_layout.addLayout(input_row)

        main_layout.addWidget(add_frame)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        main_layout.addWidget(self.list_widget)

        main_layout.addStretch()

    def cycle_filter(self):
        self.current_filter_idx = (self.current_filter_idx + 1) % len(self.filter_options)
        f_type = self.filter_options[self.current_filter_idx]
        self.btn_filter.setText(f"[{f_type}]")
        self.search_input.set_filter(f_type)

    def load_custom_hotkeys(self):
        path = get_data_path("keybinds.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.custom_hotkeys = data.get("custom_hotkeys", [])
                self.load_list_ui()
            except Exception as e:
                self.mw.append_log(f"Error loading custom hotkeys: {e}", THEME_USER_COLORS["error"])

    def load_list_ui(self):
        self.list_widget.clear()
        for hk in self.custom_hotkeys:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 40))
            widget = CustomHotkeyItemWidget(hk, self.list_widget, self)
            self.list_widget.setItemWidget(item, widget)

    def check_conflict(self, action_name, new_keybind):
        """Check against all listener hotkeys: custom, search bar, and Better Motion."""
        if not new_keybind:
            return None
        new_norm = new_keybind.strip().lower()

        # Custom hotkeys already saved
        for hk in self.custom_hotkeys:
            if hk.get("keybind", "").strip().lower() == new_norm:
                return f"Custom Hotkey ({hk.get('match_name', '?')})"

        # Search bar hotkey
        kb_path = get_data_path("keybinds.json")
        if os.path.exists(kb_path):
            try:
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb_data = json.load(f)
                search_key = kb_data.get("Run Search Bar", "")
                if search_key and search_key.strip().lower() == new_norm:
                    return "Run Search Bar"
            except Exception:
                pass

        # Better Motion hotkeys
        bm_path = get_data_path("betterMotion_config.json")
        if os.path.exists(bm_path):
            try:
                with open(bm_path, "r", encoding="utf-8") as f:
                    bm = json.load(f)
                for sec_key in ("position", "scale", "rotation", "opacity"):
                    sec = bm.get(sec_key, {})
                    for act_key, act_val in sec.items():
                        k = act_val.get("key", "") if isinstance(act_val, dict) else act_val
                        if k and k.strip().lower() == new_norm:
                            return f"Better Motion: {sec_key}.{act_key}"
            except Exception:
                pass

        return None

    def check_duplicate(self, new_keybind):
        return self.check_conflict("", new_keybind) is not None

    def add_hotkey(self):
        kb = self.key_input.text().strip()
        search_str = self.search_input.text().strip()
        
        if not kb or not search_str:
            return

        if self.check_duplicate(kb):
            QMessageBox.warning(
                self,
                "Hotkey Conflict",
                f"The hotkey '{kb}' is already in use by another custom hotkey. "
                f"Please choose a different hotkey."
            )
            return

        all_items = self.mw.all_effects + self.mw.all_presets
        found_item = None
        
        for item in all_items:
            e_type = item.get("type", "Unknown")
            m_name = item.get("matchName", "")
            
            if m_name and search_str.endswith(f"({m_name})") and search_str.startswith(f"[{e_type}]"):
                found_item = {"type": e_type, "match_name": m_name}
                break

        if not found_item:
            self.mw.append_log(" Invalid effect format. Select from the dropdown.", THEME_USER_COLORS["error"])
            return

        self.custom_hotkeys.append({
            "keybind": kb,
            "vk": self.key_input.vk,
            "effect_type": found_item["type"],
            "match_name": found_item["match_name"]
        })

        self.key_input.clear()
        self.search_input.clear()
        self.save_and_reload()

    def save_and_reload(self):
        path = get_data_path("keybinds.json")
        os.makedirs(get_data_path(), exist_ok=True)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
        
        data["custom_hotkeys"] = self.custom_hotkeys
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        self.load_list_ui()
        
        if hasattr(self.mw, 'update_global_hotkey'):
            self.mw.update_global_hotkey()
        
        self.mw.append_log(" Custom hotkeys saved!", THEME_USER_COLORS["success"])