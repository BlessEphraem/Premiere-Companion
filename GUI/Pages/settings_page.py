# GUI/settings_page.py
import os
import json
import zipfile
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QFrame, QLabel, QDialog
from PyQt6.QtCore import Qt
from GUI.Pages.theme_page import ThemePage
from Core.paths import get_data_path
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS

class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"])
        layout.setSpacing(THEME_SPACING["spacing_element"])

                # Premiere Pro Card
        premiere_card = QFrame()
        premiere_card.setObjectName("CardFrame")
        premiere_layout = QVBoxLayout(premiere_card)
        premiere_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])

        premiere_title_layout = QHBoxLayout()
        premiere_title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_premiere_icon = QLabel()
        lbl_premiere_icon.setPixmap(icon_pixmap("globe", size=THEME_SPACING["icon_medium"]))
        lbl_premiere_icon.setFixedSize(THEME_SPACING["icon_medium"], THEME_SPACING["icon_medium"])
        lbl_premiere_icon.setScaledContents(True)
        lbl_premiere_title = QLabel("Premiere Pro")
        lbl_premiere_title.setObjectName("CardLabelBold")
        premiere_title_layout.addWidget(lbl_premiere_icon)
        premiere_title_layout.addWidget(lbl_premiere_title)
        premiere_title_layout.addStretch()
        premiere_layout.addLayout(premiere_title_layout)

        lbl_premiere_desc = QLabel("Connection and RegEx configuration.")
        lbl_premiere_desc.setObjectName("CardLabelSubtle")
        premiere_layout.addWidget(lbl_premiere_desc)

        hbox_premiere = QHBoxLayout()
        hbox_premiere.setSpacing(THEME_SPACING["spacing_element"])
        self.btn_config_premiere = QPushButton()
        self.btn_config_premiere.setIcon(icon("cog"))
        self.btn_config_premiere.setText(" Configure")
        self.btn_config_premiere.setFixedWidth(THEME_SPACING["width_button_medium"])
        self.btn_config_premiere.clicked.connect(self.open_premiere_settings)

        self.btn_regex = QPushButton()
        self.btn_regex.setIcon(icon("broom"))
        self.btn_regex.setText(" RegEx")
        self.btn_regex.setFixedWidth(THEME_SPACING["width_button_small"])
        self.btn_regex.clicked.connect(self.open_regex)

        hbox_premiere.addWidget(self.btn_config_premiere)
        hbox_premiere.addWidget(self.btn_regex)
        hbox_premiere.addStretch()
        premiere_layout.addLayout(hbox_premiere)

        layout.addWidget(premiere_card)

        search_card = QFrame()
        search_card.setObjectName("CardFrame")
        search_layout = QVBoxLayout(search_card)
        search_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])

        search_title_layout = QHBoxLayout()
        search_title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_search_icon = QLabel()
        lbl_search_icon.setPixmap(icon_pixmap("search", size=THEME_SPACING["icon_medium"]))
        lbl_search_icon.setFixedSize(THEME_SPACING["icon_medium"], THEME_SPACING["icon_medium"])
        lbl_search_icon.setScaledContents(True)
        lbl_search_title = QLabel("Search")
        lbl_search_title.setObjectName("CardLabelBold")
        search_title_layout.addWidget(lbl_search_icon)
        search_title_layout.addWidget(lbl_search_title)
        search_title_layout.addStretch()
        search_layout.addLayout(search_title_layout)

        lbl_search_desc = QLabel("SearchBar configuration.")
        lbl_search_desc.setObjectName("CardLabelSubtle")
        search_layout.addWidget(lbl_search_desc)

        hbox_search = QHBoxLayout()
        hbox_search.setSpacing(THEME_SPACING["spacing_element"])
        self.btn_searchbar_settings = QPushButton()
        self.btn_searchbar_settings.setIcon(icon("cog"))
        self.btn_searchbar_settings.setText(" Bar")
        self.btn_searchbar_settings.setFixedWidth(THEME_SPACING["width_button_medium"])
        self.btn_searchbar_settings.clicked.connect(self.open_searchbar_settings)

        self.btn_priority_ignore = QPushButton()
        self.btn_priority_ignore.setIcon(icon("broom"))
        self.btn_priority_ignore.setText(" Priority & Ignore")
        self.btn_priority_ignore.clicked.connect(self.open_priority_ignore)

        hbox_search.addWidget(self.btn_searchbar_settings)
        hbox_search.addWidget(self.btn_priority_ignore)
        hbox_search.addStretch()
        search_layout.addLayout(hbox_search)

        layout.addWidget(search_card)

        # Commands Card
        commands_card = QFrame()
        commands_card.setObjectName("CardFrame")
        commands_layout = QVBoxLayout(commands_card)
        commands_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])

        cmd_title_layout = QHBoxLayout()
        cmd_title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_cmd_icon = QLabel()
        lbl_cmd_icon.setPixmap(icon_pixmap("bolt", size=THEME_SPACING["icon_medium"]))
        lbl_cmd_icon.setFixedSize(THEME_SPACING["icon_medium"], THEME_SPACING["icon_medium"])
        lbl_cmd_icon.setScaledContents(True)
        lbl_cmd_title = QLabel("Commands")
        lbl_cmd_title.setObjectName("CardLabelBold")
        cmd_title_layout.addWidget(lbl_cmd_icon)
        cmd_title_layout.addWidget(lbl_cmd_title)
        cmd_title_layout.addStretch()
        commands_layout.addLayout(cmd_title_layout)

        lbl_cmd_desc = QLabel("Customize search keywords for each content type.")
        lbl_cmd_desc.setObjectName("CardLabelSubtle")
        commands_layout.addWidget(lbl_cmd_desc)

        hbox_cmd = QHBoxLayout()
        hbox_cmd.setSpacing(THEME_SPACING["spacing_element"])
        self.btn_commands = QPushButton()
        self.btn_commands.setIcon(icon("cog"))
        self.btn_commands.setText(" Configure")
        self.btn_commands.setFixedWidth(THEME_SPACING["width_button_medium"])
        self.btn_commands.clicked.connect(self.open_commands)
        hbox_cmd.addWidget(self.btn_commands)
        hbox_cmd.addStretch()
        commands_layout.addLayout(hbox_cmd)

        layout.addWidget(commands_card)

        # Theme Configuration Button
        self.btn_theme_settings = QPushButton()
        self.btn_theme_settings.setIcon(icon("palette"))
        self.btn_theme_settings.setText(" Theme Configuration")
        self.btn_theme_settings.clicked.connect(self.open_theme_settings)
        layout.addWidget(self.btn_theme_settings)

        # Import/Export Config Buttons
        hbox_ie = QHBoxLayout()
        hbox_ie.setSpacing(THEME_SPACING["spacing_element"])
        self.btn_import_config = QPushButton()
        self.btn_import_config.setIcon(icon("download", size=THEME_SPACING["icon_medium"]))
        self.btn_import_config.setText(" Import Config..")
        self.btn_import_config.clicked.connect(self.import_config)
        self.btn_export_config = QPushButton()
        self.btn_export_config.setIcon(icon("upload", size=THEME_SPACING["icon_medium"]))
        self.btn_export_config.setText(" Export Config")
        self.btn_export_config.clicked.connect(self.export_config)
        hbox_ie.addWidget(self.btn_import_config, 1)
        hbox_ie.addWidget(self.btn_export_config, 1)
        layout.addLayout(hbox_ie)

        layout.addStretch()

    # MÉTHODE D'OUVERTURE
    def open_commands(self):
        from Core.functions.windows import create_window
        self.commands_window = create_window("commands", self.mw)
        self.mw.register_child_window(self.commands_window)
        self.commands_window.show()

    def open_priority_ignore(self):
        from Core.functions.windows import create_window
        self.priority_ignore_window = create_window("priority_ignore", self.mw)
        self.mw.register_child_window(self.priority_ignore_window)
        self.priority_ignore_window.show()

    def open_searchbar_settings(self):
        from GUI.Pages.searchbar_page import SearchBarPage
        from Core.functions.windows import apply_window_config
        self.searchbar_window = SearchBarPage(self.mw)
        apply_window_config(self.searchbar_window, "searchbar", "SearchBar Configuration")
        self.mw.register_child_window(self.searchbar_window)
        self.searchbar_window.show()

    def open_theme_settings(self):
        from Core.functions.windows import apply_window_config
        if hasattr(self, "theme_window") and self.theme_window.isVisible():
            self.theme_window.raise_()
            self.theme_window.activateWindow()
            return
            
        self.theme_window = ThemePage(self.mw)
        apply_window_config(self.theme_window, "theme", "Theme Configuration")
        self.theme_window.setWindowModality(Qt.WindowModality.NonModal)
        self.mw.register_child_window(self.theme_window)
        self.theme_window.show()


    def open_premiere_settings(self):
        from Core.functions.windows import create_window
        self.premiere_window = create_window("premiere", self.mw)
        self.mw.register_child_window(self.premiere_window)
        self.premiere_window.show()

    def open_regex(self):
        from Core.functions.windows import create_window
        self.regex_window = create_window("regex", self.mw)
        self.mw.register_child_window(self.regex_window)
        self.regex_window.show()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self.mw, 'btn_toggle_console'):
            self.mw.btn_toggle_console.show()

    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self.mw, 'btn_toggle_console'):
            self.mw.btn_toggle_console.hide()

    def export_config(self):
        data_path = get_data_path()
        config_files = [
            "settings.json",
            "keybinds.json",
            "port_settings.json",
            "theme.json",
            "rules.json",
            "searchbar_config.json",
            "quick_apply_config.json",
            "betterMotion_config.json",
            "search_history.json"
        ]
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Config", "PremiereCompanion_Config.zip", "Zip Files (*.zip)")
        if not file_path:
            return
        
        try:
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for config_file in config_files:
                    file_full_path = os.path.join(data_path, config_file)
                    if os.path.exists(file_full_path):
                        zipf.write(file_full_path, config_file)
            
            self.mw.append_log(f" Config exported successfully!", THEME_USER_COLORS["success"])
        except Exception as e:
            self.mw.append_log(f" Export failed: {e}", THEME_USER_COLORS["error"])
            QMessageBox.critical(self, "Export Error", str(e))

    def import_config(self):
        data_path = get_data_path()
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Config", "", "Zip Files (*.zip)")
        if not file_path:
            return
        
        reply = QMessageBox.question(
            self, "Import Config",
            "This will overwrite existing settings. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                for member in zipf.namelist():
                    # Write directly to the data directory
                    target_path = os.path.join(data_path, member)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, 'wb') as f:
                        f.write(zipf.read(member))
            
            self.mw.append_log(f" Config imported successfully! Restart required.", THEME_USER_COLORS["success"])
            QMessageBox.information(self, "Import Complete", "Config imported. Please restart the application.")
        except Exception as e:
            self.mw.append_log(f" Import failed: {e}", THEME_USER_COLORS["error"])
            QMessageBox.critical(self, "Import Error", str(e))
