# GUI/searchbar_page.py
import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QSpinBox,
                             QPushButton, QFormLayout, QSlider)
from PyQt6.QtCore import Qt
from Core.paths import get_data_path

class SearchBarPage(QDialog):
    CONFIG_PATH = get_data_path("searchbar_config.json")

    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.setWindowTitle("SearchBar Configuration")
        self.resize(400, 300)
        self.setModal(True)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # QSS
        lbl_title = QLabel("🔍 SearchBar Configuration")
        lbl_title.setObjectName("PageTitle")
        layout.addWidget(lbl_title)

        # --- 1. Max Items ---
        self.lbl_max_items = QLabel("Max item showed : 100")
        layout.addWidget(self.lbl_max_items)
        
        self.slider_max_items = QSlider(Qt.Orientation.Horizontal)
        self.slider_max_items.setRange(1, 256)
        self.slider_max_items.valueChanged.connect(lambda v: self.lbl_max_items.setText(f"Max item showed : {v}"))
        layout.addWidget(self.slider_max_items)

        # --- 2. Max Recents ---
        self.lbl_max_recent = QLabel("Max item in recent : 3")
        layout.addWidget(self.lbl_max_recent)
        
        self.slider_max_recent = QSlider(Qt.Orientation.Horizontal)
        self.slider_max_recent.setRange(0, 5)
        self.slider_max_recent.valueChanged.connect(lambda v: self.lbl_max_recent.setText(f"Max item in recent : {v}"))
        layout.addWidget(self.slider_max_recent)

        # --- 3. Width ---
        self.lbl_width = QLabel("Bar Width : 600 px")
        layout.addWidget(self.lbl_width)
        
        self.slider_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_width.setRange(300, 1200)
        self.slider_width.valueChanged.connect(lambda v: self.lbl_width.setText(f"Bar Width : {v} px"))
        layout.addWidget(self.slider_width)

        # --- 4. Height ---
        self.lbl_height = QLabel("Bar Height : 420 px")
        layout.addWidget(self.lbl_height)
        
        self.slider_height = QSlider(Qt.Orientation.Horizontal)
        self.slider_height.setRange(200, 1000)
        self.slider_height.valueChanged.connect(lambda v: self.lbl_height.setText(f"Bar Height : {v} px"))
        layout.addWidget(self.slider_height)

        # --- 5. Font Size ---
        self.lbl_font = QLabel("Font Size : 15 px")
        layout.addWidget(self.lbl_font)
        
        self.slider_font = QSlider(Qt.Orientation.Horizontal)
        self.slider_font.setRange(10, 30)
        self.slider_font.valueChanged.connect(lambda v: self.lbl_font.setText(f"Font Size : {v} px"))
        layout.addWidget(self.slider_font)

        layout.addStretch()

        # Save Button
        btn_save = QPushButton("💾 Save Settings")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)

    def load_config(self):
        # Default Configuration
        default_config = {
            "max_items": 100,
            "max_recent": 3,
            "window_width": 600,
            "window_height": 420,
            "font_size": 15
        }
        
        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_config.update(data)
            except Exception:
                pass

        self.slider_max_items.setValue(default_config.get("max_items", 100))
        self.slider_max_recent.setValue(default_config.get("max_recent", 3))
        self.slider_width.setValue(default_config.get("window_width", 600))
        self.slider_height.setValue(default_config.get("window_height", 420))
        self.slider_font.setValue(default_config.get("font_size", 15))

    def save_config(self):
        data = {
            "max_items": self.slider_max_items.value(),
            "max_recent": self.slider_max_recent.value(),
            "window_width": self.slider_width.value(),
            "window_height": self.slider_height.value(),
            "font_size": self.slider_font.value()
            }

            os.makedirs(get_data_path(), exist_ok=True)
            with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:            json.dump(data, f, indent=4)
        
        self.mw.append_log("✅ SearchBar settings saved!", "#55ff55")
        self.accept()