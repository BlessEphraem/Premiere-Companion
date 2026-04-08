# GUI/regex_page.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, 
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                             QInputDialog, QFrame)
from PyQt6.QtCore import Qt, QSize
from Core.functions.regex import AutoRegexEngine
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS

class RegexItemWidget(QWidget):
    def __init__(self, rule, list_widget, parent_page):
        super().__init__()
        self.rule = rule
        self.list_widget = list_widget
        self.parent_page = parent_page

        layout = QHBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"], THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"])

        # Rules List
        display_text = f"[Type: {rule.get('type', 'All')}] Find: {rule.get('pattern', '')}  |  Replace: '{rule.get('replacement', '')}'"
        self.lbl_text = QLabel(display_text)
        self.lbl_text.setObjectName("RegexRuleText") 
        layout.addWidget(self.lbl_text, stretch=1)

        # Rules Action Button
        btn_edit = QPushButton()
        btn_edit.setIcon(icon("edit"))
        btn_edit.setFixedSize(THEME_SPACING["icon_button"], THEME_SPACING["icon_button"])
        btn_edit.setObjectName("RegexEditBtn")
        btn_edit.clicked.connect(self.edit_rule)

        btn_up = QPushButton()
        btn_up.setIcon(icon("arrow-up", size=THEME_SPACING["icon_medium"]))
        btn_up.setFixedSize(THEME_SPACING["icon_button"], THEME_SPACING["icon_button"])
        btn_up.setObjectName("RegexMoveBtn")
        btn_up.clicked.connect(self.move_up)

        btn_down = QPushButton()
        btn_down.setIcon(icon("arrow-down", size=THEME_SPACING["icon_medium"]))
        btn_down.setFixedSize(THEME_SPACING["icon_button"], THEME_SPACING["icon_button"])
        btn_down.setObjectName("RegexMoveBtn")
        btn_down.clicked.connect(self.move_down)

        btn_del = QPushButton()
        btn_del.setIcon(icon("times-circle"))
        btn_del.setFixedSize(THEME_SPACING["icon_button"], THEME_SPACING["icon_button"])
        btn_del.setObjectName("RegexDeleteBtn")
        btn_del.clicked.connect(self.delete_rule)

        layout.addWidget(btn_edit)
        layout.addWidget(btn_up)
        layout.addWidget(btn_down)
        layout.addWidget(btn_del)

    def edit_rule(self):
        new_pattern, ok1 = QInputDialog.getText(self, "Edit Rule", "Find Pattern:", QLineEdit.EchoMode.Normal, self.rule.get("pattern", ""))
        if ok1:
            new_replace, ok2 = QInputDialog.getText(self, "Edit Rule", "Replacement Text:", QLineEdit.EchoMode.Normal, self.rule.get("replacement", ""))
            if ok2:
                self.rule["pattern"] = new_pattern.strip()
                self.rule["replacement"] = new_replace
                self.parent_page.mw.cleaner.save_rules()
                self.parent_page.load_rules_ui()

    def move_up(self):
        rules = self.parent_page.mw.cleaner.rules
        idx = rules.index(self.rule)
        if idx > 0:
            rules[idx], rules[idx - 1] = rules[idx - 1], rules[idx]
            self.parent_page.mw.cleaner.save_rules()
            self.parent_page.load_rules_ui()

    def move_down(self):
        rules = self.parent_page.mw.cleaner.rules
        idx = rules.index(self.rule)
        if idx < len(rules) - 1:
            rules[idx], rules[idx + 1] = rules[idx + 1], rules[idx]
            self.parent_page.mw.cleaner.save_rules()
            self.parent_page.load_rules_ui()

    def delete_rule(self):
        self.parent_page.mw.cleaner.rules.remove(self.rule)
        self.parent_page.mw.cleaner.save_rules()
        self.parent_page.load_rules_ui()


class RegexPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.init_ui()
        self.load_rules_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"])
        main_layout.setSpacing(THEME_SPACING["spacing_element"])

        add_layout = QHBoxLayout()
        self.txt_pattern = QLineEdit()
        self.txt_pattern.setFixedHeight(THEME_SPACING["height_action_input"])
        self.txt_pattern.setPlaceholderText("Word to remove (e.g., ^AE\\.)")
        self.txt_replace = QLineEdit()
        self.txt_replace.setFixedHeight(THEME_SPACING["height_action_input"])
        self.txt_replace.setPlaceholderText("Replace with (e.g., empty)")
        
        btn_add = QPushButton()
        btn_add.setIcon(icon("plus"))
        btn_add.setText(" Add")
        btn_add.setFixedHeight(THEME_SPACING["height_action_input"])
        btn_add.clicked.connect(self.add_rule_ui)

        info_label = QLabel(
            "Premiere Pro's API doesn't provide clean names for transitions. "
            "Auto-Generate focuses on transitions - check your imports. "
            "Example: 'Motion Tween' appears as 'Impact Animate' in code."
        )
        info_label.setWordWrap(True)
        info_label.setObjectName("RegexInfoLabel")
        main_layout.addWidget(info_label)
        
        add_layout.addWidget(self.txt_pattern)
        add_layout.addWidget(self.txt_replace)
        add_layout.addWidget(btn_add)
        main_layout.addLayout(add_layout)

        self.list_rules = QListWidget()
        self.list_rules.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        main_layout.addWidget(self.list_rules)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(THEME_SPACING["spacing_element"])
        
        btn_gen = QPushButton()
        btn_gen.setIcon(icon("magic"))
        btn_gen.setText(" Auto-Generate Rules")
        btn_gen.setObjectName("AccentButton")
        btn_gen.clicked.connect(self.generate_rules_ui)
        
        btn_save = QPushButton()
        btn_save.setIcon(icon("sync", size=THEME_SPACING["icon_medium"]))
        btn_save.setText(" Reload Rules")
        btn_save.setObjectName("ReloadRulesBtn")
        btn_save.clicked.connect(self.save_rules_ui)

        btn_layout.addWidget(btn_save, 1)
        btn_layout.addWidget(btn_gen, 1)
        main_layout.addLayout(btn_layout)

    def load_rules_ui(self):
        self.list_rules.clear()
        for rule in self.mw.cleaner.rules:
            item = QListWidgetItem(self.list_rules)
            item.setSizeHint(QSize(0, 50))
            
            widget = RegexItemWidget(rule, self.list_rules, self)
            self.list_rules.setItemWidget(item, widget)

    def add_rule_ui(self):
        pattern = self.txt_pattern.text().strip()
        if pattern:
            rule = {"type": "TR.V", "pattern": pattern, "replacement": self.txt_replace.text()}
            self.mw.cleaner.rules.append(rule)
            self.mw.cleaner.save_rules()
            self.load_rules_ui()
            self.txt_pattern.clear()
            self.txt_replace.clear()

    def generate_rules_ui(self):
        # On s'assure que les effets sont charges
        if not self.mw.all_effects:
            self.mw.load_effects()

        if not self.mw.all_effects:
            QMessageBox.warning(self, "Error", "Sync effects first before generating rules.")
            return

        # On prend les TR.V (deja mappes par load_effects)
        t_names = [e["matchName"] for e in self.mw.all_effects if "TR.V" in str(e.get("type", ""))]
        all_names = [e["matchName"] for e in self.mw.all_effects]
        
        self.mw.append_log(f" Analyzing {len(t_names)} transitions...", THEME_USER_COLORS["info_text"])
        new_rules = AutoRegexEngine.generate_rules(t_names, all_names)
        
        if new_rules:
            for r in new_rules:
                if not any(existing["pattern"] == r["pattern"] for existing in self.mw.cleaner.rules):
                    self.mw.cleaner.rules.append(r)
            self.mw.cleaner.save_rules()
            self.load_rules_ui()
            self.mw.append_log(f" Generated {len(new_rules)} rules.", THEME_USER_COLORS["success"])
        else:
            self.mw.append_log(" No new obvious patterns detected.", THEME_USER_COLORS["warning"])

    def save_rules_ui(self):
        self.mw.cleaner.save_rules()
        self.mw.append_log(" Rules force reloaded.", THEME_USER_COLORS["success"])
        if self.mw.all_effects:
            self.mw.refresh_ui(effects=True, presets=True)