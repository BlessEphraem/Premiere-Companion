# GUI/Pages/addons_page.py
import os
import json
from Core.paths import get_data_path
from Core.theme_qss import THEME_USER_COLORS, THEME_SPACING
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                             QPushButton)
from PyQt6.QtCore import Qt
from Core.functions.icon_loader import icon, icon_pixmap
from Modules.apply_preset import PresetApplier
from GUI.Pages.quickApply_page import QuickApplyWizard
from Core.functions.windows import create_window, apply_window_config


def get_theme_colors():
    colors = THEME_USER_COLORS.copy()
    theme_path = get_data_path("theme.json")
    if os.path.exists(theme_path):
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                colors.update(json.load(f))
        except Exception:
            pass
    return colors


class AddonsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.colors = get_theme_colors()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"])
        layout.setSpacing(THEME_SPACING["spacing_element"])

        # ── Quick Apply (Presets) Card ────────────────────────────────────────
        qa_card = QFrame()
        qa_card.setObjectName("CardFrame")
        qa_layout = QVBoxLayout(qa_card)
        qa_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])

        qa_title_layout = QHBoxLayout()
        qa_title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_qa_icon = QLabel()
        lbl_qa_icon.setPixmap(icon_pixmap("magic", size=THEME_SPACING["icon_medium"]))
        lbl_qa_icon.setFixedSize(THEME_SPACING["icon_medium"], THEME_SPACING["icon_medium"])
        lbl_qa_icon.setScaledContents(True)
        lbl_qa_title = QLabel("Quick Apply (Presets)")
        lbl_qa_title.setObjectName("CardLabelBold")
        qa_title_layout.addWidget(lbl_qa_icon)
        qa_title_layout.addWidget(lbl_qa_title)
        qa_title_layout.addStretch()
        qa_layout.addLayout(qa_title_layout)

        lbl_qa_desc = QLabel("Bypass drag-and-drop. Requires screen calibration.")
        lbl_qa_desc.setObjectName("CardLabelSubtle")
        qa_layout.addWidget(lbl_qa_desc)

        hbox_qa = QHBoxLayout()
        hbox_qa.setSpacing(THEME_SPACING["spacing_element"])
        
        self.btn_config_qa = QPushButton()
        self.btn_config_qa.setIcon(icon("cog"))
        self.btn_config_qa.setText(" Configure")
        self.btn_config_qa.setFixedWidth(THEME_SPACING["width_button_medium"])
        self.btn_config_qa.clicked.connect(self.open_qa_config)

        self.btn_keybinds_qa = QPushButton()
        self.btn_keybinds_qa.setIcon(icon("keyboard"))
        self.btn_keybinds_qa.setText(" Keybinds")
        self.btn_keybinds_qa.setFixedWidth(THEME_SPACING["width_button_medium"])
        self.btn_keybinds_qa.clicked.connect(self.open_premiere_keybinds)
        
        self.btn_toggle_qa = QPushButton()
        self.btn_toggle_qa.setObjectName("Toggle")
        self.btn_toggle_qa.setFixedWidth(THEME_SPACING["width_button_small"])
        self.btn_toggle_qa.clicked.connect(self.toggle_quick_apply)
        
        hbox_qa.addWidget(self.btn_config_qa)
        hbox_qa.addWidget(self.btn_keybinds_qa)
        hbox_qa.addWidget(self.btn_toggle_qa)
        hbox_qa.addStretch()
        qa_layout.addLayout(hbox_qa)
        
        layout.addWidget(qa_card)

        # ── Better Motion Card ────────────────────────────────────────────────
        bm_card = QFrame()
        bm_card.setObjectName("CardFrame")
        bm_layout = QVBoxLayout(bm_card)
        bm_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])

        bm_title_layout = QHBoxLayout()
        bm_title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_bm_icon = QLabel()
        lbl_bm_icon.setPixmap(icon_pixmap("magic", size=THEME_SPACING["icon_medium"]))
        lbl_bm_icon.setFixedSize(THEME_SPACING["icon_medium"], THEME_SPACING["icon_medium"])
        lbl_bm_icon.setScaledContents(True)
        lbl_bm_title = QLabel("Better Motion")
        lbl_bm_title.setObjectName("CardLabelBold")
        bm_title_layout.addWidget(lbl_bm_icon)
        bm_title_layout.addWidget(lbl_bm_title)
        bm_title_layout.addStretch()
        bm_layout.addLayout(bm_title_layout)

        lbl_bm_desc = QLabel("Change any motion property of a clip.\nExample: Alt+S to change scale (Move mouse to increase/decrease).")
        lbl_bm_desc.setObjectName("CardLabelSubtle")
        bm_layout.addWidget(lbl_bm_desc)

        hbox_bm = QHBoxLayout()
        hbox_bm.setSpacing(THEME_SPACING["spacing_element"])
        
        self.btn_config_bm = QPushButton()
        self.btn_config_bm.setIcon(icon("cog"))
        self.btn_config_bm.setText(" Configure")
        self.btn_config_bm.setFixedWidth(THEME_SPACING["width_button_medium"])
        self.btn_config_bm.clicked.connect(self.open_bm_config)
        
        self.btn_toggle_bm = QPushButton()
        self.btn_toggle_bm.setObjectName("Toggle")
        self.btn_toggle_bm.setFixedWidth(THEME_SPACING["width_button_small"])
        self.btn_toggle_bm.clicked.connect(self.toggle_better_motion)
        
        hbox_bm.addWidget(self.btn_config_bm)
        hbox_bm.addWidget(self.btn_toggle_bm)
        hbox_bm.addStretch()
        bm_layout.addLayout(hbox_bm)
        
        layout.addWidget(bm_card)

        # ── Custom Hotkeys Card ───────────────────────────────────────────────
        custom_btn_card = QFrame()
        custom_btn_card.setObjectName("CardFrame")
        custom_btn_layout = QVBoxLayout(custom_btn_card)
        custom_btn_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
        custom_btn_layout.setSpacing(THEME_SPACING["spacing_element"])

        lbl_custom = QLabel("Custom Hotkeys")
        lbl_custom.setObjectName("CardLabelBold")
        custom_btn_layout.addWidget(lbl_custom)

        desc_custom = QLabel("Add custom shortcuts to quickly apply effects and presets.")
        desc_custom.setObjectName("CardLabelSubtle")
        custom_btn_layout.addWidget(desc_custom)

        btn_custom = QPushButton()
        btn_custom.setIcon(icon("plus", size=THEME_SPACING["icon_medium"]))
        btn_custom.setText(" Manage Custom Hotkeys")
        btn_custom.clicked.connect(self.open_custom_hotkey)
        custom_btn_layout.addWidget(btn_custom)

        layout.addWidget(custom_btn_card)

        layout.addStretch()

    def open_premiere_keybinds(self):
        dialog = create_window("premiere_keybinds", self.mw, modal=True)
        if dialog:
            dialog.exec()

    def open_custom_hotkey(self):
        dialog = create_window("custom_hotkey", self.mw, modal=True)
        if dialog:
            dialog.exec()

    def open_qa_config(self):
        wizard = QuickApplyWizard(self.mw)
        apply_window_config(wizard, "quick_apply", "Configuration: Quick Apply for Presets")
        self.mw.register_child_window(wizard)
        if wizard.exec():
            self.update_qa_ui()

    def toggle_quick_apply(self):
        config = PresetApplier.load_config()
        is_enabled = config.get("quick_apply_enabled", False) if config else False
        has_capture = config and "mouse_x" in config and "mouse_y" in config

        if not is_enabled:
            if not has_capture:
                self.open_qa_config()
                return

        config = config or {}
        was_disabled = not is_enabled
        config["quick_apply_enabled"] = not is_enabled
        PresetApplier.save_config(config)
        self.update_qa_ui()
        state = "ENABLED" if config["quick_apply_enabled"] else "DISABLED"
        self.mw.append_log(f" Quick Apply {state}", THEME_USER_COLORS["info"])

        if hasattr(self.mw, "reload_commands"):
            self.mw.reload_commands()

        if was_disabled and config["quick_apply_enabled"] and has_capture:
            self.mw.append_log(" QuickApply enabled. Triggering sync...", THEME_USER_COLORS["info"])
            self.mw.trigger_sync()

    def update_qa_ui(self):
        config = PresetApplier.load_config()
        is_enabled = config.get("quick_apply_enabled", False) if config else False
        self.btn_toggle_qa.setText("Toggle : Enable" if is_enabled else "Toggle : Disable")
        self.btn_toggle_qa.setProperty("qa_state", "enabled" if is_enabled else "disabled")
        self.btn_toggle_qa.style().unpolish(self.btn_toggle_qa)
        self.btn_toggle_qa.style().polish(self.btn_toggle_qa)

    def open_bm_config(self):
        from GUI.Pages.betterMotion_page import BetterMotionPage
        wizard = BetterMotionPage(self.mw)
        apply_window_config(wizard, "better_motion", "Configuration: Better Motion")
        self.mw.register_child_window(wizard)
        wizard.exec()

    def toggle_better_motion(self):
        path = get_data_path("betterMotion_config.json")
        config = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except:
                pass
        
        is_enabled = config.get("enabled", False)
        
        if not is_enabled:
            has_hotkeys = False
            for sec_key in ("position", "scale", "rotation", "opacity"):
                for act_key, act_val in config.get(sec_key, {}).items():
                    k = act_val.get("key", "") if isinstance(act_val, dict) else act_val
                    if k:
                        has_hotkeys = True
                        break
                if has_hotkeys:
                    break
                    
            if not has_hotkeys:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.mw, 
                    "Better Motion", 
                    "Veuillez d'abord configurer au moins un raccourci pour Better Motion."
                )
                self.open_bm_config()
                return

        config["enabled"] = not is_enabled
        
        os.makedirs(get_data_path(), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        
        self.update_bm_ui()
        state = "ENABLED" if config["enabled"] else "DISABLED"
        self.mw.append_log(f" Better Motion {state}", THEME_USER_COLORS["info"])

        if hasattr(self.mw, "reload_commands"):
            self.mw.reload_commands()

        if hasattr(self.mw, 'update_global_hotkey'):
            self.mw.update_global_hotkey()

    def update_bm_ui(self):
        path = get_data_path("betterMotion_config.json")
        is_enabled = False
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    is_enabled = json.load(f).get("enabled", False)
            except:
                pass
        
        self.btn_toggle_bm.setText("Toggle : Enable" if is_enabled else "Toggle : Disable")
        self.btn_toggle_bm.setProperty("qa_state", "enabled" if is_enabled else "disabled")
        self.btn_toggle_bm.style().unpolish(self.btn_toggle_bm)
        self.btn_toggle_bm.style().polish(self.btn_toggle_bm)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_qa_ui()
        self.update_bm_ui()
