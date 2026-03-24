# GUI/main_window.py
import sys
import os
import subprocess
import json
import keyboard
from PyQt6.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, 
                             QTextEdit, QHBoxLayout, QLineEdit, QListWidget, 
                             QPushButton, QStackedWidget, QFrame, QToolTip)
from PyQt6.QtCore import Qt, QRect, QTimer, QObject, pyqtSignal, QEvent, QSize
from PyQt6.QtGui import QCursor

from Core.server import ServerWorker
from Core.cleaner import EffectCleaner
from Core.hotkeys import GlobalHotkeyManager

from GUI.item_list import EffectItemWidget
from GUI.settings_page import SettingsPage
from GUI.keymaps_page import KeymapsPage
from GUI.regex_page import RegexPage

from Modules.SearchBar import FloatingSearchBar

class HotkeySignal(QObject):
    trigger_search_bar = pyqtSignal()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Companion - V3")
        self.resize(750, 850)
        self.setMinimumSize(500, 600)

        self.cleaner = EffectCleaner()
        self.all_effects = []
        self.all_presets = []
        self.cache_path = os.path.join("Data", "effects_cache.json")
        self.presets_cache_path = os.path.join("Data", "presets_cache.json")
        self.settings_path = os.path.join("Data", "settings.json")
        self.settings = self.load_settings()

        self.filter_modes = [
            {"name": "All", "type": "All"},
            {"name": "Video", "type": "FxVideo"},
            {"name": "Audio", "type": "FxAudio"},
            {"name": "Transitions", "type": "Transition"},
            {"name": "Presets", "type": "Preset"}
        ]
        self.current_filter_idx = 0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        nav_layout = QHBoxLayout()
        self.btn_main = QPushButton("✨ Effects")
        self.btn_main.setObjectName("NavButton")
        self.btn_regex = QPushButton("🧹 Regex Clean")
        self.btn_regex.setObjectName("NavButton")
        self.btn_keys = QPushButton("⌨️ Keymaps")
        self.btn_keys.setObjectName("NavButton")
        self.btn_settings = QPushButton("⚙️ Settings")
        self.btn_settings.setObjectName("NavButton")
        
        self.nav_buttons = [self.btn_main, self.btn_regex, self.btn_keys, self.btn_settings]
        for btn in self.nav_buttons:
            nav_layout.addWidget(btn)
        
        # Init active state
        self.btn_main.setProperty("active", True)
        
        self.btn_main.clicked.connect(lambda: self.switch_page(0, self.btn_main))
        self.btn_regex.clicked.connect(lambda: self.switch_page(3, self.btn_regex))
        self.btn_keys.clicked.connect(lambda: self.switch_page(2, self.btn_keys))
        self.btn_settings.clicked.connect(lambda: self.switch_page(1, self.btn_settings))
        main_layout.addLayout(nav_layout)

        sep = QFrame()
        sep.setObjectName("separatorLine")
        sep.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(sep)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.page_main = QWidget()
        page_main_layout = QVBoxLayout(self.page_main)
        page_main_layout.setContentsMargins(0, 0, 0, 0)

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("MainSearchBar")
        self.search_bar.installEventFilter(self)
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.execute_filter)
        self.search_bar.textChanged.connect(lambda: self.search_timer.start(150))
        page_main_layout.addWidget(self.search_bar)

        self.effect_list = QListWidget()
        self.last_selected_widget = None
        self.effect_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.effect_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        page_main_layout.addWidget(self.effect_list)

        actions_layout = QHBoxLayout()

        # --- Fetch Effects Button
        btn_fetch_effects = QPushButton("🔄 Fetch Effects")
        btn_fetch_effects.setObjectName("PrimaryButton") # Style bleu dans ton QSS
        btn_fetch_effects.clicked.connect(self.trigger_fetch_script)
        
        # --- Fetch Presets Button
        btn_fetch_presets = QPushButton("📁 Fetch Presets")
        btn_fetch_presets.setObjectName("AccentButton")  # Style violet dans ton QSS
        btn_fetch_presets.clicked.connect(self.sync_presets) # On va créer cette fonction plus bas

        actions_layout.addWidget(btn_fetch_effects)
        actions_layout.addWidget(btn_fetch_presets)

        page_main_layout.addLayout(actions_layout)

        self.page_settings = SettingsPage(self)
        self.page_keymaps = KeymapsPage(self)
        self.page_regex = RegexPage(self)

        self.stacked_widget.addWidget(self.page_main)
        self.stacked_widget.addWidget(self.page_settings)
        self.stacked_widget.addWidget(self.page_keymaps)
        self.stacked_widget.addWidget(self.page_regex)

        # --- Console Section
        self.log_console = QTextEdit()
        self.log_console.setObjectName("LogConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setFixedHeight(120)
        main_layout.addWidget(self.log_console)

        self.status_label = QLabel("🔴 Waiting for Premiere Pro...")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setProperty("connected", False)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.worker = ServerWorker()
        self.worker.log_signal.connect(self.append_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.effects_signal.connect(self.populate_effects)
        self.worker.tooltip_signal.connect(self.show_tooltip_error) 
        self.worker.start()

        self.temp_effects = []
        self.sync_timer = QTimer()
        self.sync_timer.setSingleShot(True)
        self.sync_timer.timeout.connect(self.finalize_sync)

        self.search_bar_overlay = FloatingSearchBar(self)
        self.hotkey_signal = HotkeySignal()
        self.hotkey_signal.trigger_search_bar.connect(self.search_bar_overlay.show_bar)
        
        self.hotkey_manager = GlobalHotkeyManager(
            trigger_callback=self.hotkey_signal.trigger_search_bar.emit,
            log_callback=self.append_log
        )

        self.apply_filter_style()
        self.update_global_hotkey()
        self.load_presets()

    def eventFilter(self, obj, event):
        if obj == self.search_bar and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Right:
                if self.search_bar.cursorPosition() == len(self.search_bar.text()):
                    self.cycle_filter(1)
                    return True
            elif event.key() == Qt.Key.Key_Left:
                if self.search_bar.cursorPosition() == 0:
                    self.cycle_filter(-1)
                    return True
        return super().eventFilter(obj, event)

    def cycle_filter(self, direction):
        self.current_filter_idx = (self.current_filter_idx + direction) % len(self.filter_modes)
        self.apply_filter_style()
        self.execute_filter()
        if self.search_bar_overlay.mode != "options":
            self.search_bar_overlay.apply_filter_style()
            self.search_bar_overlay.update_results(self.search_bar_overlay.search_input.text())

    def apply_filter_style(self):
        mode = self.filter_modes[self.current_filter_idx]
        self.search_bar.setPlaceholderText(f"🔍 Search ({mode['name']})...")
        self.search_bar.setProperty("filterType", mode["type"])
        self.search_bar.style().unpolish(self.search_bar)
        self.search_bar.style().polish(self.search_bar)

    def switch_page(self, index, active_btn):
        self.stacked_widget.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        active_btn.setProperty("active", True)
        active_btn.style().unpolish(active_btn)
        active_btn.style().polish(active_btn)

    def load_settings(self):
        # 1. Tes réglages de base (à compléter au fur et à mesure des versions)
        defaults = {
            "quick_apply_enabled": False,
            "last_filter": "All" # Exemple d'ajout futur
        }
        
        if not os.path.exists(self.settings_path):
            return defaults
    
        try:
            with open(self.settings_path, "r") as f:
                data = json.load(f)
                
            # 2. Vérifier si on doit mettre à jour le fichier (si des clés manquent)
            needs_update = False
            for key, value in defaults.items():
                if key not in data:
                    data[key] = value
                    needs_update = True
            
            # 3. Si on a ajouté des nouvelles options, on sauvegarde le fichier propre
            if needs_update:
                self.settings = data # On met à jour l'attribut de classe
                self.save_settings() # On utilise ta fonction de sauvegarde existante
                
            return data
        except: 
            return defaults

    def save_settings(self):
        os.makedirs("Data", exist_ok=True)
        with open(self.settings_path, "w") as f: json.dump(self.settings, f)

    def update_global_hotkey(self):
        self.hotkey_manager.update_global_hotkey()

    def load_presets(self):
        if os.path.exists(self.presets_cache_path):
            try:
                with open(self.presets_cache_path, "r", encoding="utf-8") as f: self.all_presets = json.load(f)
            except: pass
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f: self.all_effects = json.load(f)
            except: pass
        self.refresh_full_list()

    def apply_regex_rules(self):
        self.append_log("🔄 RegEx rules updated. Refreshing...", "#55ccff")
        self.refresh_full_list()
        self.switch_page(0, self.btn_main)

    def trigger_fetch_script(self):
        try:
            self.temp_effects = [] 
            self.append_log("Executing fetch_effects.py script... Please wait.", "#aaaaaa")
            subprocess.Popen([sys.executable, os.path.join("Modules", "fetch_effects.py")])
        except Exception as e:
            self.append_log(f"Execution error: {e}", "#ff5555")

    def populate_effects(self, effects):
        self.temp_effects.extend(effects)
        self.sync_timer.start(500)

    def sync_presets(self):
        """Lance le script de récupération des presets en utilisant la version configurée"""
        from Modules.fetch_preset import fetch_presets
        from Modules.apply_preset import PresetApplier
        import os

        self.append_log("⚡ Scanning for Premiere Presets...", "#55ccff")
        
        try:
            config = PresetApplier.load_config()
            target_version = config.get("selected_version") if config else None

            if not target_version:
                docs_path = os.path.expanduser(r"~\Documents\Adobe\Premiere Pro")
                if not os.path.exists(docs_path):
                    self.append_log("❌ Adobe folder not found in Documents.", "#ff5555")
                    return

                versions = [f for f in os.listdir(docs_path) 
                            if os.path.isdir(os.path.join(docs_path, f)) and f[0].isdigit()]
                
                if not versions:
                    self.append_log("❌ No valid Premiere version found.", "#ff5555")
                    return
                
                versions.sort(key=lambda x: os.path.getmtime(os.path.join(docs_path, x)), reverse=True)
                target_version = versions[0]
                
                default_data = config if config else {}
                default_data["selected_version"] = target_version
                PresetApplier.save_config(default_data)

            fetch_presets(target_version)
            
            self.load_presets() 
            self.refresh_full_list()
            self.execute_filter()
            
            self.append_log(f"✅ Presets synced from v{target_version}!", "#55ff55")

        except Exception as e:
            self.append_log(f"❌ Preset Sync Error: {e}", "#ff5555")

    def finalize_sync(self):
        self.all_effects = self.temp_effects
        self.temp_effects = []
        os.makedirs("Data", exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f: json.dump(self.all_effects, f, indent=4)
        self.refresh_full_list()
        self.append_log(f"✅ Database saved with {len(self.all_effects)} effects.", "#55ff55")

    def refresh_full_list(self):
        self.last_selected_widget = None
        self.effect_list.clear()
        combined_list = self.all_effects + self.all_presets
        for effect in combined_list:
            raw_d_name = effect.get("displayName", "")
            m_name = effect.get("matchName", "")
            e_type = effect.get("type", "Unknown")
            clean_d_name = self.cleaner.clean_name(raw_d_name, e_type)
            
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem()
            widget = EffectItemWidget(clean_d_name, m_name, e_type, self, self.effect_list)
            item.setSizeHint(QSize(0, 45)) 
            item.setData(Qt.ItemDataRole.UserRole, {"clean_name": clean_d_name.lower(), "match_name": m_name.lower(), "type": e_type})
            self.effect_list.addItem(item)
            self.effect_list.setItemWidget(item, widget)
        self.execute_filter()

    def execute_filter(self):
        query_text = self.search_bar.text().lower().strip()
        query_words = query_text.split() if query_text else []
        
        current_mode = self.filter_modes[self.current_filter_idx]["type"]

        for i in range(self.effect_list.count()):
            item = self.effect_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            e_type = data.get("type", "")
            
            matches_type = True
            if current_mode != "All":
                if current_mode == "FxVideo" and ("FxVideo" not in e_type or "Transition" in e_type): matches_type = False
                elif current_mode == "FxAudio" and ("FxAudio" not in e_type or "Transition" in e_type): matches_type = False
                elif current_mode == "Transition" and "Transition" not in e_type: matches_type = False
                elif current_mode == "Preset" and "Preset" not in e_type: matches_type = False

            target_text = f"{data['clean_name']} {data['match_name']}"
            matches_text = True
            if query_words:
                matches_text = all(word in target_text for word in query_words)

            item.setHidden(not (matches_text and matches_type))

    def on_selection_changed(self):
        if self.last_selected_widget:
            try: self.last_selected_widget.btn_apply.setVisible(False)
            except RuntimeError: pass
        current_item = self.effect_list.currentItem()
        if current_item:
            widget = self.effect_list.itemWidget(current_item)
            if widget:
                widget.btn_apply.setVisible(True)
                self.last_selected_widget = widget
        else:
            self.last_selected_widget = None

    def on_item_double_clicked(self, item):
        widget = self.effect_list.itemWidget(item)
        if widget: widget.btn_apply.click()

    def append_log(self, message, color="#ffffff"):
        self.log_console.append(f'<span style="color:{color};">{message}</span>')
        self.log_console.verticalScrollBar().setValue(self.log_console.verticalScrollBar().maximum())

    def update_status(self, is_connected):
        self.status_label.setText("🟢 Premiere Pro Connected" if is_connected else "🔴 Waiting for Premiere Pro...")
        self.status_label.setProperty("connected", is_connected)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def show_tooltip_error(self, message):
        QToolTip.showText(QCursor.pos(), f"⚠️ {message}", self, QRect(), 3000)