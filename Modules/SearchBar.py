# Modules/SearchBar.py
import os
import sys
import json
from Core.paths import get_data_path
import win32gui
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget, 
                             QListWidgetItem, QApplication, QFrame, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt, QEvent, QTimer, QSize
from PyQt6.QtGui import QCursor
from Modules.apply_effect import EffectApplier
from Modules.apply_preset import PresetApplier

class FloatingSearchBar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.history_file = get_data_path("search_history.json")
        self.config_path = get_data_path("searchbar_config.json")
        
        # 1. Chargement de la configuration
        self.load_config()
        self.recent_items = self.load_history()
        self.mode = "search"
        self.pending_transition = None

        self.setObjectName("FloatingSearchBar")

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 2. Application de la taille dynamique au démarrage
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
            "font_size": 15
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config.update(json.load(f))
            except Exception:
                pass

    def apply_dynamic_styles(self):
        """Applique la taille de police dynamiquement sans casser le QSS global"""
        font_size = self.config.get("font_size", 15)
        self.container.setStyleSheet(f"""
            QLineEdit#SearchInput {{ font-size: {font_size + 1}px; }}
            QListWidget#SearchList {{ font-size: {font_size}px; }}
            QLabel#SearchResultName {{ font-size: {font_size}px; }}
            QLabel#EffectTag {{ font-size: {font_size - 1}px; }}
        """)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame(self)
        self.container.setObjectName("SearchBarContainer")
        main_layout.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.textChanged.connect(self.update_results)
        self.search_input.installEventFilter(self)
        layout.addWidget(self.search_input)

        self.results_list = QListWidget()
        self.results_list.setObjectName("SearchList")
        self.results_list.itemDoubleClicked.connect(self.execute_selected)
        layout.addWidget(self.results_list)

    def apply_filter_style(self):
        if self.mode == "options": return
        mode = self.main_window.filter_modes[self.main_window.current_filter_idx]
        
        self.search_input.setProperty("mode", "search")
        self.search_input.setProperty("filterType", mode["type"])
        self.search_input.setPlaceholderText(f"Search ({mode['name']})...")
        self.search_input.style().unpolish(self.search_input)
        self.search_input.style().polish(self.search_input)

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f: return json.load(f)
            except: pass
        return []

    def save_history(self, match_name):
        if match_name in self.recent_items: self.recent_items.remove(match_name)
        self.recent_items.insert(0, match_name)
        
        # 3. Limite dynamique des éléments récents
        max_recent = self.config.get("max_recent", 3)
        self.recent_items = self.recent_items[:max_recent]

        os.makedirs(get_data_path(), exist_ok=True)
        with open(self.history_file, "w") as f: json.dump(self.recent_items, f)
    def check_focus(self):
        if not self.isVisible():
            self.focus_timer.stop()
            return
            
        if sys.platform == "win32":
            hwnd = int(self.winId())
            fg_hwnd = win32gui.GetForegroundWindow()
            if fg_hwnd != hwnd:
                self.hide_bar()

    def show_bar_only(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus()

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        
        if screen:
            geom = screen.availableGeometry()
        else:
            geom = QApplication.primaryScreen().availableGeometry()
            
        self.move(geom.center().x() - self.width() // 2, geom.center().y() - self.height() // 2)

        self.focus_timer.start(100)

    def show_bar(self):
        # 4. Recharge la configuration et applique les tailles à chaque ouverture !
        self.load_config()
        self.resize(self.config.get("window_width", 600), self.config.get("window_height", 420))
        self.apply_dynamic_styles()
        
        self.mode = "search"
        self.search_input.setReadOnly(False)
        self.apply_filter_style()
        self.search_input.clear()
        self.update_results("")
        self.show_bar_only()

    def show_transition_options(self, match_name, effect_type):
        self.mode = "options"
        self.pending_transition = {"match_name": match_name, "type": effect_type}
        
        self.search_input.clear()
        self.search_input.setPlaceholderText("Choose alignment (Enter to validate)")
        self.search_input.setProperty("mode", "options")
        self.search_input.style().unpolish(self.search_input)
        self.search_input.style().polish(self.search_input)
        self.search_input.setReadOnly(True)
        self.results_list.clear()

        options = [
            {"display": "➡️ At Start", "value": "start"},
            {"display": "⬅️ At End", "value": "end"},
            {"display": "↔️ Both", "value": "both"}
        ]

        font_size = self.config.get("font_size", 15)

        for opt in options:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, int(font_size * 3))) # S'adapte à la police
            item.setData(Qt.ItemDataRole.UserRole, opt)
            self.results_list.addItem(item)
            
            lbl = QLabel(opt["display"])
            lbl.setStyleSheet(f"background: transparent; color: white; font-size: {font_size}px; font-weight: bold; margin-left: 5px;")
            lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.results_list.setItemWidget(item, lbl)

        self.results_list.setCurrentRow(0)
        self.show_bar_only()

    def hide_bar(self):
        self.focus_timer.stop()
        self.hide()
        self.clearFocus()
        self.mode = "search"
        self.search_input.setReadOnly(False)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            self.hide_bar()
        super().changeEvent(event)

    def update_results(self, query):
        if self.mode == "options": return 
        
        self.results_list.clear()
        
        query_text = query.lower().strip()
        query_words = query_text.split() if query_text else []
        
        all_items = self.main_window.all_effects + self.main_window.all_presets
        scored_items = []
        
        current_mode = self.main_window.filter_modes[self.main_window.current_filter_idx]["type"]

        for item in all_items:
            d_name = item.get("displayName", "")
            m_name = item.get("matchName", "")
            e_type = item.get("type", "Unknown")
            clean_name = self.main_window.cleaner.clean_name(d_name, e_type)
            
            if current_mode != "All":
                is_transition = "Transition" in e_type
                is_preset = "Preset" in e_type
                is_video = "FxVideo" in e_type and not is_transition
                is_audio = "FxAudio" in e_type and not is_transition

                if current_mode == "FxVideo" and not is_video: continue
                if current_mode == "FxAudio" and not is_audio: continue
                if current_mode == "Transition" and not is_transition: continue
                if current_mode == "Preset" and not is_preset: continue

            target_text = f"{clean_name.lower()} {m_name.lower()}"
            if query_words and not all(word in target_text for word in query_words): 
                continue

            score = 0
            
            if m_name in self.recent_items: 
                score += 100000 + (3 - self.recent_items.index(m_name)) * 1000
                
            if query_text:
                if clean_name.lower() == query_text:
                    score += 50000
                elif clean_name.lower().startswith(query_text):
                    score += 40000
                elif query_text in clean_name.lower():
                    score += 30000
                elif query_text in target_text:
                    score += 20000
                    
                if e_type == "FxVideo": score += 4
                elif "Transition" in e_type: score += 3
                elif e_type == "FxAudio": score += 2
                elif e_type == "Preset": score += 1

            scored_items.append({"clean_name": clean_name, "match_name": m_name, "type": e_type, "score": score})

        scored_items.sort(key=lambda x: x["score"], reverse=True)
        
        # 5. Limite dynamique du nombre total d'éléments affichés
        max_items = self.config.get("max_items", 100)
        scored_items = scored_items[:max_items] 

        font_size = self.config.get("font_size", 15)

        for data in scored_items:
            is_recent = data["match_name"] in self.recent_items
            tag_text = "Recent" if is_recent else data["type"]
            
            if is_recent:
                tag_key = "TagRecent"
            else:
                if "FxVideo" in tag_text and "Transition" not in tag_text: tag_key = "TagVideo"
                elif "FxAudio" in tag_text and "Transition" not in tag_text: tag_key = "TagAudio"
                elif "Transition" in tag_text: tag_key = "TagTransition"
                elif "Preset" in tag_text: tag_key = "TagPreset"
                else: tag_key = "unknown"
            
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, int(font_size * 3))) # S'adapte à la taille de la police
            item.setData(Qt.ItemDataRole.UserRole, data)
            self.results_list.addItem(item)
            
            row_widget = QWidget()
            item_layout = QHBoxLayout(row_widget)
            item_layout.setContentsMargins(10, 0, 10, 0)
            item_layout.setSpacing(8)

            # Tag Label
            lbl_tag = QLabel(f"[{tag_text}]")
            lbl_tag.setObjectName("EffectTag")
            lbl_tag.setProperty("type", tag_key)
            lbl_tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            
            # Tag Effect
            lbl_name = QLabel(data["clean_name"])
            lbl_name.setObjectName("SearchResultName")
            lbl_name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            item_layout.addWidget(lbl_tag)
            item_layout.addWidget(lbl_name, 1)
            
            self.results_list.setItemWidget(item, row_widget)

        if self.results_list.count() > 0: self.results_list.setCurrentRow(0)

    def eventFilter(self, obj, event):
        if obj == self.search_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                current = self.results_list.currentRow()
                if current < self.results_list.count() - 1: self.results_list.setCurrentRow(current + 1)
                return True
            elif event.key() == Qt.Key.Key_Up:
                current = self.results_list.currentRow()
                if current > 0: self.results_list.setCurrentRow(current - 1)
                return True
            elif event.key() == Qt.Key.Key_Right and self.mode != "options":
                if self.search_input.cursorPosition() == len(self.search_input.text()):
                    self.main_window.cycle_filter(1)
                    return True
            elif event.key() == Qt.Key.Key_Left and self.mode != "options":
                if self.search_input.cursorPosition() == 0:
                    self.main_window.cycle_filter(-1)
                    return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.execute_selected()
                return True
            elif event.key() == Qt.Key.Key_Escape:
                self.hide_bar()
                return True
        return super().eventFilter(obj, event)

    def execute_selected(self):
        current_item = self.results_list.currentItem()
        if not current_item: return

        data = current_item.data(Qt.ItemDataRole.UserRole)
        
        if self.mode == "options":
            alignment = data["value"]
            match_name = self.pending_transition["match_name"]
            effect_type = self.pending_transition["type"]
            self.hide_bar()
            self.save_history(match_name)
            self.main_window.append_log(f"⚡ SearchBar: Transition '{match_name}' ({alignment})", "#55ccff")
            try:
                EffectApplier.apply_effect_to_premiere(match_name, effect_type, alignment)
            except Exception as e:
                self.main_window.append_log(f"❌ Error sending to Premiere: {e}", "#ff5555")
            return

        match_name = data["match_name"]
        effect_type = data["type"]

        if "Transition" in effect_type:
            self.show_transition_options(match_name, effect_type)
            return

        self.hide_bar()
        self.save_history(match_name)

        try:
            if effect_type == "Preset":
                is_qa = self.main_window.settings.get("quick_apply_enabled", False)
                self.main_window.append_log(f"⚡ SearchBar: Apply Preset '{match_name}'", "#55ccff")
                success, msg = PresetApplier.apply_preset_to_premiere(match_name, is_qa)
                self.main_window.append_log(f"✅ {msg}" if success else f"❌ {msg}", "#55ff55" if success else "#ff5555")
            else:
                self.main_window.append_log(f"⚡ SearchBar: Apply Effect '{match_name}'", "#55ccff")
                EffectApplier.apply_effect_to_premiere(match_name, effect_type)
        except Exception as e:
            self.main_window.append_log(f"❌ SearchBar Error: {e}", "#ff5555")