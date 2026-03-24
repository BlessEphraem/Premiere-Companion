# GUI/theme_page.py
import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt

class ThemePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.theme_path = os.path.join("Data", "theme.json")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl_title = QLabel("🎨 Theme Configuration")
        lbl_title.setObjectName("PageTitle")
        layout.addWidget(lbl_title)

        frame = QFrame()
        frame.setObjectName("CardFrame")
        vbox = QVBoxLayout(frame)

        # Info
        lbl_info = QLabel("Use HEX colors (e.g. #FF1796). You must restart the app to apply changes fully.")
        lbl_info.setObjectName("CardLabelSubtle")
        lbl_info.setWordWrap(True)
        vbox.addWidget(lbl_info)

        # --- Lecture intelligente des couleurs actuelles de l'utilisateur ---
        current_accent = "#FF1796"
        current_bg = "#09090b"
        if os.path.exists(self.theme_path):
            try:
                with open(self.theme_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    current_accent = data.get("accent", current_accent)
                    current_bg = data.get("bg", current_bg)
            except Exception:
                pass

        # Accent Color
        hbox_accent = QHBoxLayout()
        lbl_accent = QLabel("Accent Color (Pink):")
        lbl_accent.setObjectName("CardLabel")
        self.inp_accent = QLineEdit(current_accent)
        self.inp_accent.setFixedWidth(100)
        hbox_accent.addWidget(lbl_accent)
        hbox_accent.addStretch()
        hbox_accent.addWidget(self.inp_accent)
        vbox.addLayout(hbox_accent)

        # Background Color
        hbox_bg = QHBoxLayout()
        lbl_bg = QLabel("Main Background:")
        lbl_bg.setObjectName("CardLabel")
        self.inp_bg = QLineEdit(current_bg)
        self.inp_bg.setFixedWidth(100)
        hbox_bg.addWidget(lbl_bg)
        hbox_bg.addStretch()
        hbox_bg.addWidget(self.inp_bg)
        vbox.addLayout(hbox_bg)

        layout.addWidget(frame)

        # Save Button
        btn_save = QPushButton("💾 Save Theme")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_theme)
        layout.addWidget(btn_save)

        layout.addStretch()

    def save_theme(self):
        accent_color = self.inp_accent.text().strip()
        bg_color = self.inp_bg.text().strip()

        # Sauvegarde propre dans le fichier JSON
        theme_data = {"accent": accent_color, "bg": bg_color}
        os.makedirs("Data", exist_ok=True)
        
        with open(self.theme_path, "w", encoding="utf-8") as f:
            json.dump(theme_data, f, indent=4)

        self.mw.append_log(f"🎨 Theme updated (Accent: {accent_color}, BG: {bg_color}). Restart required.", "#55ff55")
        QMessageBox.information(self, "Success", "Theme saved successfully! Please restart the application.")
        self.close()