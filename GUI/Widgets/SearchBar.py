# Modules/SearchBar.py
import os
import sys
import json
from Core.paths import get_data_path
from Core.functions.search import (save_last_used, load_search_history, save_history_list,
                                    load_commands_config, load_searchbar_config, load_priority_ignore_config)
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_USER_COLORS, THEME_SPACING
from Core.configs.labels_config import get_type_codes, is_video, is_audio, is_transition, is_preset, is_command
from Modules.apply_effect import EffectApplier
from Modules.apply_preset import PresetApplier
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget, 
                             QListWidgetItem, QLabel, QHBoxLayout, QFrame, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QPoint
from PyQt6.QtGui import QColor, QPalette, QBrush

class FloatingSearchBar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config_path = get_data_path("searchbar_config.json")
        
        self.theme_colors = THEME_USER_COLORS.copy()
        self.load_config()
        self.commands_config = load_commands_config()
        self.priority_ignore_config = load_priority_ignore_config()
        self.load_theme()
        self.mode = "search"
        self.pending_transition = None
        self.setObjectName("FloatingSearchBar")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        # Apply blur if enabled
        if self.config.get("blur_background", False):
            try:
                from BlurWindow.blurWindow import GlobalBlur
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                GlobalBlur(self.winId(), Dark=True, QWidget=self)
            except:
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(self.config.get("window_width", 600), self.config.get("window_height", 420))
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.check_focus)
        self.init_ui()

    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        self.config = {
            "max_items": 100,
            "max_recent": 3,
            "window_width": 600,
            "window_height": 420,
            "font_size": 15,
            "bg_opacity": 0.85,
            "blur_background": False,
            "apply_last_on_empty_enter": False,
            "apply_last_without_name_enter": False
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config.update(json.load(f))
            except Exception:
                pass

    def load_theme(self):
        """Charge les couleurs de thème une seule fois"""
        theme_path = get_data_path("theme.json")
        if os.path.exists(theme_path):
            try:
                with open(theme_path, "r", encoding="utf-8") as f:
                    self.theme_colors.update(json.load(f))
            except Exception:
                pass

    def get_rgba_from_hex(self, hex_color, opacity=0.2):
        """Convert hex to rgba using QColor"""
        try:
            color = QColor(hex_color)
            if color.isValid():
                return f"rgba({color.red()}, {color.green()}, {color.blue()}, {opacity})"
        except Exception:
            pass
        return "rgba(24, 24, 27, 0.85)"

    def apply_dynamic_styles(self):
        """Applique les styles dynamiques en utilisant les couleurs du thème en cache"""
        font_size = self.config.get("font_size", 15)
        bg_opacity = self.config.get("bg_opacity", 0.85)
        
        bg_sec = self.theme_colors.get("input_bg", "#18181b")
        border = self.theme_colors.get("hover", "#27272a")
        
        bg_sec_rgba = self.get_rgba_from_hex(bg_sec, bg_opacity)
        
        self.container.setStyleSheet(f"""
            QFrame#SearchBarContainer {{
                background-color: {bg_sec_rgba};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QLineEdit#SearchInput {{
                background: transparent;
                border: none;
                color: {self.theme_colors.get('text_white', '#ffffff')};
                font-size: {font_size + 2}px;
                font-weight: bold;
                padding: 10px;
            }}
            QListWidget#SearchResults {{
                background: transparent;
                border: none;
                color: {self.theme_colors.get('text_white', '#ffffff')};
                font-size: {font_size}px;
                outline: none;
            }}
            QListWidget#SearchResults::item {{
                padding: 8px;
                border-radius: 6px;
            }}
            QListWidget#SearchResults::item:selected {{
                background-color: {self.theme_colors.get('hover', '#27272a')};
                color: {self.theme_colors.get('text_white', '#ffffff')};
            }}
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame()
        self.container.setObjectName("SearchBarContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)
        
        # ── Search Input Row ──────────────────────────────────────────────────
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search Effects & Presets...")
        self.search_input.textChanged.connect(self.update_results)
        
        self.filter_label = QLabel("[All]")
        self.filter_label.setObjectName("EffectTag")
        self.filter_label.setFixedWidth(60)
        self.filter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.filter_label)
        container_layout.addLayout(search_row)
        
        # ── Results List ──────────────────────────────────────────────────────
        self.results_list = QListWidget()
        self.results_list.setObjectName("SearchResults")
        self.results_list.itemClicked.connect(self.apply_selected)
        container_layout.addWidget(self.results_list)
        
        # ── Options Row (Visible only for transitions) ────────────────────────
        self.options_frame = QFrame()
        self.options_frame.hide()
        options_layout = QHBoxLayout(self.options_frame)
        options_layout.setContentsMargins(0, 5, 0, 0)
        
        self.lbl_opt_info = QLabel("Apply Transition:")
        self.lbl_opt_info.setObjectName("CardLabelBold")
        
        self.btn_start = QPushButton("At Start")
        self.btn_end = QPushButton("At End")
        self.btn_both = QPushButton("Both")
        
        for b in (self.btn_start, self.btn_end, self.btn_both):
            b.setFixedWidth(80)
            b.clicked.connect(self._on_option_clicked)
            options_layout.addWidget(b)
            
        options_layout.insertWidget(0, self.lbl_opt_info)
        options_layout.addStretch()
        container_layout.addWidget(self.options_frame)
        
        layout.addWidget(self.container)
        self.apply_dynamic_styles()

    def show_bar(self):
        self.mode = "search"
        self.options_frame.hide()
        self.results_list.show()
        self.search_input.clear()
        self.search_input.setFocus()
        self.apply_filter_style()
        self.center_on_screen()
        self.show()
        self.activateWindow()
        self.focus_timer.start(100)

    def show_transition_options(self, match_name, effect_type):
        self.mode = "options"
        self.pending_transition = (match_name, effect_type)
        self.results_list.hide()
        self.search_input.setText(f"Apply: {match_name}")
        self.options_frame.show()
        self.center_on_screen()
        self.show()
        self.activateWindow()
        self.btn_both.setFocus()
        self.focus_timer.start(100)

    def _on_option_clicked(self):
        if not self.pending_transition: return
        btn = self.sender()
        align = "both"
        if btn == self.btn_start: align = "start"
        elif btn == self.btn_end: align = "end"
        
        m_name, e_type = self.pending_transition
        EffectApplier.apply_effect_to_premiere(m_name, e_type, alignment=align)
        save_last_used(m_name, e_type, m_name)
        self.close_bar()

    def check_focus(self):
        if not self.isActiveWindow():
            self.close_bar()

    def close_bar(self):
        self.focus_timer.stop()
        self.hide()
        self.pending_transition = None

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close_bar()
        elif key == Qt.Key.Key_Down:
            self.results_list.setCurrentRow((self.results_list.currentRow() + 1) % self.results_list.count())
        elif key == Qt.Key.Key_Up:
            self.results_list.setCurrentRow((self.results_list.currentRow() - 1) % self.results_list.count())
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.mode == "search":
                self.apply_selected()
            else:
                self._on_option_clicked()
        elif key == Qt.Key.Key_Right:
            if self.search_input.cursorPosition() == len(self.search_input.text()):
                self.main_window.cycle_filter(1)
        elif key == Qt.Key.Key_Left:
            if self.search_input.cursorPosition() == 0:
                self.main_window.cycle_filter(-1)
        super().keyPressEvent(event)

    def apply_filter_style(self):
        idx = self.main_window.current_filter_idx
        mode = self.main_window.filter_modes[idx]
        self.filter_label.setText(f"[{mode['name']}]")
        
        color_map = {
            "error":   self.theme_colors["error"],
            "success": self.theme_colors["success"],
            "info":    self.theme_colors["info"],
            "white":   self.theme_colors["text_white"],
            "warning": self.theme_colors["warning"],
        }
        
        color_key = mode.get("color", "white")
        text_color = color_map.get(color_key, self.theme_colors["text_main"])
        
        if mode["name"] == "All":
            text_color = self.theme_colors["warning"]
            
        self.filter_label.setStyleSheet(f"color: {text_color}; font-weight: bold;")

    def update_results(self, text):
        if self.mode == "options": return
        self.results_list.clear()
        
        query = text.lower().strip()
        
        # Build filtered list
        items = []
        items.extend(self.main_window.all_effects)
        items.extend(self.main_window.all_presets)
        items.extend(self.main_window.all_commands)
        
        # Load history for scoring
        history = load_search_history()
        
        filter_type = self.main_window.filter_modes[self.main_window.current_filter_idx]["type"]
        
        scored_items = []
        for item in items:
            m_name = item.get("matchName", "")
            e_type = item.get("type", "Unknown")
            d_name = item.get("displayName", "")
            
            # Type filter
            if filter_type != "All":
                if is_video(e_type) and filter_type != "FX.V": continue
                if is_audio(e_type) and filter_type != "FX.A": continue
                if is_transition(e_type) and filter_type != "TR.V": continue
                if is_preset(e_type) and filter_type != "PRST": continue
                if is_command(e_type) and filter_type != "CMD": continue
            
            # Text filter
            clean_name = self.main_window.cleaner.clean_name(d_name, e_type)
            score = 0
            if query:
                if query in clean_name.lower(): score += 10
                if query in m_name.lower(): score += 5
                if score == 0: continue
            
            # History bonus
            if m_name in history:
                score += history[m_name] * 2
                
            scored_items.append((score, item, clean_name))
            
        scored_items.sort(key=lambda x: x[0], reverse=True)
        
        # Display limit
        max_items = self.config.get("max_items", 100)
        for _, item, clean_name in scored_items[:max_items]:
            m_name = item.get("matchName", "")
            e_type = item.get("type", "Unknown")
            
            list_item = QListWidgetItem(self.results_list)
            list_item.setSizeHint(QSize(0, 40))
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            # Simple custom widget for list item
            widget = QWidget()
            w_layout = QHBoxLayout(widget)
            w_layout.setContentsMargins(5, 2, 5, 2)
            
            tag = QLabel(f"[{e_type}]")
            tag.setObjectName("EffectTag")
            
            filter_color = {
                "FX.V": self.theme_colors["error"],
                "FX.A": self.theme_colors["success"],
                "TR.V": self.theme_colors["info"],
                "PRST": self.theme_colors["text_white"],
                "CMD":  self.theme_colors["warning"],
                "CMD.QA": self.theme_colors["warning"],
                "CMD.BM": self.theme_colors["warning"],
                "CMD.MA": self.theme_colors["warning"],
            }
            
            tag_color = filter_color.get(e_type, self.theme_colors["text_white"])
            tag.setStyleSheet(f"color: {tag_color}; font-weight: bold;")
            
            name = QLabel(clean_name)
            name.setStyleSheet(f"color: {self.theme_colors['text_white']}; font-weight: bold;")
            
            w_layout.addWidget(tag)
            w_layout.addWidget(name, 1)
            self.results_list.setItemWidget(list_item, widget)
            
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def apply_selected(self):
        item = self.results_list.currentItem()
        if not item: return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        match_name = data.get("matchName", "")
        effect_type = data.get("type", "Unknown")
        
        try:
            if is_command(effect_type):
                from Core.functions.cmd_actions import execute_cmd_action
                execute_cmd_action(match_name, self.main_window)
                self.close_bar()
            elif is_preset(effect_type):
                config = PresetApplier.load_config()
                is_qa = config.get("quick_apply_enabled", False) if config else False
                PresetApplier.apply_preset_to_premiere(match_name, is_qa)
                save_last_used(match_name, effect_type, match_name)
                self.close_bar()
            elif is_transition(effect_type):
                self.show_transition_options(match_name, effect_type)
            else:
                EffectApplier.apply_effect_to_premiere(match_name, effect_type)
                save_last_used(match_name, effect_type, match_name)
                self.close_bar()
        except Exception as e:
            self.main_window.append_log(f" SearchBar Error: {e}", THEME_USER_COLORS["error"])
