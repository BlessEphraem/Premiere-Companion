# GUI/theme_page.py
import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton, QLineEdit, QMessageBox, QScrollArea, QCheckBox, QApplication
from PyQt6.QtCore import Qt, QTimer
from Core.paths import get_data_path

class ThemePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.theme_path = get_data_path("theme.json")
        self.inputs = {}
        
        # Define all configurable theme properties and their defaults
        self.theme_schema = [
            ("accent", "Accent Color (Pink):", "#FF1796"),
            ("bg", "Main Background:", "#09090b"),
            ("bg_secondary", "Secondary Background (Inputs):", "#18181b"),
            ("card_bg", "Card Background (Lists):", "#121214"),
            ("border", "Border Color:", "#27272a"),
            ("text_main", "Main Text Color:", "#e4e4e7"),
            ("text_subtle", "Subtle Text Color:", "#a1a1aa"),
            ("success", "Success Color (Audio):", "#55ff55"),
            ("error", "Error Color (Video):", "#ff5555"),
            ("info", "Info Color (Transition):", "#55ccff"),
            ("warning", "Warning Color:", "#ffaa00"),
            ("primary_btn", "Primary Button Color:", "#3b82f6"),
            ("accent_btn", "Accent Button Color:", "#aa00ff")
        ]
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        lbl_title = QLabel("🎨 Theme Configuration")
        lbl_title.setObjectName("PageTitle")
        main_layout.addWidget(lbl_title)

        # Info
        lbl_info = QLabel("Use HEX colors (e.g. #FF1796). You must restart the app to apply changes fully.")
        lbl_info.setObjectName("CardLabelSubtle")
        lbl_info.setWordWrap(True)
        main_layout.addWidget(lbl_info)

        # Live Refresh
        self.chk_live = QCheckBox("Live Refresh (Preview changes immediately)")
        self.chk_live.setChecked(False)
        self.chk_live.setObjectName("SubtleCheckbox")
        self.chk_live.stateChanged.connect(self.on_live_toggle)
        main_layout.addWidget(self.chk_live)

        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.apply_live_theme)

        # Scroll Area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TransparentScroll")
        
        scroll_content = QWidget()
        scroll_content.setObjectName("TransparentContainer")
        vbox = QVBoxLayout(scroll_content)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(10)

        # Load current data
        current_data = {}
        if os.path.exists(self.theme_path):
            try:
                with open(self.theme_path, "r", encoding="utf-8") as f:
                    current_data = json.load(f)
            except Exception:
                pass

        # Build form rows dynamically
        for key, label_text, default_val in self.theme_schema:
            frame = QFrame()
            frame.setObjectName("CardFrame")
            hbox = QHBoxLayout(frame)
            
            lbl = QLabel(label_text)
            lbl.setObjectName("CardLabel")
            
            val = current_data.get(key, default_val)
            inp = QLineEdit(val)
            inp.setFixedWidth(120)
            inp.textChanged.connect(self.on_text_changed)
            
            self.inputs[key] = inp
            
            hbox.addWidget(lbl)
            hbox.addStretch()
            hbox.addWidget(inp)
            vbox.addWidget(frame)

        vbox.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Save Button
        btn_save = QPushButton("💾 Save Theme")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_theme)
        main_layout.addWidget(btn_save)

    def on_live_toggle(self):
        if self.chk_live.isChecked():
            self.apply_live_theme()

    def on_text_changed(self):
        if self.chk_live.isChecked():
            self.refresh_timer.start(500)

    def apply_live_theme(self):
        # Gather current values, falling back to defaults if empty
        theme_data = {}
        for key, _, default_val in self.theme_schema:
            val = self.inputs[key].text().strip()
            theme_data[key] = val if val else default_val

        ACCENT = theme_data.get("accent", "#FF1796")
        BG = theme_data.get("bg", "#09090b")
        BG_SEC = theme_data.get("bg_secondary", "#18181b")
        CARD_BG = theme_data.get("card_bg", "#121214")
        BORDER = theme_data.get("border", "#27272a")
        TEXT = theme_data.get("text_main", "#e4e4e7")
        TEXT_SUBTLE = theme_data.get("text_subtle", "#a1a1aa")
        SUCCESS = theme_data.get("success", "#55ff55")
        ERROR = theme_data.get("error", "#ff5555")
        INFO = theme_data.get("info", "#55ccff")
        WARNING = theme_data.get("warning", "#ffaa00")
        PRIMARY_BTN = theme_data.get("primary_btn", "#3b82f6")
        ACCENT_BTN = theme_data.get("accent_btn", "#aa00ff")

        dynamic_qss = f"""
        QMainWindow, QWidget {{ background-color: {BG}; color: {TEXT}; font-family: "Inter", "Segoe UI", "-apple-system", "Helvetica Neue", sans-serif; font-size: 14px; }}
        QLabel {{ background-color: transparent; color: {TEXT}; font-weight: 500; }}
        QLineEdit, QComboBox, QSpinBox {{ background-color: {BG_SEC}; color: #ffffff; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px 14px; }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {ACCENT}; background-color: #202024; }}
        QPushButton {{ background-color: {BG_SEC}; color: #fafafa; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px 16px; font-weight: 600; font-size: 13px; }}
        QPushButton:hover {{ background-color: {BORDER}; border: 1px solid #3f3f46; }}
        QPushButton:pressed {{ background-color: {BG_SEC}; border: 1px solid {ACCENT}; color: {ACCENT}; }}
        QListWidget, QTextEdit, QScrollArea {{ background-color: {BG}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; outline: none; color: #ffffff; font-size: 15px; font-weight: 600; }}
        QListWidget::item {{ background-color: {CARD_BG}; border: 1px solid {BG_SEC}; border-radius: 8px; margin: 4px; padding-left: 15px; min-height: 40px; }}
        QListWidget::item:hover {{ background-color: {BG_SEC}; border: 1px solid {BORDER}; }}
        QListWidget::item:selected {{ background-color: #1e293b; border: 1px solid {ACCENT}; color: #ffffff; }}
        QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; border-radius: 4px; }}
        QScrollBar::handle:vertical {{ background: #3f3f46; min-height: 30px; border-radius: 4px; }}
        QScrollBar::handle:vertical:hover {{ background: #52525b; }}
        QFrame#separatorLine {{ background-color: {BORDER}; max-height: 1px; }}
        QLabel#PageTitle {{ font-size: 22px; font-weight: bold; color: #ffffff; }}
        QFrame#CardFrame {{ background-color: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 8px; }}
        QLabel#CardLabel {{ font-weight: bold; font-size: 14px; border: none; }}
        QLabel#CardLabelBold {{ font-size: 16px; font-weight: bold; border: none; }}
        QLabel#CardLabelSubtle {{ color: {TEXT_SUBTLE}; border: none; }}
        QLabel#WarningLabel {{ color: {WARNING}; font-style: italic; font-size: 12px; }}
        QCheckBox#SubtleCheckbox {{ border: none; color: {TEXT_SUBTLE}; font-weight: bold; }}
        QScrollArea#TransparentScroll, QWidget#TransparentContainer, QWidget#effectItem, QWidget#FloatingSearchBar {{ background: transparent; border: none; }}
        QPushButton#PrimaryButton {{ background-color: {PRIMARY_BTN}; border: none; font-size: 16px; padding: 10px; font-weight: bold; }}
        QPushButton#PrimaryButton:hover {{ background-color: #2563eb; }}
        QPushButton#AccentButton {{ background-color: {ACCENT_BTN}; border: none; color: white; font-size: 14px; font-weight: bold; padding: 10px; }}
        QPushButton#AccentButton:hover {{ background-color: #9000d8; }}
        QPushButton#NavButton[active="true"] {{ background-color: {ACCENT}; border: none; font-weight: bold; }}
        QPushButton#ToggleQA[qa_state="enabled"] {{ background-color: {SUCCESS}; color: black; font-weight: bold; padding: 5px; border: none; }}
        QPushButton#ToggleQA[qa_state="disabled"] {{ background-color: {ERROR}; color: white; font-weight: bold; padding: 5px; border: none; }}
        QLabel#EffectTag {{ font-weight: bold; font-size: 14px; margin-right: 5px; }}
        QLabel#EffectTag[type="TagVideo"]      {{ color: {ERROR}; }}
        QLabel#EffectTag[type="TagAudio"]      {{ color: {SUCCESS}; }}
        QLabel#EffectTag[type="TagTransition"] {{ color: {INFO}; }}
        QLabel#EffectTag[type="TagPreset"]     {{ color: #ffffff; }}
        QLabel#EffectTag[type="TagRecent"]     {{ color: {WARNING}; }}
        QLabel#EffectTag[type="unknown"]       {{ color: {PRIMARY_BTN}; }}
        QLabel#StatusLabel[connected="true"] {{ color: {SUCCESS}; font-weight: bold; }}
        QLabel#StatusLabel[connected="false"] {{ color: {ERROR}; font-weight: bold; }}
        QLabel#CoordLabel[state="undefined"] {{ color: {WARNING}; font-weight: bold; font-size: 14px; }}
        QLabel#CoordLabel[state="saved"] {{ color: {SUCCESS}; font-weight: bold; font-size: 14px; }}
        QFrame#SearchBarContainer {{ background-color: rgba(30, 30, 30, 240); border: 1px solid #555555; border-radius: 12px; }}
        QListWidget#SearchList {{ background-color: transparent; border: none; color: #dddddd; font-size: 14px; outline: none; }}
        QListWidget#SearchList::item:selected {{ background-color: #005577; color: white; border: 1px solid #0077aa; }}
        QLineEdit#MainSearchBar {{ background-color: {BG_SEC}; color: #ffffff; border-radius: 8px; padding: 10px 14px; font-weight: bold; }}
        QLineEdit#MainSearchBar:focus {{ background-color: #202024; }}
        QLineEdit#MainSearchBar[filterType="All"] {{ border: 2px solid {PRIMARY_BTN}; }}
        QLineEdit#MainSearchBar[filterType="FxVideo"] {{ border: 2px solid {ERROR}; }}
        QLineEdit#MainSearchBar[filterType="FxAudio"] {{ border: 2px solid {SUCCESS}; }}
        QLineEdit#MainSearchBar[filterType="Transition"] {{ border: 2px solid {INFO}; }}
        QLineEdit#MainSearchBar[filterType="Preset"] {{ border: 2px solid #ffffff; }}
        QLineEdit#SearchInput {{ background-color: rgba(15, 15, 15, 200); color: #ffffff; border-radius: 8px; padding: 12px 15px; font-size: 16px; font-weight: bold; }}
        QLineEdit#SearchInput[filterType="All"] {{ border: 1px solid {PRIMARY_BTN}; }}
        QLineEdit#SearchInput[filterType="FxVideo"] {{ border: 1px solid {ERROR}; }}
        QLineEdit#SearchInput[filterType="FxAudio"] {{ border: 1px solid {SUCCESS}; }}
        QLineEdit#SearchInput[filterType="Transition"] {{ border: 1px solid {INFO}; }}
        QLineEdit#SearchInput[filterType="Preset"] {{ border: 1px solid #ffffff; }}
        QLineEdit#SearchInput[mode="options"] {{ border: 2px solid {INFO}; background-color: rgba(15, 15, 15, 200); color: white; }}
        QLabel#SearchResultName {{ color: {TEXT}; font-size: 15px; font-weight: bold; }}
        QLabel#RegexRuleText {{ color: {TEXT}; font-size: 14px; background: transparent; }}
        """
        QApplication.instance().setStyleSheet(dynamic_qss)

    def save_theme(self):
        theme_data = {}
        for key, _, _ in self.theme_schema:
            theme_data[key] = self.inputs[key].text().strip()

        os.makedirs(get_data_path(), exist_ok=True)

        try:
            with open(self.theme_path, "w", encoding="utf-8") as f:
                json.dump(theme_data, f, indent=4)
            self.mw.append_log(f"🎨 Theme updated successfully. Restart required.", "#55ff55") 
            QMessageBox.information(self, "Success", "Theme saved successfully! Please restart the application.")
        except Exception as e:
            self.mw.append_log(f"❌ Error saving theme: {e}", "#ff5555")