# GUI/keymaps_page.py
import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton, QScrollArea, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

class KeybindInput(QLineEdit):
    def __init__(self, default_key=""):
        super().__init__()
        self.setText(default_key)
        self.setReadOnly(True)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        if key in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return
        
        # We convert 'modifiers' with .value to make the operation binary
        key_sequence = QKeySequence(modifiers.value | key)
        
        self.setText(key_sequence.toString())
        self.clearFocus()

class KeymapsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.inputs = {}
        self.init_ui()
        self.load_keybinds()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("⌨️ Keymaps")
        lbl_title.setObjectName("PageTitle")
        layout.addWidget(lbl_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TransparentScroll")
        
        container = QWidget()
        container.setObjectName("TransparentContainer")
        self.form_layout = QVBoxLayout(container)
        
        actions = {
            "Run Search Bar": "Ctrl+Space",
            "Window > Timelines": "Shift+3",
            "Window > Effect": "Shift+2",
            "Search Find Box": "Shift+F"
        }

        for action, default in actions.items():
            frame = QFrame()
            frame.setObjectName("CardFrame")
            hbox = QHBoxLayout(frame)
            
            lbl = QLabel(action)
            lbl.setObjectName("CardLabel")
            inp = KeybindInput(default)
            inp.setFixedWidth(150)
            
            self.inputs[action] = inp
            hbox.addWidget(lbl)
            hbox.addStretch()
            hbox.addWidget(inp)
            self.form_layout.addWidget(frame)

        self.form_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_save = QPushButton("💾 Save Keybinds")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_keybinds)
        layout.addWidget(btn_save)

    def load_keybinds(self):
        path = os.path.join("Data", "pr_keybinds.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    for act, inp in self.inputs.items():
                        if act in data:
                            inp.setText(data[act])
            except Exception as e:
                self.mw.append_log(f"Error reading keybinds: {e}", "#ff5555")

    def save_keybinds(self):
        data = {act: inp.text() for act, inp in self.inputs.items()}
        os.makedirs("Data", exist_ok=True)
        path = os.path.join("Data", "pr_keybinds.json")
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            self.mw.append_log("✅ Keymaps saved!", "#55ff55")
            self.mw.update_global_hotkey()
        except Exception as e:
            self.mw.append_log(f"❌ Error saving keybinds: {e}", "#ff5555")