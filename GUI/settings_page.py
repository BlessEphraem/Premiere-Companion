# GUI/settings_page.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from GUI.quickApply_window import QuickApplyWizard
from GUI.theme_page import ThemePage

class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Settings (Title)
        lbl_title = QLabel("⚙️ Settings")
        lbl_title.setObjectName("PageTitle")
        layout.addWidget(lbl_title)

        # Quick Apply (Card Frame)
        frame_qa = QFrame()
        frame_qa.setObjectName("CardFrame")
        layout_qa = QVBoxLayout(frame_qa)
        
        # Quick Apply (Title)
        lbl_qa_title = QLabel("⚡ Quick Apply (Presets)")
        lbl_qa_title.setObjectName("CardLabelBold")
        layout_qa.addWidget(lbl_qa_title)

        # Quick Apply (Description)
        lbl_qa_desc = QLabel("Bypass drag-and-drop. Requires screen calibration.")
        lbl_qa_desc.setObjectName("CardLabelSubtle")
        layout_qa.addWidget(lbl_qa_desc)

        hbox_qa = QHBoxLayout()
        
        # Quick Apply (Enable/Disable Toggle)
        self.btn_toggle_qa = QPushButton()
        self.btn_toggle_qa.setObjectName("ToggleQA")
        self.btn_toggle_qa.clicked.connect(self.toggle_quick_apply)
        
        # Quick Apply (Configure Button)
        self.btn_config_qa = QPushButton("⚙️ Configure")
        self.btn_config_qa.setFixedWidth(120)
        self.btn_config_qa.clicked.connect(self.open_qa_config)
        hbox_qa.addWidget(self.btn_toggle_qa)
        hbox_qa.addWidget(self.btn_config_qa)
        hbox_qa.addStretch()
        layout_qa.addLayout(hbox_qa)
        layout.addWidget(frame_qa)

        # Port and Connection Settings Button
        self.btn_port_settings = QPushButton("🌐 Port and Connection Settings")
        self.btn_port_settings.clicked.connect(self.open_port_settings)
        layout.addWidget(self.btn_port_settings)

        # SearchBar Configuration Button
        self.btn_searchbar_settings = QPushButton("🔍 SearchBar Configuration")
        self.btn_searchbar_settings.clicked.connect(self.open_searchbar_settings)
        layout.addWidget(self.btn_searchbar_settings)

        # Theme Configuration Button
        self.btn_theme_settings = QPushButton("🎨 Theme Configuration")
        self.btn_theme_settings.clicked.connect(self.open_theme_settings)
        layout.addWidget(self.btn_theme_settings)

        layout.addStretch()

        self.update_qa_ui()

    # MÉTHODE D'OUVERTURE
    def open_searchbar_settings(self):
        from GUI.searchbar_page import SearchBarPage
        self.searchbar_window = SearchBarPage(self.mw)
        self.searchbar_window.show()

    def open_theme_settings(self):
        self.theme_window = ThemePage(self.mw)
        self.theme_window.setWindowTitle("Theme Configuration")
        self.theme_window.resize(400, 300)
        self.theme_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.theme_window.show()


    def open_port_settings(self):
        from GUI.port_page import PortPage
        self.port_window = PortPage(self.mw)
        self.port_window.setWindowTitle("Port Settings")
        self.port_window.resize(400, 300)
        self.port_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.port_window.show()

    def toggle_quick_apply(self):
        is_enabled = self.mw.settings.get("quick_apply_enabled", False)

        if not is_enabled:
            import os
            from Modules.apply_preset import PresetApplier
            if not os.path.exists(PresetApplier.CONFIG_PATH):
                self.open_qa_config()
                return

        self.mw.settings["quick_apply_enabled"] = not is_enabled
        self.mw.save_settings()
        self.update_qa_ui()
        state = "ENABLED" if self.mw.settings["quick_apply_enabled"] else "DISABLED"
        self.mw.append_log(f"⚙️ Quick Apply {state}", "#55ccff")

    def update_qa_ui(self):
        is_enabled = self.mw.settings.get("quick_apply_enabled", False)
        self.btn_toggle_qa.setText("Enabled" if is_enabled else "Disabled")
        self.btn_toggle_qa.setProperty("qa_state", "enabled" if is_enabled else "disabled")
        self.btn_toggle_qa.style().unpolish(self.btn_toggle_qa)
        self.btn_toggle_qa.style().polish(self.btn_toggle_qa)

    def open_qa_config(self):
        wizard = QuickApplyWizard(self.mw)
        if wizard.exec():
            self.update_qa_ui()