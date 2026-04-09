# GUI/Pages/macros_page.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QWidget,
                             QListWidget, QListWidgetItem, QScrollArea)
from PyQt6.QtCore import Qt, QSize
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS


class MacroItemWidget(QWidget):
    def __init__(self, macro_data, parent_page):
        super().__init__()
        self.macro_data = macro_data
        self.parent_page = parent_page

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"],
            THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"],
        )

        lbl_tag = QLabel("[CMD.MA]")
        lbl_tag.setObjectName("EffectTag")
        lbl_tag.setProperty("type", "TagCommand")

        lbl_name = QLabel(macro_data.get("name", "Unnamed Macro"))
        lbl_name.setObjectName("effectName")

        layout.addWidget(lbl_tag)
        layout.addWidget(lbl_name)
        layout.addStretch()

        btn_edit = QPushButton()
        btn_edit.setIcon(icon("edit"))
        btn_edit.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
        btn_edit.setObjectName("RegexEditBtn")
        btn_edit.clicked.connect(self.edit_macro)

        btn_del = QPushButton()
        btn_del.setIcon(icon("times-circle"))
        btn_del.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
        btn_del.setObjectName("RegexDeleteBtn")
        btn_del.clicked.connect(self.delete_macro)

        layout.addWidget(btn_edit)
        layout.addWidget(btn_del)

    def edit_macro(self):
        self.parent_page.open_macro_editor(self.macro_data)

    def delete_macro(self):
        from Core.configs.macros_config import load_macros_config, save_macros_config
        config = load_macros_config()
        config["macros"] = [m for m in config["macros"] if m["name"] != self.macro_data["name"]]
        save_macros_config(config)
        self.parent_page.load_macros_ui()
        self.parent_page.mw.reload_commands()


class MacrosPage(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.setModal(True)
        self.init_ui()
        self.load_macros_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"],
            THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"],
        )
        layout.setSpacing(THEME_SPACING["spacing_element"])

        # Header
        title_layout = QHBoxLayout()
        title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_icon = QLabel()
        lbl_icon.setPixmap(icon_pixmap("bolt", size=THEME_SPACING["icon_large"]))
        lbl_icon.setFixedSize(THEME_SPACING["icon_large"], THEME_SPACING["icon_large"])
        lbl_icon.setScaledContents(True)
        lbl_title = QLabel("Hotkeys & Macros")
        lbl_title.setObjectName("PageTitle")
        title_layout.addWidget(lbl_icon)
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Custom Hotkeys section (embedded)
        from GUI.Pages.customHotkey_page import CustomHotkeyPage
        self.hotkeys_section = CustomHotkeyPage(self.mw)
        layout.addWidget(self.hotkeys_section)

        # Macros card
        macro_card = QFrame()
        macro_card.setObjectName("CardFrame")
        macro_layout = QVBoxLayout(macro_card)
        macro_layout.setContentsMargins(
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
        )
        macro_layout.setSpacing(THEME_SPACING["spacing_element"])

        macro_header = QHBoxLayout()
        lbl_macro_title = QLabel("Custom Macros")
        lbl_macro_title.setObjectName("CardLabelBold")
        btn_create = QPushButton(" Create Macro")
        btn_create.setIcon(icon("plus"))
        btn_create.setFixedWidth(THEME_SPACING["width_button_medium"])
        btn_create.clicked.connect(lambda: self.open_macro_editor())
        macro_header.addWidget(lbl_macro_title)
        macro_header.addStretch()
        macro_header.addWidget(btn_create)
        macro_layout.addLayout(macro_header)

        lbl_desc = QLabel(
            "Create sequences of effects, presets, transitions and commands.\n"
            "Chain them together with custom parameters and timing."
        )
        lbl_desc.setObjectName("CardLabelSubtle")
        macro_layout.addWidget(lbl_desc)

        self.macro_list = QListWidget()
        self.macro_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.macro_list.setFixedHeight(300)
        macro_layout.addWidget(self.macro_list)

        layout.addWidget(macro_card)
        layout.addStretch()

    def load_macros_ui(self):
        from Core.configs.macros_config import load_macros_config
        self.macro_list.clear()
        config = load_macros_config()
        for macro in config.get("macros", []):
            item = QListWidgetItem(self.macro_list)
            item.setSizeHint(QSize(0, 45))
            widget = MacroItemWidget(macro, self)
            self.macro_list.setItemWidget(item, widget)

    def open_macro_editor(self, macro_data=None):
        from Core.functions.windows import create_window
        dialog = create_window("macro_editor", self.mw, modal=True)
        if dialog:
            if macro_data:
                dialog.load_macro(macro_data)
            if dialog.exec():
                self.load_macros_ui()
                self.mw.reload_commands()
