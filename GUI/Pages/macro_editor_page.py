# GUI/Pages/macro_editor_page.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                             QFrame, QCompleter, QWidget, QDialogButtonBox, QSpinBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from Core.paths import get_data_path
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
from Core.configs.labels_config import get_type_codes, is_video, is_audio, is_transition, is_preset, is_command
from Core.configs.macros_config import load_macros_config, save_macros_config
import json
import os


# ── Helpers ───────────────────────────────────────────────────────────────────

_ALIGNMENT_LABELS = {
    "start": "At Start",
    "end":   "At End",
    "both":  "Both Sides",
}


def _needs_edit(action):
    """Return True if this action type has configurable params."""
    e_type = action.get("type", "")
    return (e_type == "SLEEP"
            or is_transition(e_type)
            or action.get("matchName", "").endswith(".dynamic"))


def _params_summary(action):
    """Short suffix appended to the label to show current param values."""
    e_type = action.get("type", "")
    params = action.get("params", {})
    if e_type == "SLEEP":
        return f"  {params.get('duration_ms', 1000)} ms"
    if is_transition(e_type):
        label = _ALIGNMENT_LABELS.get(params.get("alignment", "start"), "At Start")
        return f"  ({label})"
    if action.get("matchName", "").endswith(".dynamic"):
        cd = params.get("custom_data", "")
        return f"  → {cd}" if cd else "  → ?"
    return ""


# ── Alignment picker dialog ───────────────────────────────────────────────────

class AlignmentPickerDialog(QDialog):
    def __init__(self, parent, current="start"):
        super().__init__(parent)
        self.setWindowTitle("Choose Alignment")
        self.setModal(True)
        self.result_value = current

        layout = QVBoxLayout(self)
        layout.setSpacing(THEME_SPACING["spacing_element"])

        lbl = QLabel("Transition alignment:")
        lbl.setObjectName("CardLabelSubtle")
        layout.addWidget(lbl)

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        for key, display in [("start", "At Start"), ("end", "At End"), ("both", "Both Sides (Center)")]:
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.list.addItem(item)
            if key == current:
                self.list.setCurrentItem(item)
        self.list.itemDoubleClicked.connect(self._accept)
        layout.addWidget(self.list)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self):
        cur = self.list.currentItem()
        if cur:
            self.result_value = cur.data(Qt.ItemDataRole.UserRole)
        self.accept()


# ── Dynamic value dialog ──────────────────────────────────────────────────────

class DynamicValueDialog(QDialog):
    def __init__(self, parent, prop, current_value=""):
        super().__init__(parent)
        self.setWindowTitle(f"Set Value — {prop.capitalize()}")
        self.setModal(True)
        self.prop = prop
        self.result_value = current_value

        layout = QVBoxLayout(self)
        layout.setSpacing(THEME_SPACING["spacing_element"])

        hint_extra = " &nbsp; <code>100.200</code> &nbsp; <code>.500</code>" if prop == "position" else ""
        lbl = QLabel(
            f"Value for <b>{prop.capitalize()}</b>:<br>"
            f"<small>Examples: <code>50</code> &nbsp; <code>+10</code> &nbsp; "
            f"<code>-5</code> &nbsp; <code>reset</code>{hint_extra}</small>"
        )
        lbl.setWordWrap(True)
        lbl.setObjectName("CardLabelSubtle")
        layout.addWidget(lbl)

        placeholder = "reset  /  50  /  +10  /  -5" + ("  /  100.200" if prop == "position" else "")
        self.input = QLineEdit(current_value)
        self.input.setPlaceholderText(placeholder)
        self.input.setFixedHeight(THEME_SPACING["height_action_input"])
        self.input.returnPressed.connect(self._try_accept)
        layout.addWidget(self.input)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._try_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _try_accept(self):
        text = self.input.text().strip()
        if not text:
            QMessageBox.warning(self, "Empty Value", "Please enter a value.")
            return
        if text.lower() == "reset":
            self.result_value = "reset"
            self.accept()
            return
        from Core.functions.cmd_actions import parse_bm_value
        if parse_bm_value(self.prop, text) is not None:
            self.result_value = text
            self.accept()
        else:
            pos_hint = ', or X.Y for position (e.g. 100.200, .500, +10.-20).' if self.prop == "position" else '.'
            QMessageBox.warning(
                self, "Invalid Value",
                f'"{text}" is not a valid value for {self.prop.capitalize()}.\n\n'
                f'Use a number (e.g. 50), a signed delta (+10, -5), "reset"{pos_hint}'
            )


# ── Sleep dialog ──────────────────────────────────────────────────────────────

class SleepDialog(QDialog):
    def __init__(self, parent, current_ms=1000):
        super().__init__(parent)
        self.setWindowTitle("Sleep Duration")
        self.setModal(True)
        self.result_ms = current_ms

        layout = QVBoxLayout(self)
        layout.setSpacing(THEME_SPACING["spacing_element"])

        lbl = QLabel("Wait duration before the next action:")
        lbl.setObjectName("CardLabelSubtle")
        layout.addWidget(lbl)

        self.spin = QSpinBox()
        self.spin.setMinimum(1)
        self.spin.setMaximum(30000)
        self.spin.setSingleStep(100)
        self.spin.setValue(current_ms)
        self.spin.setSuffix(" ms")
        self.spin.setFixedHeight(THEME_SPACING["height_action_input"])
        layout.addWidget(self.spin)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self):
        self.result_ms = self.spin.value()
        self.accept()


# ── Action widget (one row in the macro list) ────────────────────────────────

class MacroActionWidget(QWidget):
    def __init__(self, action_data, order, list_widget, parent_page):
        super().__init__()
        self.action_data = action_data
        self.list_widget = list_widget
        self.parent_page = parent_page

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"],
            THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"]
        )
        layout.setSpacing(4)

        e_type  = action_data.get("type", "?")
        d_name  = action_data.get("displayName", "?")
        summary = _params_summary(action_data)

        if e_type == "SLEEP":
            label_text = f"{order} — Sleep{summary}"
        else:
            label_text = f"{order} — [{e_type}] {d_name}{summary}"

        self.lbl = QLabel(label_text)
        self.lbl.setObjectName("CardLabelSubtle")
        layout.addWidget(self.lbl, stretch=1)

        if _needs_edit(action_data):
            btn_edit = QPushButton()
            btn_edit.setIcon(icon("edit"))
            btn_edit.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
            btn_edit.setObjectName("RegexMoveBtn")
            btn_edit.clicked.connect(self.edit_params)
            layout.addWidget(btn_edit)

        for btn_icon, slot in [("arrow-up", self.move_up), ("arrow-down", self.move_down)]:
            btn = QPushButton()
            btn.setIcon(icon(btn_icon))
            btn.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
            btn.setObjectName("RegexMoveBtn")
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        btn_del = QPushButton()
        btn_del.setIcon(icon("times-circle"))
        btn_del.setFixedSize(THEME_SPACING["width_icon_button_fixed"], THEME_SPACING["width_icon_button_fixed"])
        btn_del.setObjectName("RegexDeleteBtn")
        btn_del.clicked.connect(self.delete_action)
        layout.addWidget(btn_del)

    def edit_params(self):
        action = self.action_data
        e_type = action.get("type", "")
        params = action.setdefault("params", {})

        if e_type == "SLEEP":
            dlg = SleepDialog(self, params.get("duration_ms", 1000))
            if dlg.exec() == QDialog.DialogCode.Accepted:
                params["duration_ms"] = dlg.result_ms
                self.parent_page.load_actions_ui()

        elif is_transition(e_type):
            dlg = AlignmentPickerDialog(self, params.get("alignment", "start"))
            if dlg.exec() == QDialog.DialogCode.Accepted:
                params["alignment"] = dlg.result_value
                self.parent_page.load_actions_ui()

        elif action.get("matchName", "").endswith(".dynamic"):
            prop = action["matchName"].split(".")[2]  # CMD.BM.<prop>.dynamic
            dlg = DynamicValueDialog(self, prop, params.get("custom_data", ""))
            if dlg.exec() == QDialog.DialogCode.Accepted:
                params["custom_data"] = dlg.result_value
                self.parent_page.load_actions_ui()

    def move_up(self):
        idx = self.parent_page.actions.index(self.action_data)
        if idx > 0:
            a = self.parent_page.actions
            a[idx], a[idx - 1] = a[idx - 1], a[idx]
            self.parent_page.load_actions_ui()

    def move_down(self):
        idx = self.parent_page.actions.index(self.action_data)
        if idx < len(self.parent_page.actions) - 1:
            a = self.parent_page.actions
            a[idx], a[idx + 1] = a[idx + 1], a[idx]
            self.parent_page.load_actions_ui()

    def delete_action(self):
        self.parent_page.actions.remove(self.action_data)
        self.parent_page.load_actions_ui()


# ── Search input with auto-add ────────────────────────────────────────────────

class MacroSearchInput(QLineEdit):
    def __init__(self, main_window, on_select=None):
        super().__init__()
        self.mw = main_window
        self._on_select = on_select
        self.setPlaceholderText("Search for Effect, Preset or Command...")
        self.completer_obj = QCompleter()
        self.completer_obj.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer_obj.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer_obj)
        # Auto-add when user clicks a completer suggestion
        self.completer_obj.activated[str].connect(self._on_completer_activated)
        self.update_completer()

    def _on_completer_activated(self, text):
        """Fired when the user clicks (or Enter-selects) a completer popup item."""
        self.setText(text)
        if self._on_select:
            self._on_select(text)

    def keyPressEvent(self, event):
        # Enter on a non-popup selection: add whatever is in the field
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not self.completer_obj.popup().isVisible():
                text = self.text().strip()
                if text and self._on_select:
                    self._on_select(text)
                return
        super().keyPressEvent(event)

    def update_completer(self):
        model = QStandardItemModel()
        from Core.functions.cmd_actions import get_dynamic_commands
        all_items = self.mw.all_effects + self.mw.all_presets + get_dynamic_commands()
        for item in all_items:
            # Exclude .dynamic variants — user adds the base command and sets value via Edit
            if item.get("matchName", "").endswith(".dynamic"):
                continue
            e_type     = item.get("type", "Unknown")
            clean_name = self.mw.cleaner.clean_name(item.get("displayName", ""), e_type)
            m_name     = item.get("matchName", "")
            model.appendRow(QStandardItem(f"[{e_type}] {clean_name} ({m_name})"))
        self.completer_obj.setModel(model)


# ── Macro editor dialog ───────────────────────────────────────────────────────

class MacroEditorPage(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.setModal(True)
        self.setWindowTitle("Macro Editor")
        self.actions = []
        self.editing_name = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"],
            THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"]
        )
        layout.setSpacing(THEME_SPACING["spacing_element"])

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Macro Name (e.g., My Awesome Macro)")
        self.name_input.setFixedHeight(THEME_SPACING["height_action_input"])
        layout.addWidget(self.name_input)

        add_frame = QFrame()
        add_frame.setObjectName("CardFrame")
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"]
        )

        # Search input auto-adds on completer click or Enter
        self.search_input = MacroSearchInput(self.mw, on_select=self.add_action)

        # "Add Sleep" replaces the old "Add to Sequence" button
        btn_sleep = QPushButton("Add Sleep")
        btn_sleep.clicked.connect(self.add_sleep_action)

        add_layout.addWidget(self.search_input, 1)
        add_layout.addWidget(btn_sleep)
        layout.addWidget(add_frame)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton(" Save Macro")
        btn_save.setIcon(icon("save"))
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_macro)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    # ── Adding actions ────────────────────────────────────────────────────────

    def add_action(self, text=None):
        search_str = (text if text is not None else self.search_input.text()).strip()
        if not search_str:
            return

        from Core.functions.cmd_actions import get_dynamic_commands
        all_items = self.mw.all_effects + self.mw.all_presets + get_dynamic_commands()

        found_item = None
        for item in all_items:
            if item.get("matchName", "").endswith(".dynamic"):
                continue
            e_type     = item.get("type", "Unknown")
            m_name     = item.get("matchName", "")
            clean_name = self.mw.cleaner.clean_name(item.get("displayName", ""), e_type)
            if search_str == f"[{e_type}] {clean_name} ({m_name})":
                found_item = {
                    "type":      e_type,
                    "matchName": m_name,
                    "displayName": clean_name,
                    "dynamic":   item.get("dynamic", False),
                }
                break

        if not found_item:
            QMessageBox.warning(self, "Invalid Selection", "Please select an item from the dropdown list.")
            return

        e_type = found_item["type"]
        m_name = found_item["matchName"]

        if is_transition(e_type):
            found_item["params"] = {"alignment": "start"}

        elif is_command(e_type) and found_item.get("dynamic"):
            # Dynamic BM command — ask for value immediately; cancel = don't add
            prop = m_name.split(".")[2] if len(m_name.split(".")) >= 3 else "value"
            found_item["matchName"] = f"{m_name}.dynamic" if not m_name.endswith(".dynamic") else m_name
            dlg = DynamicValueDialog(self, prop)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            found_item["params"] = {"custom_data": dlg.result_value}

        else:
            found_item["params"] = {}

        self.actions.append(found_item)
        self.load_actions_ui()
        self.search_input.clear()

    def add_sleep_action(self):
        dlg = SleepDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.actions.append({
                "type":        "SLEEP",
                "matchName":   "SLEEP",
                "displayName": "Sleep",
                "params":      {"duration_ms": dlg.result_ms},
            })
            self.load_actions_ui()

    # ── List rendering ────────────────────────────────────────────────────────

    def load_actions_ui(self):
        self.list_widget.clear()
        for i, action in enumerate(self.actions):
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 40))
            widget = MacroActionWidget(action, i + 1, self.list_widget, self)
            self.list_widget.setItemWidget(item, widget)

    # ── Load / Save ───────────────────────────────────────────────────────────

    def load_macro(self, macro_data):
        self.editing_name = macro_data["name"]
        self.name_input.setText(self.editing_name)
        self.actions = list(macro_data.get("actions", []))
        # Backward compat: ensure params dicts exist and transitions have a default alignment
        for action in self.actions:
            action.setdefault("params", {})
            if is_transition(action.get("type", "")) and "alignment" not in action["params"]:
                action["params"]["alignment"] = "start"
        self.load_actions_ui()

    def save_macro(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for the macro.")
            return
        if not self.actions:
            QMessageBox.warning(self, "Empty Macro", "Please add at least one action to the macro.")
            return

        # Validate dynamic commands have a value set
        for action in self.actions:
            if action.get("matchName", "").endswith(".dynamic"):
                if not action.get("params", {}).get("custom_data"):
                    QMessageBox.warning(
                        self, "Incomplete Action",
                        f'Action "{action["displayName"]}" needs a value.\n'
                        f'Click the Edit button on that action to set it.'
                    )
                    return

        config = load_macros_config()

        if name != self.editing_name and any(m["name"] == name for m in config["macros"]):
            QMessageBox.warning(self, "Duplicate Name", "A macro with this name already exists.")
            return

        new_macro = {"name": name, "actions": self.actions}

        if self.editing_name:
            config["macros"] = [
                m if m["name"] != self.editing_name else new_macro
                for m in config["macros"]
            ]
        else:
            config["macros"].append(new_macro)

        save_macros_config(config)
        self.accept()
