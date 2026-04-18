# Modules/SearchBar.py
import os
import sys
import json
from Core.paths import get_data_path
from Core.functions.search import (save_last_used, load_search_history, save_history_list,
                                    load_commands_config, load_searchbar_config, load_priority_ignore_config)
from Core.functions.icon_loader import icon, icon_pixmap
from Core.theme_qss import THEME_USER_COLORS, THEME_SPACING, THEME_TYPOGRAPHY, hex_to_rgba
from Core.configs.labels_config import get_type_codes, is_video, is_audio, is_transition, is_preset, is_command
from Modules.apply_effect import EffectApplier
from Modules.apply_preset import PresetApplier
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget, 
                             QListWidgetItem, QLabel, QHBoxLayout, QFrame, QApplication, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QPoint, QEvent
from PyQt6.QtGui import QColor, QPalette, QBrush

_BM_ALIASES = {
    "position": "position", "pos": "position",
    "scale": "scale",       "scl": "scale",
    "rotation": "rotation", "rot": "rotation",
    "opacity": "opacity",   "opc": "opacity",
}

def _detect_bm_query(query):
    """If query looks like '<prop_alias> <value>', return a dynamic BM command item list."""
    parts = query.split(None, 1)
    if len(parts) < 2:
        return []
    prop = _BM_ALIASES.get(parts[0])
    raw = parts[1].strip()
    if not prop or not raw:
        return []

    if raw.lower() == "reset":
        return [{
            "displayName": f"{prop.capitalize()}  Reset",
            "matchName": f"CMD.BM.{prop}.dynamic",
            "type": "CMD.BM",
            "custom_data": "reset",
            "dynamic": True,
        }]

    from Core.functions.cmd_actions import parse_bm_value
    parsed = parse_bm_value(prop, raw)
    if not parsed:
        return []

    def _fmt(op, val):
        if val is None:
            return None
        if op == "add":
            return f"+{val:g}"
        if op == "sub":
            return f"-{val:g}"
        return f"{val:g}"

    if prop == "position":
        xs = _fmt(parsed["op_x"], parsed["val_x"])
        ys = _fmt(parsed["op_y"], parsed["val_y"])
        if xs and ys and xs == ys:
            display = f"Position  {xs}"
        elif xs and ys:
            display = f"Position  X:{xs}  Y:{ys}"
        elif xs:
            display = f"Position  X:{xs}"
        else:
            display = f"Position  Y:{ys}"
    else:
        display = f"{prop.capitalize()}  {_fmt(parsed['op_x'], parsed['val_x'])}"

    return [{
        "displayName": display,
        "matchName": f"CMD.BM.{prop}.dynamic",
        "type": "CMD.BM",
        "custom_data": raw,
        "dynamic": True,
    }]


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
        return hex_to_rgba(THEME_USER_COLORS.get("sb_bg", "#18181b"), opacity)

    def apply_dynamic_styles(self):
        """Applique les styles dynamiques en utilisant les couleurs du thème en cache"""
        font_size  = self.config.get("font_size", 15)
        bg_opacity = self.config.get("bg_opacity", 0.85)

        bg_sec = self.theme_colors.get("sb_bg",     THEME_USER_COLORS["sb_bg"])
        border = self.theme_colors.get("sb_border", THEME_USER_COLORS["sb_border"])
        subtle = self.theme_colors.get("text_subtle", THEME_USER_COLORS["text_subtle"])

        bg_sec_rgba = self.get_rgba_from_hex(bg_sec, bg_opacity)

        filter_color = self._get_filter_text_color()
        text_color   = filter_color if filter_color else self.theme_colors.get("sb_input_text", THEME_USER_COLORS["sb_input_text"])

        self.container.setStyleSheet(f"""
            QFrame#SearchBarContainer {{
                background-color: {bg_sec_rgba};
                border: 1px solid {border};
                border-radius: {THEME_SPACING['radius_large']};
            }}
            QLineEdit#SearchInput {{
                background: transparent;
                border: none;
                color: {text_color};
                font-size: {font_size + 2}px;
                font-weight: bold;
                padding: {THEME_SPACING['padding_small']}px;
            }}
            QLineEdit#SearchInput::placeholder {{
                color: {subtle};
            }}
            QListWidget#SearchResults {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget#SearchResults::item {{
                background: transparent;
                padding: 4px;
                border-radius: {THEME_SPACING['radius_small']};
                margin: {THEME_SPACING['margin_search_result_item']} 5px;
            }}
            QListWidget#SearchResults::item:selected {{
                background-color: {self.theme_colors.get('sb_item_hover', THEME_USER_COLORS['sb_item_hover'])};
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
        self.search_input.setPlaceholderText("All")
        self.search_input.textChanged.connect(self.update_results)
        self.search_input.installEventFilter(self)

        search_row.addWidget(self.search_input, 1)
        container_layout.addLayout(search_row)
        
        # ── Results List ──────────────────────────────────────────────────────
        self.results_list = QListWidget()
        self.results_list.setObjectName("SearchResults")
        self.results_list.itemClicked.connect(self.apply_selected)
        container_layout.addWidget(self.results_list)
        
        layout.addWidget(self.container)
        self.apply_dynamic_styles()

    def show_bar(self):
        self.mode = "search"
        self.results_list.show()
        self.search_input.clear()
        self.update_results("")
        self.search_input.setFocus()
        self.apply_filter_style()
        self.center_on_screen()
        self.show()
        self.activateWindow()
        self.focus_timer.start(100)

    def show_transition_options(self, match_name, effect_type):
        """Affiche les options d'alignement directement dans la liste"""
        self.mode = "alignment"
        self.pending_transition = (match_name, effect_type)
        self.results_list.clear()
        self.search_input.setText(f"Align: {match_name}")
        self.search_input.selectAll()
        
        options = [
            {"displayName": "At Start", "matchName": "start", "type": "ALIGN"},
            {"displayName": "At End",   "matchName": "end",   "type": "ALIGN"},
            {"displayName": "Both Sides (Center)", "matchName": "both", "type": "ALIGN"}
        ]
        
        for opt in options:
            list_item = QListWidgetItem(self.results_list)
            list_item.setSizeHint(QSize(0, 38))
            list_item.setData(Qt.ItemDataRole.UserRole, opt)
            
            widget = QWidget()
            widget.setStyleSheet("background: transparent; border: none;")
            w_layout = QHBoxLayout(widget)
            w_layout.setContentsMargins(10, 0, 10, 0)
            
            name = QLabel(opt["displayName"])
            name.setStyleSheet(f"color: {self.theme_colors.get('sb_item_text', THEME_USER_COLORS['sb_item_text'])}; font-weight: bold; font-size: {THEME_TYPOGRAPHY['font_search_result']}px; background: transparent;")
            w_layout.addWidget(name)
            self.results_list.setItemWidget(list_item, widget)
            
        self.results_list.setCurrentRow(2) # Default to 'Both'
        self.results_list.show()
        self.center_on_screen()
        self.show()
        self.activateWindow()
        self.results_list.setFocus()

    def apply_selected(self):
        item = self.results_list.currentItem()
        if not item: return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        
        # Gestion du mode ALIGNEMENT (Transitions)
        if self.mode == "alignment":
            align = data.get("matchName", "both")
            m_name, e_type = self.pending_transition
            EffectApplier.apply_effect_to_premiere(m_name, e_type, alignment=align)
            save_last_used(m_name, e_type, m_name)
            self.close_bar()
            return

        match_name = data.get("matchName", "")
        effect_type = data.get("type", "Unknown")
        
        try:
            skip_typing = False
            if is_preset(effect_type) and self.search_input.text().strip() == "":
                if self.config.get("apply_last_without_name_enter", False):
                    last_used = load_search_history().get("last_used")
                    if last_used and last_used.get("match_name") == match_name:
                        skip_typing = True

            if is_command(effect_type):
                from Core.functions.cmd_actions import execute_cmd_action
                custom_data = data.get("custom_data")
                execute_cmd_action(match_name, self.main_window, custom_data=custom_data)
                if match_name.endswith(".dynamic") and custom_data is not None:
                    save_last_used(match_name, effect_type, data.get("displayName", match_name), custom_data=custom_data)
                self.close_bar()
            elif is_preset(effect_type):
                config = PresetApplier.load_config()
                is_qa = config.get("quick_apply_enabled", False) if config else False
                success, msg = PresetApplier.apply_preset_to_premiere(match_name, is_qa, skip_typing=skip_typing)
                if not success:
                    self.main_window.append_log(f" Quick Apply error: {msg}", THEME_USER_COLORS["error"])
                else:
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
        elif key == Qt.Key.Key_Tab:
            if self.mode != "alignment" and self.results_list.count() > 0:
                item = self.results_list.currentItem()
                if item:
                    data = item.data(Qt.ItemDataRole.UserRole)
                    raw  = data.get("displayName", "")
                    clean = self.main_window.cleaner.clean_name(raw, data.get("type", ""))
                    if clean.startswith("\x00LASTUSED\x00"):
                        clean = clean[len("\x00LASTUSED\x00"):]
                    self.search_input.setText(clean)
                    self.search_input.setCursorPosition(len(clean))
            event.accept()
            return
        elif key == Qt.Key.Key_Down:
            if self.results_list.count() > 0:
                self.results_list.setCurrentRow((self.results_list.currentRow() + 1) % self.results_list.count())
        elif key == Qt.Key.Key_Up:
            if self.results_list.count() > 0:
                self.results_list.setCurrentRow((self.results_list.currentRow() - 1) % self.results_list.count())
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.apply_selected()
        super().keyPressEvent(event)

    def _get_filter_text_color(self):
        """Retourne la couleur associée au filtre actuel, ou None pour 'All' (texte normal)."""
        try:
            idx  = self.main_window.current_filter_idx
            mode = self.main_window.filter_modes[idx]
        except (AttributeError, IndexError):
            return None
        if mode["name"] == "All":
            return None
        color_map = {
            "error":   self.theme_colors.get("error",         THEME_USER_COLORS["error"]),
            "success": self.theme_colors.get("success",       THEME_USER_COLORS["success"]),
            "info":    self.theme_colors.get("info",          THEME_USER_COLORS["info"]),
            "white":   self.theme_colors.get("sb_input_text", THEME_USER_COLORS["sb_input_text"]),
            "warning": self.theme_colors.get("warning",       THEME_USER_COLORS["warning"]),
        }
        return color_map.get(mode.get("color", "white"))

    def eventFilter(self, obj, event):
        if obj is self.search_input and event.type() == QEvent.Type.KeyPress:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.key() == Qt.Key.Key_Right:
                    self.main_window.cycle_filter(1)
                    return True
                elif event.key() == Qt.Key.Key_Left:
                    self.main_window.cycle_filter(-1)
                    return True
        return super().eventFilter(obj, event)

    def apply_filter_style(self):
        try:
            idx  = self.main_window.current_filter_idx
            mode = self.main_window.filter_modes[idx]
        except (AttributeError, IndexError):
            return
        self.search_input.setPlaceholderText(mode["name"])
        self.apply_dynamic_styles()

    def update_results(self, text):
        if self.mode == "alignment": return
        self.results_list.clear()
        
        query = text.lower().strip()
        items = []
        items.extend(self.main_window.all_effects)
        items.extend(self.main_window.all_presets)
        items.extend(self.main_window.all_commands)
        
        # History is now a dict: {"last_used": ..., "history": [match_names]}
        history_data = load_search_history()
        history_list = history_data.get("history", [])
        
        filter_type = self.main_window.filter_modes[self.main_window.current_filter_idx]["type"]
        
        scored_items = []
        for item in items:
            m_name = item.get("matchName", "")
            e_type = item.get("type", "Unknown")
            d_name = item.get("displayName", "")
            
            if filter_type != "All":
                if is_video(e_type) and filter_type != "FX.V": continue
                if is_audio(e_type) and filter_type != "FX.A": continue
                if is_transition(e_type) and filter_type != "TR.V": continue
                if is_preset(e_type) and filter_type != "PRST": continue
                if is_command(e_type) and filter_type != "CMD": continue
            
            clean_name = self.main_window.cleaner.clean_name(d_name, e_type)
            score = 0
            
            if m_name.endswith(".dynamic"):
                score += 100000
            
            if query:
                if query in clean_name.lower(): score += 100
                if clean_name.lower().startswith(query): score += 50
                if query in m_name.lower(): score += 20
                if score == 0: continue
            else:
                # Mode Initial : on montre TOUT.
                # Les récents ont un score de 1000+, les autres ont un score de 1.
                if m_name in history_list:
                    score = 2000 - history_list.index(m_name)
                else:
                    score = 1
            
            if not query and self.config.get("apply_last_on_empty_enter", False):
                last_used = history_data.get("last_used")
                if last_used and m_name == last_used.get("match_name") and e_type == last_used.get("type"):
                    clean_name = f"\x00LASTUSED\x00{clean_name}"
                    score += 10000
            
            if m_name in history_list:
                score += 500 # Boost constant pour les récents
                
            if m_name.endswith(".dynamic"):
                score += 100000
                
            scored_items.append((score, item, clean_name))

        # Inject dynamic BM commands when query contains a prop alias + value
        bm_items = _detect_bm_query(query)
        for bm_item in bm_items:
            scored_items.append((300000, bm_item, bm_item["displayName"]))

        # Inject recent dynamic commands from history (e.g. last "opacity 0" used)
        dynamic_data = history_data.get("dynamic_data", {})
        injected_names = {bm["matchName"] for bm in bm_items}
        for i, mname in enumerate(history_list):
            dd = dynamic_data.get(mname)
            if not dd:
                continue
            if mname in injected_names:
                continue  # User is actively typing a new value for this prop — skip the old recent
            if filter_type != "All" and not (is_command(dd["type"]) and filter_type == "CMD"):
                continue
            if query and query not in dd["displayName"].lower() and query not in mname.lower():
                continue
            recent_item = {
                "displayName": dd["displayName"],
                "matchName": mname,
                "type": dd["type"],
                "custom_data": dd["custom_data"],
                "dynamic": True,
            }
            scored_items.append((2000 - i + 500, recent_item, dd["displayName"]))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        
        max_items = self.config.get("max_items", 100)
        for _, item, clean_name in scored_items[:max_items]:
            m_name = item.get("matchName", "")
            e_type = item.get("type", "Unknown")
            
            list_item = QListWidgetItem(self.results_list)
            list_item.setSizeHint(QSize(0, 38))
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            widget = QWidget()
            widget.setStyleSheet("background: transparent; border: none;")
            w_layout = QHBoxLayout(widget)
            w_layout.setContentsMargins(10, 0, 10, 0)
            w_layout.setSpacing(10)
            
            tag = QLabel(f" {e_type} ")
            tag.setObjectName("EffectTag")
            tag.setFixedHeight(18)
            
            filter_color = {
                "FX.V":   self.theme_colors.get("error",      THEME_USER_COLORS["error"]),
                "FX.A":   self.theme_colors.get("success",    THEME_USER_COLORS["success"]),
                "TR.V":   self.theme_colors.get("info",       THEME_USER_COLORS["info"]),
                "PRST":   self.theme_colors.get("btn_accent_2", THEME_USER_COLORS["btn_accent_2"]),
                "CMD":    self.theme_colors.get("warning",    THEME_USER_COLORS["warning"]),
                "CMD.QA": self.theme_colors.get("warning",    THEME_USER_COLORS["warning"]),
                "CMD.BM": self.theme_colors.get("warning",    THEME_USER_COLORS["warning"]),
                "CMD.MA": self.theme_colors.get("warning",    THEME_USER_COLORS["warning"]),
            }

            tag_color = filter_color.get(e_type, THEME_USER_COLORS["text_white"])
            tag.setStyleSheet(f"background-color: {self.get_rgba_from_hex(tag_color, 0.15)}; color: {tag_color}; border: 1px solid {tag_color}; border-radius: 4px; font-size: {THEME_TYPOGRAPHY['font_tag']}px; font-weight: bold;")

            item_color      = self.theme_colors.get("sb_item_text",   THEME_USER_COLORS["sb_item_text"])
            last_used_color = self.theme_colors.get("sb_last_used",  THEME_USER_COLORS["sb_last_used"])
            recent_color    = self.theme_colors.get("sb_recent_icon", THEME_USER_COLORS["sb_recent_icon"])

            is_last_used = clean_name.startswith("\x00LASTUSED\x00")
            if is_last_used:
                clean_name = clean_name[len("\x00LASTUSED\x00"):]

            name = QLabel()
            name.setStyleSheet(f"font-weight: bold; font-size: {THEME_TYPOGRAPHY['font_search_item']}px; background: transparent;")
            name.setText(f"<span style='color:{item_color}'>{clean_name}</span>")

            w_layout.addWidget(tag)
            w_layout.addWidget(name, 1)

            if is_last_used or m_name in history_list:
                clock_color = last_used_color if is_last_used else recent_color
                clock_lbl = QLabel()
                clock_lbl.setPixmap(icon_pixmap("clock", color=clock_color, size=14))
                clock_lbl.setFixedSize(14, 14)
                clock_lbl.setScaledContents(True)
                clock_lbl.setStyleSheet("background: transparent;")
                w_layout.addWidget(clock_lbl)

            self.results_list.setItemWidget(list_item, widget)
            
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def apply_selected(self):
        item = self.results_list.currentItem()
        if not item: return
        
        data = item.data(Qt.ItemDataRole.UserRole)

        # Gestion du mode ALIGNEMENT (Transitions)
        if self.mode == "alignment":
            align = data.get("matchName", "both")
            m_name, e_type = self.pending_transition
            EffectApplier.apply_effect_to_premiere(m_name, e_type, alignment=align)
            save_last_used(m_name, e_type, m_name)
            self.close_bar()
            return

        match_name = data.get("matchName", "")
        effect_type = data.get("type", "Unknown")
        
        try:
            skip_typing = False
            if is_preset(effect_type) and self.search_input.text().strip() == "":
                if self.config.get("apply_last_without_name_enter", False):
                    last_used = load_search_history().get("last_used")
                    if last_used and last_used.get("match_name") == match_name:
                        skip_typing = True

            if is_command(effect_type):
                from Core.functions.cmd_actions import execute_cmd_action
                custom_data = data.get("custom_data")
                execute_cmd_action(match_name, self.main_window, custom_data=custom_data)
                if match_name.endswith(".dynamic") and custom_data is not None:
                    save_last_used(match_name, effect_type, data.get("displayName", match_name), custom_data=custom_data)
                self.close_bar()
            elif is_preset(effect_type):
                config = PresetApplier.load_config()
                is_qa = config.get("quick_apply_enabled", False) if config else False
                success, msg = PresetApplier.apply_preset_to_premiere(match_name, is_qa, skip_typing=skip_typing)
                if not success:
                    self.main_window.append_log(f" Quick Apply error: {msg}", THEME_USER_COLORS["error"])
                else:
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
