import os
import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt

class ThemePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.style_path = os.path.join("Data", "style.qss")
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

        # Accent Color
        hbox_accent = QHBoxLayout()
        lbl_accent = QLabel("Accent Color (Pink):")
        lbl_accent.setObjectName("CardLabel")
        self.inp_accent = QLineEdit("#FF1796")
        self.inp_accent.setFixedWidth(100)
        hbox_accent.addWidget(lbl_accent)
        hbox_accent.addStretch()
        hbox_accent.addWidget(self.inp_accent)
        vbox.addLayout(hbox_accent)

        # Background Color
        hbox_bg = QHBoxLayout()
        lbl_bg = QLabel("Main Background:")
        lbl_bg.setObjectName("CardLabel")
        self.inp_bg = QLineEdit("#09090b")
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

        if not os.path.exists(self.style_path):
            QMessageBox.warning(self, "Error", "style.qss not found!")
            return

        # QSS Reading
        with open(self.style_path, "r", encoding="utf-8") as f:
            content = f.read()

        content = re.sub(r"#[A-Fa-f0-9]{6}(?=;|\s+\})", lambda m: accent_color if m.group(0).lower() == "#ff1796" else m.group(0), content)
        content = re.sub(r"#[A-Fa-f0-9]{6}(?=;|\s+\})", lambda m: bg_color if m.group(0).lower() == "#09090b" else m.group(0), content)

        # Écriture
        with open(self.style_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.mw.append_log(f"🎨 Theme updated (Accent: {accent_color}, BG: {bg_color}). Restart required.", "#55ff55")
        QMessageBox.information(self, "Success", "Theme saved successfully! Please restart the application.")
        self.close()