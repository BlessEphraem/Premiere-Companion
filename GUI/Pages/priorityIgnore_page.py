# GUI/Pages/priorityIgnore_page.py
import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QListWidget, QListWidgetItem,
                             QWidget, QCheckBox, QSpinBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QSize, QTimer
from Core.paths import get_data_path
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
from Core.configs.labels_config import get_display_label, is_video, is_audio, is_transition, is_preset, is_command
from Core.configs.priority_ignore_config import DEFAULT_PRIORITY_IGNORE_CONFIG


# ── Groupe meta-data ──────────────────────────────────────────────────────────

_GROUP_ROWS = [
    ("FX.V",   "Video Effects"),
    ("FX.A",   "Audio Effects"),
    ("TR.V",   "Video Transitions"),
    ("PRST",   "Presets"),
    ("CMD",    "Commands"),
]


# ── Widget par item dans la liste ─────────────────────────────────────────────

class IgnoreItemWidget(QWidget):
    def __init__(self, clean_name, match_name, effect_type,
                 checked=False, priority_value=0):
        super().__init__()
        self.setObjectName("effectItem")
        self.match_name = match_name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            THEME_SPACING["padding_small"],
            THEME_SPACING["padding_tiny"],
            THEME_SPACING["padding_small"],
            THEME_SPACING["padding_tiny"],
        )
        layout.setSpacing(THEME_SPACING["spacing_element"])

        # Checkbox (ignore)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)

        # Type tag
        type_key = "unknown"
        if is_command(effect_type):      type_key = "TagCommand"
        elif is_preset(effect_type):     type_key = "TagPreset"
        elif is_transition(effect_type): type_key = "TagTransition"
        elif is_video(effect_type):      type_key = "TagVideo"
        elif is_audio(effect_type):      type_key = "TagAudio"

        lbl_tag = QLabel(get_display_label(effect_type))
        lbl_tag.setObjectName("EffectTag")
        lbl_tag.setProperty("type", type_key)

        lbl_name = QLabel(clean_name)
        lbl_name.setObjectName("effectName")

        # Priority spinbox (0 = no individual priority)
        lbl_prio = QLabel("Prio:")
        lbl_prio.setObjectName("CardLabelSubtle")

        self.prio_spin = QSpinBox()
        self.prio_spin.setRange(0, 999)
        self.prio_spin.setValue(priority_value)
        self.prio_spin.setFixedWidth(70)
        self.prio_spin.setToolTip("0 = no individual priority  |  1–999 = pinned within its group")
        self.prio_spin.setSpecialValueText("—")   # shows "—" when value is 0

        layout.addWidget(self.checkbox)
        layout.addWidget(lbl_tag)
        layout.addWidget(lbl_name)
        layout.addStretch()
        layout.addWidget(lbl_prio)
        layout.addWidget(self.prio_spin)

    def is_checked(self):
        return self.checkbox.isChecked()

    def priority_value(self):
        return self.prio_spin.value()


# ── Page principale ───────────────────────────────────────────────────────────

class PriorityIgnorePage(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.setModal(True)
        self._item_widgets = {}    # match_name -> IgnoreItemWidget
        self._group_spins  = {}    # type_code  -> QSpinBox
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(self._apply_filter)
        self.init_ui()
        self._build_list()
        self.load_config()

    # ── UI ────────────────────────────────────────────────────────────────────

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
        lbl_icon.setPixmap(icon_pixmap("broom", size=THEME_SPACING["icon_large"]))
        lbl_icon.setFixedSize(THEME_SPACING["icon_large"], THEME_SPACING["icon_large"])
        lbl_icon.setScaledContents(True)
        lbl_title = QLabel("Priority & Ignore")
        lbl_title.setObjectName("PageTitle")
        title_layout.addWidget(lbl_icon)
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # ── Priority section ──────────────────────────────────────────────────
        prio_card = QFrame()
        prio_card.setObjectName("CardFrame")
        prio_layout = QVBoxLayout(prio_card)
        prio_layout.setContentsMargins(
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
        )
        prio_layout.setSpacing(THEME_SPACING["spacing_element"])

        lbl_prio_title = QLabel("Priority")
        lbl_prio_title.setObjectName("CardLabelBold")
        prio_layout.addWidget(lbl_prio_title)

        lbl_prio_desc = QLabel(
            "Set the display rank of each type group (1 = first).\n"
            "Items with individual priority are pinned within their group — never above a higher-ranked group."
        )
        lbl_prio_desc.setObjectName("CardLabelSubtle")
        lbl_prio_desc.setWordWrap(True)
        prio_layout.addWidget(lbl_prio_desc)

        defaults = DEFAULT_PRIORITY_IGNORE_CONFIG["group_priority"]
        for type_code, label in _GROUP_ROWS:
            row = QHBoxLayout()
            row.setSpacing(THEME_SPACING["spacing_element"])

            lbl = QLabel(label)
            lbl.setObjectName("CardLabel")

            spin = QSpinBox()
            spin.setRange(1, 99)
            spin.setValue(defaults.get(type_code, 99))
            spin.setFixedWidth(70)

            self._group_spins[type_code] = spin

            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(spin)
            prio_layout.addLayout(row)

        layout.addWidget(prio_card)

        # ── Ignore section ────────────────────────────────────────────────────
        ignore_card = QFrame()
        ignore_card.setObjectName("CardFrame")
        ignore_layout = QVBoxLayout(ignore_card)
        ignore_layout.setContentsMargins(
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
            THEME_SPACING["margin_card"], THEME_SPACING["margin_card"],
        )
        ignore_layout.setSpacing(THEME_SPACING["spacing_element"])

        lbl_ignore_title = QLabel("Ignore")
        lbl_ignore_title.setObjectName("CardLabelBold")
        ignore_layout.addWidget(lbl_ignore_title)

        lbl_ignore_desc = QLabel(
            "Check items to hide them from all lists and searches.\n"
            "Set a Prio value (1–999) to pin an item at the top of its group."
        )
        lbl_ignore_desc.setObjectName("CardLabelSubtle")
        lbl_ignore_desc.setWordWrap(True)
        ignore_layout.addWidget(lbl_ignore_desc)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter list...")
        self.search_input.textChanged.connect(self._on_filter_changed)
        ignore_layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("MainEffectList")
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        ignore_layout.addWidget(self.list_widget)

        layout.addWidget(ignore_card)

        # Footer
        footer_layout = QHBoxLayout()
        self.lbl_count = QLabel("0 ignored")
        self.lbl_count.setObjectName("CardLabelSubtle")
        footer_layout.addWidget(self.lbl_count)
        footer_layout.addStretch()

        btn_save = QPushButton()
        btn_save.setIcon(icon("save"))
        btn_save.setText(" Save")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_config)
        footer_layout.addWidget(btn_save)

        layout.addLayout(footer_layout)

    # ── List building ─────────────────────────────────────────────────────────

    def _build_list(self):
        self.list_widget.clear()
        self._item_widgets.clear()

        all_items = list(self.mw.all_effects) + list(self.mw.all_presets) + list(self.mw.all_commands)
        for item_data in all_items:
            d_name = item_data.get("displayName", "")
            m_name = item_data.get("matchName", "")
            e_type = item_data.get("type", "Unknown")
            clean  = self.mw.cleaner.clean_name(d_name, e_type)

            widget = IgnoreItemWidget(clean, m_name, e_type)
            widget.checkbox.stateChanged.connect(self._update_count)
            self._item_widgets[m_name] = widget

            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 45))
            list_item.setData(Qt.ItemDataRole.UserRole, clean.lower())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, widget)

        self._update_count()

    # ── Interactions ──────────────────────────────────────────────────────────

    def _on_item_clicked(self, list_item):
        widget = self.list_widget.itemWidget(list_item)
        if isinstance(widget, IgnoreItemWidget):
            widget.checkbox.setChecked(not widget.checkbox.isChecked())

    def _on_filter_changed(self):
        self._filter_timer.start(150)

    def _apply_filter(self):
        query = self.search_input.text().lower().strip()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            name_data = item.data(Qt.ItemDataRole.UserRole) or ""
            item.setHidden(bool(query) and query not in name_data)

    def _update_count(self):
        checked = sum(1 for w in self._item_widgets.values() if w.is_checked())
        total   = len(self._item_widgets)
        self.lbl_count.setText(f"{checked} / {total} ignored")

    # ── Config I/O ────────────────────────────────────────────────────────────

    def load_config(self):
        from Core.functions.search import load_priority_ignore_config
        cfg = load_priority_ignore_config()

        # Group priority spinboxes
        for type_code, spin in self._group_spins.items():
            spin.setValue(cfg["group_priority"].get(
                type_code,
                DEFAULT_PRIORITY_IGNORE_CONFIG["group_priority"].get(type_code, 99)
            ))

        # Item priorities
        prio_map = {p["match_name"]: p["value"] for p in cfg.get("priority", [])}

        # Ignore + item priority
        for m_name in cfg.get("ignore", []):
            if m_name in self._item_widgets:
                w = self._item_widgets[m_name]
                w.checkbox.blockSignals(True)
                w.checkbox.setChecked(True)
                w.checkbox.blockSignals(False)

        for m_name, value in prio_map.items():
            if m_name in self._item_widgets:
                self._item_widgets[m_name].prio_spin.setValue(value)

        self._update_count()

    def save_config(self):
        path = get_data_path("priority_ignore_config.json")
        os.makedirs(get_data_path(), exist_ok=True)

        group_priority = {
            type_code: spin.value()
            for type_code, spin in self._group_spins.items()
        }

        priority = [
            {"match_name": mn, "value": w.priority_value()}
            for mn, w in self._item_widgets.items()
            if w.priority_value() > 0
        ]

        ignore = [mn for mn, w in self._item_widgets.items() if w.is_checked()]

        data = {"group_priority": group_priority, "priority": priority, "ignore": ignore}

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            self.mw.append_log(
                f" Priority & Ignore saved ({len(ignore)} ignored, {len(priority)} pinned).",
                THEME_USER_COLORS["success"],
            )
            self.mw.refresh_ui(effects=True, presets=True)

            # Update open SearchBar cache immediately
            if self.mw.search_bar_overlay is not None:
                self.mw.search_bar_overlay.priority_ignore_config = data

            self.accept()
        except Exception as e:
            self.mw.append_log(f" Error saving: {e}", THEME_USER_COLORS["error"])
