# GUI/Pages/commands_page.py
import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QFrame, QCheckBox,
                             QWidget, QScrollArea, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QSize
from Core.paths import get_data_path
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
from Core.configs.commands_config import DEFAULT_COMMANDS_CONFIG
from Core.functions.search import load_commands_config


# Ordered rows shown in the UI (type_code, display_label, example)
_KEYWORD_ROWS = [
    ("CMD",    "Commands",           "//  (generic command search)"),
    ("FX.V",   "Video Effects",      "/V Brightness & Contrast"),
    ("FX.A",   "Audio Effects",      "/A DeHummer"),
    ("TR.V",   "Video Transitions",  "/T Motion Tween"),
    ("PRST",   "Presets",            "/P YourPreset"),
    ("CMD.QA", "Quick Apply",        "/QA  (switches to Quick Apply mode)"),
    ("CMD.BM", "Better Motion",      "/BM  (switches to Better Motion mode)"),
]


class MacroItemWidget(QWidget):
    def __init__(self, macro_data, parent_page):
        super().__init__()
        self.macro_data = macro_data
        self.parent_page = parent_page

        layout = QHBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"], THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"])

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


class CommandsPage(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.setModal(True)
        self._inputs = {}   # type_code -> QLineEdit
        self.init_ui()
        self.load_config()
        self.load_macros_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"],
            THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"],
        )
        layout.setSpacing(THEME_SPACING["spacing_element"])

        # Create a scroll area for the whole content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TransparentScroll")
        
        scroll_content = QWidget()
        scroll_content.setObjectName("TransparentContainer")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(THEME_SPACING["spacing_element"])

        # Header
        title_layout = QHBoxLayout()
        title_layout.setSpacing(THEME_SPACING["spacing_element"])
        lbl_icon = QLabel()
        lbl_icon.setPixmap(icon_pixmap("bolt", size=THEME_SPACING["icon_large"]))
        lbl_icon.setFixedSize(THEME_SPACING["icon_large"], THEME_SPACING["icon_large"])
        lbl_icon.setScaledContents(True)
        lbl_title = QLabel("Commands")
        lbl_title.setObjectName("PageTitle")
        title_layout.addWidget(lbl_icon)
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        scroll_layout.addLayout(title_layout)

        # Keywords card
        kw_card = QFrame()
        kw_card.setObjectName("CardFrame")
        kw_layout = QVBoxLayout(kw_card)
        kw_layout.setContentsMargins(
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
        )
        kw_layout.setSpacing(THEME_SPACING["spacing_element"])

        lbl_kw_title = QLabel("Keywords")
        lbl_kw_title.setObjectName("CardLabelBold")
        kw_layout.addWidget(lbl_kw_title)

        # "Disable Keywords" toggle
        self.btn_disable = QPushButton("Disable Keywords: OFF")
        self.btn_disable.setCheckable(True)
        self.btn_disable.setObjectName("Toggle")
        self.btn_disable.setProperty("qa_state", "disabled")
        self.btn_disable.clicked.connect(self._toggle_disable)
        kw_layout.addWidget(self.btn_disable)

        lbl_desc = QLabel(
            "Switch search type instantly by starting with '/' + keyword."
        )
        lbl_desc.setObjectName("CardLabelSubtle")
        kw_layout.addWidget(lbl_desc)

        # Keyword rows
        for type_code, display_label, example in _KEYWORD_ROWS:
            v_layout = QVBoxLayout()
            v_layout.setSpacing(2)
            top_row = QHBoxLayout()
            lbl = QLabel(display_label)
            lbl.setObjectName("CardLabel")
            inp = QLineEdit()
            inp.setFixedWidth(60)
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inp.setMaxLength(6)
            inp.setPlaceholderText(DEFAULT_COMMANDS_CONFIG["keywords"].get(type_code, ""))
            inp.textChanged.connect(self._clear_warning)
            self._inputs[type_code] = inp
            top_row.addWidget(lbl)
            top_row.addStretch()
            top_row.addWidget(inp)
            v_layout.addLayout(top_row)
            bottom_row = QHBoxLayout()
            lbl_example = QLabel(example)
            lbl_example.setObjectName("CardLabelSubtle")
            bottom_row.addStretch()
            bottom_row.addWidget(lbl_example)
            v_layout.addLayout(bottom_row)
            kw_layout.addLayout(v_layout)

        scroll_layout.addWidget(kw_card)

        # Macros card
        macro_card = QFrame()
        macro_card.setObjectName("CardFrame")
        macro_layout = QVBoxLayout(macro_card)
        macro_layout.setContentsMargins(THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"], THEME_SPACING["margin_card"])
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

        self.macro_list = QListWidget()
        self.macro_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.macro_list.setFixedHeight(200)
        macro_layout.addWidget(self.macro_list)
        scroll_layout.addWidget(macro_card)

        # Warning label
        self.lbl_warning = QLabel("")
        self.lbl_warning.setObjectName("WarningLabel")
        self.lbl_warning.setWordWrap(True)
        self.lbl_warning.hide()
        scroll_layout.addWidget(self.lbl_warning)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        btn_save = QPushButton()
        btn_save.setIcon(icon("save"))
        btn_save.setText(" Save")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_config)
        footer.addWidget(btn_save)
        layout.addLayout(footer)

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
        # We need to register "macro_editor" in windows.py first
        # But let's assume it will be there.
        dialog = create_window("macro_editor", self.mw, modal=True)
        if dialog:
            if macro_data:
                dialog.load_macro(macro_data)
            if dialog.exec():
                self.load_macros_ui()
                self.mw.reload_commands()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _toggle_disable(self):
        checked = self.btn_disable.isChecked()
        self.btn_disable.setProperty("qa_state", "enabled" if checked else "disabled")
        self.btn_disable.style().unpolish(self.btn_disable)
        self.btn_disable.style().polish(self.btn_disable)
        self.btn_disable.setText(f"Disable Keywords: {'ON' if checked else 'OFF'}")

    def _clear_warning(self):
        self.lbl_warning.hide()
        self.lbl_warning.setText("")

    def _validate(self):
        """Return (ok, error_message)."""
        seen = {}
        for type_code, inp in self._inputs.items():
            val = inp.text().strip()
            if not val:
                # Empty = keyword disabled for this type — allowed
                continue
            key = val.lower()
            if key in seen:
                conflict = seen[key]
                return False, (
                    f"Conflict: '{val}' is already used by "
                    f"'{conflict}' and '{type_code}'."
                )
            seen[key] = type_code
        return True, ""

    # ── Config I/O ────────────────────────────────────────────────────────────

    def load_config(self):
        cfg = load_commands_config()

        disabled = not cfg.get("keywords_enabled", True)
        self.btn_disable.setChecked(disabled)
        self.btn_disable.setProperty("qa_state", "enabled" if disabled else "disabled")
        self.btn_disable.style().unpolish(self.btn_disable)
        self.btn_disable.style().polish(self.btn_disable)
        self.btn_disable.setText(f"Disable Keywords: {'ON' if disabled else 'OFF'}")

        keywords = cfg.get("keywords", {})
        for type_code, inp in self._inputs.items():
            inp.setText(keywords.get(type_code, DEFAULT_COMMANDS_CONFIG["keywords"].get(type_code, "")))

    def save_config(self):
        ok, err = self._validate()
        if not ok:
            self.lbl_warning.setText(err)
            self.lbl_warning.show()
            return

        keywords = {}
        for type_code, inp in self._inputs.items():
            val = inp.text().strip()
            if val:
                keywords[type_code] = val
            # If empty, the keyword is omitted → that type won't match any prefix

        data = {
            "keywords_enabled": not self.btn_disable.isChecked(),
            "keywords": keywords,
        }

        path = get_data_path("commands_config.json")
        os.makedirs(get_data_path(), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Hot-reload in running components
            from Core.functions.search import load_commands_config as _lcc
            fresh = _lcc()
            self.mw._commands_config = fresh
            if self.mw.search_bar_overlay is not None:
                self.mw.search_bar_overlay.commands_config = fresh

            self.mw.append_log(" Commands configuration saved!", THEME_USER_COLORS["success"])
            self.accept()
        except Exception as e:
            self.mw.append_log(f" Error saving commands: {e}", THEME_USER_COLORS["error"])
