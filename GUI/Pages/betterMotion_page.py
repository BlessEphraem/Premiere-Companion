# GUI/Pages/betterMotion_page.py
import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QHBoxLayout,
                             QPushButton, QLineEdit, QMessageBox, QFrame, QSpinBox, QScrollArea, QWidget, QCheckBox, QComboBox)
from PyQt6.QtCore import Qt
from Core.paths import get_data_path
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS

from GUI.Widgets.hotkeyInputBox import KeybindCapture

class BMKeybindInput(KeybindCapture):
    pass

class BetterMotionPage(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.setModal(True)
        self.inputs = {}
        self.amounts = {}
        self.axis_combos = {}
        self.invert_checks = {}
        self.init_ui()
        self.load_config()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"])
        layout.setSpacing(THEME_SPACING["spacing_element"])

        title_layout = QHBoxLayout()
        title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_icon = QLabel()
        lbl_icon.setPixmap(icon_pixmap("magic", size=THEME_SPACING["icon_large"]))
        lbl_icon.setFixedSize(THEME_SPACING["icon_large"], THEME_SPACING["icon_large"])
        lbl_icon.setScaledContents(True)
        lbl_title = QLabel("Better Motion")
        lbl_title.setObjectName("PageTitle")
        title_layout.addWidget(lbl_icon)
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        desc = QLabel("Configure shortcuts to interact with Premiere Pro's motion properties.\nPress Backspace or Delete to clear a hotkey.")
        desc.setObjectName("CardLabelSubtle")
        layout.addWidget(desc)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TransparentScroll")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_content.setObjectName("TransparentContainer")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(14)

        # ── Better Transform (top-level hotkey) ──────────────────────────────
        bt_frame = QFrame()
        bt_frame.setObjectName("CardFrame")
        bt_layout = QVBoxLayout(bt_frame)
        bt_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
        bt_layout.setSpacing(THEME_SPACING["spacing_element"])

        bt_lbl = QLabel("Better Transform")
        bt_lbl.setObjectName("SectionTitle")
        bt_layout.addWidget(bt_lbl)

        bt_desc = QLabel("All-in-one interactive mode: Position by default, hold RMB for Rotation, hold MMB for Scale.")
        bt_desc.setObjectName("CardLabelSubtle")
        bt_desc.setWordWrap(True)
        bt_layout.addWidget(bt_desc)

        bt_row = QHBoxLayout()
        bt_row.setSpacing(THEME_SPACING["spacing_element"])
        bt_row_lbl = QLabel("Hotkey")
        bt_row_lbl.setObjectName("CardLabel")
        bt_row_lbl.setFixedWidth(80)
        bt_inp = BMKeybindInput(action_name="better_transform")
        bt_inp.setFixedWidth(THEME_SPACING["width_input_keybind"])
        bt_inp.setPlaceholderText("Click to bind")
        self.inputs["better_transform"] = bt_inp
        bt_row.addWidget(bt_row_lbl)
        bt_row.addWidget(bt_inp)
        bt_row.addStretch()
        bt_layout.addLayout(bt_row)

        scroll_layout.addWidget(bt_frame)

        sections = [
            ("Position", "position", [
                ("Adjust", "adjust", None),
                ("Reset", "reset", None),
                ("X Add", "x_add", (0, 1000)),
                ("X Sub", "x_sub", (-1000, 0)),
                ("Y Add", "y_add", (0, 1000)),
                ("Y Sub", "y_sub", (-1000, 0))
            ]),
            ("Scale", "scale", [
                ("Adjust", "adjust", None),
                ("Reset", "reset", None),
                ("Add", "add", (0, 1000)),
                ("Sub", "sub", (-1000, 0))
            ]),
            ("Rotation", "rotation", [
                ("Adjust", "adjust", None),
                ("Reset", "reset", None),
                ("Add", "add", (0, 1000)),
                ("Sub", "sub", (-1000, 0))
            ]),
            ("Opacity", "opacity", [
                ("Adjust", "adjust", None),
                ("Reset", "reset", None),
                ("Add", "add", (0, 1000)),
                ("Sub", "sub", (-1000, 0))
            ])
        ]

        for sec_title, sec_key, actions in sections:
            sec_frame = QFrame()
            sec_frame.setObjectName("CardFrame")
            sec_layout = QVBoxLayout(sec_frame)
            sec_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
            sec_layout.setSpacing(THEME_SPACING["spacing_element"])

            sec_lbl = QLabel(sec_title)
            sec_lbl.setObjectName("SectionTitle")
            sec_layout.addWidget(sec_lbl)

            # Mouse axis/invert control — for all non-position props
            if sec_key in ("scale", "rotation", "opacity"):
                axis_row = QHBoxLayout()
                axis_row.setSpacing(THEME_SPACING["spacing_element"])
                axis_lbl = QLabel("Mouse Axis")
                axis_lbl.setObjectName("CardLabel")
                axis_lbl.setFixedWidth(80)
                axis_combo = QComboBox()
                axis_combo.addItems(["Horizontal", "Vertical"])
                axis_combo.setFixedWidth(120)
                invert_chk = QCheckBox("Invert")
                invert_chk.setObjectName("SubtleCheckbox")
                self.axis_combos[sec_key] = axis_combo
                self.invert_checks[sec_key] = invert_chk
                axis_row.addWidget(axis_lbl)
                axis_row.addWidget(axis_combo)
                axis_row.addWidget(invert_chk)
                axis_row.addStretch()
                sec_layout.addLayout(axis_row)

            for act_title, act_key, amount_range in actions:
                full_key = f"{sec_key}.{act_key}"
                
                row = QHBoxLayout()
                row.setSpacing(THEME_SPACING["spacing_element"])
                lbl = QLabel(act_title)
                lbl.setObjectName("CardLabel")
                lbl.setFixedWidth(80)
                
                inp = BMKeybindInput(action_name=full_key)
                inp.setFixedWidth(THEME_SPACING["width_input_keybind"])
                inp.setPlaceholderText("Click to bind")
                self.inputs[full_key] = inp
                
                row.addWidget(lbl)
                row.addWidget(inp)

                if amount_range is not None:
                    amt_lbl = QLabel("Amount:")
                    amt_lbl.setObjectName("CardLabelSubtle")
                    amt_spin = QSpinBox()
                    amt_spin.setRange(amount_range[0], amount_range[1])
                    amt_spin.setFixedWidth(80)
                    self.amounts[full_key] = amt_spin
                    row.addWidget(amt_lbl)
                    row.addWidget(amt_spin)
                
                row.addStretch()
                sec_layout.addLayout(row)
            
            scroll_layout.addWidget(sec_frame)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        live_frame = QFrame()
        live_frame.setObjectName("CardFrame")
        live_layout = QVBoxLayout(live_frame)
        live_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
        live_layout.setSpacing(THEME_SPACING["spacing_element"])

        self.chk_live_motion = QCheckBox("Enable Live Motion")
        self.chk_live_motion.setObjectName("CardLabelBold")
        live_layout.addWidget(self.chk_live_motion)

        lbl_live_warning = QLabel(
            "Allows you to see the current editing in real time in the Premiere Pro monitor."
            "Use with caution: since undo grouping is not possible due to API limitations,"
            "you will need to press Ctrl+Z multiple times to undo the changes."
            "Tips -> Use 'Reset' hotkeys."
        )
        lbl_live_warning.setObjectName("CardLabelSubtle")
        lbl_live_warning.setWordWrap(True)
        live_layout.addWidget(lbl_live_warning)

        layout.addWidget(live_frame)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_save = QPushButton()
        btn_save.setIcon(icon("save"))
        btn_save.setText(" Save Configuration")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_config)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def check_conflict(self, action_name, new_keybind):
        if not new_keybind:
            return None
            
        new_norm = new_keybind.strip().lower()
        for act, inp in self.inputs.items():
            if act != action_name and inp.text():
                if inp.text().strip().lower() == new_norm:
                    return act
                    
        from Core.paths import get_data_path
        kb_path = get_data_path("keybinds.json")
        legacy_kb_path = get_data_path("pr_keybinds.json")
        search_str = "Ctrl+Space"
        custom_hotkeys = []

        path_to_load = kb_path
        if not os.path.exists(kb_path) and os.path.exists(legacy_kb_path):
            path_to_load = legacy_kb_path

        if os.path.exists(path_to_load):
            try:
                with open(path_to_load, "r", encoding="utf-8") as f:
                    keybinds = json.load(f)
                search_str = keybinds.get("Run Search Bar", "Ctrl+Space")
                custom_hotkeys = keybinds.get("custom_hotkeys", [])
            except Exception:
                pass
                
        if search_str and search_str.strip().lower() == new_norm:
            return "Run Search Bar"
            
        for chk in custom_hotkeys:
            existing = chk.get("keybind", "")
            if existing and new_norm == existing.strip().lower():
                return f"Custom Hotkey ({chk.get('match_name', 'Unknown')})"
                
        return None

    def load_config(self):
        path = get_data_path("betterMotion_config.json")
        if not os.path.exists(path):
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.chk_live_motion.setChecked(data.get("live_motion", False))

            bt_data = data.get("better_transform", {})
            if isinstance(bt_data, dict) and "better_transform" in self.inputs:
                self.inputs["better_transform"].setText(bt_data.get("key", ""))
                self.inputs["better_transform"].vk = bt_data.get("vk", 0)

            _axis_defaults = {"scale": "vertical", "rotation": "horizontal", "opacity": "vertical"}
            for sec_key in ["position", "scale", "rotation", "opacity"]:
                if sec_key in data:
                    sec_data = data[sec_key]
                    for act_key, act_val in sec_data.items():
                        full_key = f"{sec_key}.{act_key}"
                        if isinstance(act_val, dict):
                            if full_key in self.inputs:
                                self.inputs[full_key].setText(act_val.get("key", ""))
                                self.inputs[full_key].vk = act_val.get("vk", 0)
                            if full_key in self.amounts:
                                self.amounts[full_key].setValue(act_val.get("amount", 0))
                        else:
                            if full_key in self.inputs:
                                self.inputs[full_key].setText(act_val)
                    # Load axis/invert for non-position sections
                    if sec_key in self.axis_combos:
                        axis_val = sec_data.get("axis", _axis_defaults.get(sec_key, "horizontal"))
                        self.axis_combos[sec_key].setCurrentIndex(0 if axis_val == "horizontal" else 1)
                        self.invert_checks[sec_key].setChecked(sec_data.get("invert", False))
        except Exception as e:
            self.mw.append_log(f"Error loading Better Motion config: {e}", THEME_USER_COLORS["error"])

    def save_config(self):
        path = get_data_path("betterMotion_config.json")
        os.makedirs(get_data_path(), exist_ok=True)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"enabled": False}
            
        data["live_motion"] = self.chk_live_motion.isChecked()

        if "better_transform" in self.inputs:
            inp = self.inputs["better_transform"]
            data["better_transform"] = {
                "key": inp.text().strip(),
                "vk": inp.vk if hasattr(inp, "vk") else 0
            }

        for sec_key in ["position", "scale", "rotation", "opacity"]:
            if sec_key not in data:
                data[sec_key] = {}

        for full_key, inp in self.inputs.items():
            if "." not in full_key:
                continue  # top-level keys (e.g. better_transform) handled separately
            sec_key, act_key = full_key.split(".")
            key_val = inp.text().strip()
            vk_val = inp.vk if hasattr(inp, 'vk') else 0

            if full_key in self.amounts:
                data[sec_key][act_key] = {
                    "key": key_val,
                    "vk": vk_val,
                    "amount": self.amounts[full_key].value()
                }
            else:
                data[sec_key][act_key] = {
                    "key": key_val,
                    "vk": vk_val
                }

        # Save axis/invert per section
        for sec_key, combo in self.axis_combos.items():
            if sec_key not in data:
                data[sec_key] = {}
            data[sec_key]["axis"] = "horizontal" if combo.currentIndex() == 0 else "vertical"
            data[sec_key]["invert"] = self.invert_checks[sec_key].isChecked()

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.mw.append_log(" Better Motion Configuration saved!", THEME_USER_COLORS["success"])
            if hasattr(self.mw, 'update_global_hotkey'):
                self.mw.update_global_hotkey()
            if hasattr(self.mw, 'reload_commands'):
                self.mw.reload_commands()
            self.accept()
        except Exception as e:
            self.mw.append_log(f" Error saving Better Motion config: {e}", THEME_USER_COLORS["error"])
