import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                              QLineEdit, QCheckBox, QPushButton)
from PyQt6.QtCore import Qt
from Core.paths import get_data_path
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
from Core.configs.port_config import DEFAULT_PORTS
from Core.functions.bridge import get_premiere_version, get_premiere_name, request_premiere_version


class PremierePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.settings_path = get_data_path("port_settings.json")
        self.init_ui()
        self.load_ports()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"]
        )

        premiere_card = QFrame()
        premiere_card.setObjectName("CardFrame")
        premiere_layout = QVBoxLayout(premiere_card)
        premiere_layout.setContentsMargins(
            THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"]
        )
        premiere_layout.setSpacing(THEME_SPACING["spacing_element"])

        title_layout = QHBoxLayout()
        title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_icon = QLabel()
        lbl_icon.setPixmap(icon_pixmap("globe", size=THEME_SPACING["icon_large"]))
        lbl_icon.setFixedSize(THEME_SPACING["icon_large"], THEME_SPACING["icon_large"])
        lbl_icon.setScaledContents(True)
        lbl_title = QLabel("Premiere Pro")
        lbl_title.setObjectName("PageTitle")
        title_layout.addWidget(lbl_icon)
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        premiere_layout.addLayout(title_layout)

        version_layout = QHBoxLayout()
        version_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_version_title = QLabel("Version:")
        lbl_version_title.setObjectName("CardLabel")
        version_layout.addWidget(lbl_version_title)
        
        self.lbl_version_value = QLabel()
        self.lbl_version_value.setObjectName("CardLabelBold")
        version_layout.addWidget(self.lbl_version_value)
        version_layout.addStretch()
        premiere_layout.addLayout(version_layout)

        self._update_version_display()

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("Separator")
        premiere_layout.addWidget(separator)

        hbox_sync = QHBoxLayout()
        hbox_sync.setSpacing(THEME_SPACING["spacing_element"])
        self.btn_sync = QPushButton()
        self.btn_sync.setIcon(icon("sync", size=THEME_SPACING["icon_small"]))
        self.btn_sync.setText(" Sync")
        self.btn_sync.setFixedHeight(THEME_SPACING["height_search_bar"])
        self.btn_sync.setObjectName("PrimaryButton")
        self.btn_sync.clicked.connect(self.on_sync_clicked)
        hbox_sync.addWidget(self.btn_sync)
        hbox_sync.addStretch()
        premiere_layout.addLayout(hbox_sync)

        port_title = QLabel("Connection Settings")
        port_title.setObjectName("CardLabelBold")
        premiere_layout.addWidget(port_title)

        hbox_ws = QHBoxLayout()
        hbox_ws.setSpacing(THEME_SPACING["spacing_element"])
        lbl_ws = QLabel("WebSocket Port:")
        lbl_ws.setObjectName("CardLabel")
        self.inp_ws = QLineEdit()
        self.inp_ws.setFixedWidth(THEME_SPACING["width_input_port"])
        hbox_ws.addWidget(lbl_ws)
        hbox_ws.addStretch()
        hbox_ws.addWidget(self.inp_ws)
        premiere_layout.addLayout(hbox_ws)

        hbox_tcp = QHBoxLayout()
        hbox_tcp.setSpacing(THEME_SPACING["spacing_element"])
        lbl_tcp = QLabel("TCP Port:")
        lbl_tcp.setObjectName("CardLabel")
        self.inp_tcp = QLineEdit()
        self.inp_tcp.setFixedWidth(THEME_SPACING["width_input_port"])
        hbox_tcp.addWidget(lbl_tcp)
        hbox_tcp.addStretch()
        hbox_tcp.addWidget(self.inp_tcp)
        premiere_layout.addLayout(hbox_tcp)

        self.chk_auto = QCheckBox("Auto-connect on startup")
        self.chk_auto.setObjectName("SubtleCheckbox")
        premiere_layout.addWidget(self.chk_auto)

        btn_save = QPushButton()
        btn_save.setIcon(icon("save"))
        btn_save.setText(" Save Settings")
        btn_save.setObjectName("AccentButton")
        btn_save.clicked.connect(self.save_ports)
        premiere_layout.addWidget(btn_save)

        info_layout = QHBoxLayout()
        info_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_warn_icon = QLabel()
        lbl_warn_icon.setFixedSize(THEME_SPACING["icon_small_fixed"], THEME_SPACING["icon_small_fixed"])
        lbl_warn_icon.setPixmap(icon_pixmap("exclamation-triangle", size=THEME_SPACING["icon_small_fixed"]))
        lbl_warn_icon.setScaledContents(True)
        lbl_info = QLabel("Changes require restarting the application.")
        lbl_info.setObjectName("WarningLabel")
        info_layout.addWidget(lbl_warn_icon)
        info_layout.addSpacing(4)
        info_layout.addWidget(lbl_info)
        info_layout.addStretch()
        premiere_layout.addLayout(info_layout)

        premiere_layout.addStretch()
        layout.addWidget(premiere_card)
        layout.addStretch()

    def _update_version_display(self):
        version = get_premiere_version()
        name = get_premiere_name()
        
        if version:
            if name:
                self.lbl_version_value.setText(f"{version} ({name})")
            else:
                self.lbl_version_value.setText(version)
            self.lbl_version_value.setStyleSheet(f"color: {THEME_USER_COLORS['success']};")
        else:
            self.lbl_version_value.setText("Not detected")
            self.lbl_version_value.setStyleSheet(f"color: {THEME_USER_COLORS['text_subtle']};")

    def on_sync_clicked(self):
        self.btn_sync.setEnabled(False)
        self.mw.trigger_sync()
        self.btn_sync.setEnabled(True)

    def load_ports(self):
        default_data = {"ws_port": DEFAULT_PORTS["ws_port"], "tcp_port": DEFAULT_PORTS["tcp_port"], "auto_connect": False}
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    data = json.load(f)
                    default_data.update(data)
            except:
                pass
        
        self.inp_ws.setText(str(default_data["ws_port"]))
        self.inp_tcp.setText(str(default_data["tcp_port"]))
        self.chk_auto.setChecked(default_data.get("auto_connect", False))

    def save_ports(self):
        data = {
            "ws_port": int(self.inp_ws.text() or DEFAULT_PORTS["ws_port"]),
            "tcp_port": int(self.inp_tcp.text() or DEFAULT_PORTS["tcp_port"]),
            "auto_connect": self.chk_auto.isChecked()
        }
        os.makedirs(get_data_path(), exist_ok=True)
        with open(self.settings_path, "w") as f:
            json.dump(data, f, indent=4)
        
        self.mw.append_log(f" Port settings saved (WS: {data['ws_port']}, TCP: {data['tcp_port']}). Please restart.", THEME_USER_COLORS["success"])
