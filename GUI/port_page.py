import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QLineEdit, QCheckBox, QPushButton
from PyQt6.QtCore import Qt
from Core.paths import get_data_path

class PortPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.settings_path = get_data_path("port_settings.json")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl_title = QLabel("🌐 Port Settings")
        lbl_title.setObjectName("PageTitle")
        layout.addWidget(lbl_title)

        frame = QFrame()
        frame.setObjectName("CardFrame")
        vbox = QVBoxLayout(frame)

        # Web Socket Port
        hbox_ws = QHBoxLayout()
        lbl_ws = QLabel("WebSocket Port (Excepthook):")
        lbl_ws.setObjectName("CardLabel")
        self.inp_ws = QLineEdit()
        self.inp_ws.setFixedWidth(100)
        hbox_ws.addWidget(lbl_ws)
        hbox_ws.addStretch()
        hbox_ws.addWidget(self.inp_ws)
        vbox.addLayout(hbox_ws)

        # TCP Port
        hbox_tcp = QHBoxLayout()
        lbl_tcp = QLabel("TCP Port (App):")
        lbl_tcp.setObjectName("CardLabel")
        self.inp_tcp = QLineEdit()
        self.inp_tcp.setFixedWidth(100)
        hbox_tcp.addWidget(lbl_tcp)
        hbox_tcp.addStretch()
        hbox_tcp.addWidget(self.inp_tcp)
        vbox.addLayout(hbox_tcp)

        # Auto-Connect
        self.chk_auto = QCheckBox("Auto-connect to Premiere on startup")
        self.chk_auto.setObjectName("SubtleCheckbox")
        vbox.addWidget(self.chk_auto)

        layout.addWidget(frame)

        btn_save = QPushButton("💾 Save Settings")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_ports)
        layout.addWidget(btn_save)

        lbl_info = QLabel("Changes require restarting the application.")
        lbl_info.setObjectName("WarningLabel")
        layout.addWidget(lbl_info)

        layout.addStretch()
        self.load_ports()

    def load_ports(self):
        default_data = {"ws_port": 8090, "tcp_port": 8091, "auto_connect": False}
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
            "ws_port": int(self.inp_ws.text() or 8090),
            "tcp_port": int(self.inp_tcp.text() or 8091),
            "auto_connect": self.chk_auto.isChecked()
        }
        os.makedirs(get_data_path(), exist_ok=True)
        with open(self.settings_path, "w") as f:
            json.dump(data, f, indent=4)
        
        self.mw.append_log(f"✅ Port settings saved (WS: {data['ws_port']}, TCP: {data['tcp_port']}). Please restart.", "#55ff55")
        
    @staticmethod
    def get_ports():
        path = get_data_path("port_settings.json")
        default = {"ws_port": 8090, "tcp_port": 8091, "auto_connect": False}
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    default.update(data)
            except:
                pass
        return default
