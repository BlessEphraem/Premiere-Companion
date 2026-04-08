# GUI/effects_page.py
import sys
import os
import subprocess
import json
import threading
import time
from PyQt6.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, 
                             QTextEdit, QHBoxLayout, QLineEdit, QListWidget, 
                             QPushButton, QStackedWidget, QFrame, QToolTip, QDialog, QApplication)
from PyQt6.QtCore import Qt, QRect, QTimer, QObject, pyqtSignal, QEvent, QSize
from PyQt6.QtGui import QCursor

DEBUG_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "debug_startup.log")

def debug_log(msg):
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] [EffectsPage] {msg}\n")

from Core.functions.server import ServerWorker, set_server_worker
from Core.cleaner import EffectCleaner
from Core.functions.hotkey_listener import GlobalHotkeyManager
from Core.paths import get_data_path
from Core.theme_qss import THEME_TYPOGRAPHY, THEME_USER_COLORS, THEME_SPACING
from Core.functions.windows import WINDOW_SIZES
from Core.configs.search_config import SEARCH_TIMER_DELAY
from Core.functions.search import (FILTER_MODES, cycle_filter, get_last_used, load_searchbar_config,
                                    load_priority_ignore_config, load_commands_config, parse_search_command)
from Core.configs.labels_config import is_video, is_audio, is_transition, is_preset, is_command
from Core.functions.cmd_actions import get_dynamic_commands
from GUI.Widgets.splash import SplashOverlay
from Core.functions.icon_loader import icon

from GUI.Widgets.ItemList import EffectItemWidget
from GUI.Widgets.Buttons import create_sync_button
from GUI.Pages.settings_page import SettingsPage
from GUI.Pages.addons_page import AddonsPage
from GUI.Widgets.Menu import NavMenu

from GUI.Widgets.SearchBar import FloatingSearchBar
from Core.functions.fetch import fetch_effects, fetch_presets
from Core.functions.bridge import (
    load_quick_apply_config,
    save_quick_apply_config,
    request_premiere_version
)

class HotkeySignal(QObject):
    trigger_search_bar = pyqtSignal()
    trigger_transition_options = pyqtSignal(str, str)
    log_signal = pyqtSignal(str, str)
    trigger_better_motion = pyqtSignal(str)

class EffectsPage(QMainWindow):
    def __init__(self):
        debug_log("__init__ started")
        super().__init__()
        debug_log("super().__init__ done")
        self.hide()  # Prevent any premature window display
        self.resize(WINDOW_SIZES["main"]["width"], WINDOW_SIZES["main"]["height"])
        self.setMinimumSize(WINDOW_SIZES["main_min"]["width"], WINDOW_SIZES["main_min"]["height"])
        self.dragging = False
        self.drag_start_pos = None
        
        # Child windows management
        self.child_windows = []

        self.cleaner = EffectCleaner()
        self.all_effects = []
        self.all_presets = []
        self.all_commands = get_dynamic_commands()
        self.cache_path = get_data_path("effects_cache.json")
        self.presets_cache_path = get_data_path("presets_cache.json")
        self.settings_path = get_data_path("settings.json")
        self.settings = self.load_settings()

        self.load_dialog = None
        self.fetch_thread = None
        self.fetch_cancelled = False
        self.splash_overlay = None
        self._effects_connection = None
        self._effects_fetch_progress = [0, 0]
        self._presets_total = 0

        self.filter_modes = FILTER_MODES
        self.current_filter_idx = 0
        self._commands_config = load_commands_config()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"], THEME_SPACING["spacing_page"])
        main_layout.setSpacing(THEME_SPACING["spacing_element"])

        def on_search_change(text):
            self.execute_filter()
        
        def on_filter_change(idx):
            self.current_filter_idx = idx
            self.execute_filter()
            if self.search_bar_overlay and self.search_bar_overlay.mode != "options":
                self.search_bar_overlay.apply_filter_style()
                self.search_bar_overlay.update_results(self.search_bar_overlay.search_input.text())

        nav_layout, nav_buttons_dict, self.nav_buttons = NavMenu.create_menu(
            self.switch_page,
            on_search_change=on_search_change,
            on_filter_change=on_filter_change
        )
        debug_log("NavMenu.create_menu done")
        self.btn_keys = nav_buttons_dict["btn_keys"]
        self.btn_settings = nav_buttons_dict["btn_settings"]
        self.btn_home = nav_buttons_dict["btn_home"]
        if hasattr(self.btn_home, "sync_triggered"):
            self.btn_home.sync_triggered.connect(self.trigger_sync)
        self.menu_search = nav_buttons_dict["menu_search"]
        self.search_bar = self.menu_search.search_bar
        main_layout.addLayout(nav_layout)

        self._debug_mode = self.settings.get("console_visible", True)
        
        self.page_main = QWidget()
        page_main_layout = QVBoxLayout(self.page_main)
        page_main_layout.setContentsMargins(THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"], THEME_SPACING["margin_none"])
        page_main_layout.setSpacing(THEME_SPACING["spacing_element"])

        self.effect_list = QListWidget()
        self.effect_list.setObjectName("MainEffectList")
        self.last_selected_widget = None
        self.effect_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.effect_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        page_main_layout.addWidget(self.effect_list)

        self.page_keymaps = AddonsPage(self)
        debug_log("AddonsPage created")
        self.page_settings = SettingsPage(self)
        debug_log("SettingsPage created")

        # Create stacked_widget and add pages BEFORE adding to layout
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.page_main)
        self.stacked_widget.addWidget(self.page_keymaps)
        self.stacked_widget.addWidget(self.page_settings)
        main_layout.addWidget(self.stacked_widget)

        self.btn_toggle_console = QPushButton("Show/Hide Console")
        self.btn_toggle_console.setObjectName("ConsoleButton")
        self.btn_toggle_console.clicked.connect(self.toggle_console)
        self.btn_toggle_console.hide()
        main_layout.addWidget(self.btn_toggle_console)

        self._debug_mode = self.settings.get("console_visible", True)
        
        if self._debug_mode:
            self.log_console = QTextEdit()
            self.log_console.setObjectName("LogConsole")
            self.log_console.setReadOnly(True)
            self.log_console.setFixedHeight(THEME_SPACING["height_console"])
            main_layout.addWidget(self.log_console)
        else:
            self.log_console = None
        
        self._console_restart_label = QLabel()
        self._console_restart_label.setStyleSheet("color: #ff5555; background-color: #331111; padding: 5px;")
        self._console_restart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._console_restart_label.hide()
        main_layout.addWidget(self._console_restart_label)

        self.status_label = QLabel("Waiting for Premiere Pro...")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setProperty("connected", False)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("StatusLabel")
        main_layout.addWidget(self.status_label)

        debug_log("About to create ServerWorker...")
        self.worker = ServerWorker()
        debug_log("ServerWorker created")
        self.worker.log_signal.connect(self.append_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.effects_signal.connect(self.populate_effects)
        self.worker.tooltip_signal.connect(self.show_tooltip_error)
        self.worker.version_detected_signal.connect(self.on_version_detected)
        self.worker.bm_ready_signal.connect(self._on_bm_ready)
        
        if self._get_auto_connect():
            QTimer.singleShot(0, self.trigger_sync)
        
        set_server_worker(self.worker)

        self.temp_effects = []
        self.sync_timer = QTimer()
        self.sync_timer.setSingleShot(True)
        self.sync_timer.timeout.connect(self.finalize_sync)

        self.search_bar_overlay = None
        self.hotkey_signal = HotkeySignal()
        self.hotkey_signal.trigger_search_bar.connect(self._ensure_searchbar)
        self.hotkey_signal.trigger_transition_options.connect(self._show_transition_safe)
        self.hotkey_signal.log_signal.connect(self.append_log)
        self.hotkey_signal.trigger_better_motion.connect(self._start_better_motion)
        
        debug_log("About to create GlobalHotkeyManager...")
        self.hotkey_manager = GlobalHotkeyManager(
            trigger_callback=self.hotkey_signal.trigger_search_bar.emit,
            transition_callback=self.hotkey_signal.trigger_transition_options.emit,
            log_callback=self.hotkey_signal.log_signal.emit,
            bm_callback=self.hotkey_signal.trigger_better_motion.emit,
            last_used_getter=get_last_used,
            config_getter=load_searchbar_config
        )
        debug_log("GlobalHotkeyManager created")

        self.update_global_hotkey()
        self.load_presets()
        self.load_effects()
        self.refresh_ui(effects=True, presets=True)
        debug_log("__init__ completed!")

    def _ensure_searchbar(self):
        if self.search_bar_overlay is None:
            self.search_bar_overlay = FloatingSearchBar(self)
        self.search_bar_overlay.show_bar()

    def _show_transition_safe(self, match_name, effect_type):
        if self.search_bar_overlay is None:
            self.search_bar_overlay = FloatingSearchBar(self)
        self.search_bar_overlay.show_transition_options(match_name, effect_type)

    def _start_better_motion(self, prop_name):
        from Core.functions.better_motion import start_better_motion_adjust
        start_better_motion_adjust(prop_name)

    def _on_bm_ready(self, prop, value):
        from Core.functions.better_motion import handle_bm_ready
        handle_bm_ready(prop, value)

    def switch_page(self, index, active_btn):
        self.stacked_widget.setCurrentIndex(index)
        for btn in self.nav_buttons:
            if hasattr(btn, 'set_active'):
                btn.set_active(False)
            else:
                btn.setProperty("active", False)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        
        if active_btn is None:
            pass
        elif hasattr(active_btn, 'set_active'):
            active_btn.set_active(True)
        else:
            active_btn.setProperty("active", True)
            active_btn.style().unpolish(active_btn)
            active_btn.style().polish(active_btn)

    def load_settings(self):
        defaults = {
            "console_visible": True
        }
        
        if not os.path.exists(self.settings_path):
            return defaults
    
        try:
            with open(self.settings_path, "r") as f:
                data = json.load(f)
                
            needs_update = False
            for key, value in defaults.items():
                if key not in data:
                    data[key] = value
                    needs_update = True
            
            if needs_update:
                self.settings = data
                self.save_settings()
                
            return data
        except: 
            return defaults

    def save_settings(self):
        os.makedirs(get_data_path(), exist_ok=True)
        with open(self.settings_path, "w") as f: json.dump(self.settings, f)

    def _get_auto_connect(self):
        port_settings_path = get_data_path("port_settings.json")
        default = {"auto_connect": False}
        if os.path.exists(port_settings_path):
            try:
                with open(port_settings_path, "r") as f:
                    default.update(json.load(f))
            except:
                pass
        return default.get("auto_connect", False)

    def start_server(self):
        if not self.worker.isRunning():
            self.worker.start_server()

    def trigger_sync(self):
        self.append_log(" Starting server...", THEME_USER_COLORS["info"])
        
        if not self.worker.isRunning():
            self.worker.start_server()
        
        if not self.worker.wait_for_ready(timeout=5.0):
            if not self.worker.wait_for_ready(timeout=5.0):
                if self._get_auto_connect():
                    self.append_log(" Timeout - Retrying..", THEME_USER_COLORS["warning"])
                    QTimer.singleShot(5000, self.trigger_sync)
                else:
                    self.append_log(" Timeout - Try resync.", THEME_USER_COLORS["error"])
                return
        
        if self.worker._premiere_connected.is_set():
            self.append_log(" Already connected! Fetching directly...", THEME_USER_COLORS["info"])
            self.trigger_fetch_script()
        else:
            if not self.worker.wait_for_premiere_connection(timeout=5.0):
                if self._get_auto_connect():
                    self.append_log(" Timeout - Retrying..", THEME_USER_COLORS["warning"])
                    QTimer.singleShot(5000, self.trigger_sync)
                else:
                    self.append_log(" Timeout - Try resync.", THEME_USER_COLORS["error"])
                return
            
            self.append_log(" Connected! Requesting version...", THEME_USER_COLORS["success"])

    def on_version_detected(self, version, name):
        self.trigger_fetch_script()

    def update_global_hotkey(self):
        self.hotkey_manager.update_global_hotkey()

    def load_presets(self):
        if os.path.exists(self.presets_cache_path):
            try:
                with open(self.presets_cache_path, "r", encoding="utf-8") as f: self.all_presets = json.load(f)
            except: pass
    
    def load_effects(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f: 
                    self.all_effects = json.load(f)
                
                for effect in self.all_effects:
                    pass
                with open(self.cache_path, "w", encoding="utf-8") as f: 
                    json.dump(self.all_effects, f, indent=4)
            except: pass

    def reload_commands(self):
        """Rebuild the dynamic CMD command list and refresh the UI."""
        self.all_commands = get_dynamic_commands()
        self.refresh_ui(effects=True, presets=True)

    def apply_regex_rules(self):
        self.append_log(" RegEx rules updated. Refreshing...", THEME_USER_COLORS["info"])
        self.refresh_ui(effects=True, presets=True)
        self.switch_page(0, self.btn_keys)

    def trigger_fetch_script(self):
        import threading
        try:
            self.temp_effects = []
            
            self.splash_overlay = SplashOverlay(self, THEME_USER_COLORS)
            self.splash_overlay.set_title("Fetching Effects...")
            self.splash_overlay.show()
            self.setEnabled(False)
            
            self._effects_fetch_progress = [0, 0]
            self._effects_connection = None
            
            def on_effects_received(effects):
                if effects:
                    self._effects_fetch_progress[1] = len(effects)
            
            self._effects_connection = self.worker.effects_signal.connect(on_effects_received)
            
            thread = threading.Thread(target=fetch_effects, daemon=True)
            thread.start()
            
        except Exception as e:
            self.append_log(f" Synchronization error: {e}", THEME_USER_COLORS["error"])
            self._close_splash_overlay()

    def populate_effects(self, effects):
        self.temp_effects.extend(effects)
        self.sync_timer.start(500)

    def sync_presets(self):
        from Modules.apply_preset import PresetApplier
        from PyQt6.QtWidgets import QMessageBox
        import os

        self.settings = self.load_settings()
        
        config = PresetApplier.load_config()
        is_qa_enabled = config.get("quick_apply_enabled", False) if config else False
        has_capture = config and "mouse_x" in config and "mouse_y" in config

        if not is_qa_enabled or not has_capture:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Quick Apply Required")
            msg_box.setText("<b>Quick Apply must be configured to use and apply Presets.</b>")
            msg_box.setInformativeText(
                "To apply Presets, you need to enable and configure Quick Apply:\n\n"
                "1. Go to Settings page\n"
                "2. Click 'Configure' next to Quick Apply\n"
                "3. Complete the mouse position capture\n"
                "4. Enable Quick Apply toggle\n\n"
                "Would you like to open Settings now?"
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            result = msg_box.exec()
            if result == QMessageBox.StandardButton.Yes:
                self.switch_page(1, self.btn_settings)
            return

        self.append_log(" Scanning for Premiere Presets...", THEME_USER_COLORS["info"])
        
        config = PresetApplier.load_config()
        target_version = config.get("selected_version") if config else None

        if not target_version:
            docs_path = os.path.expanduser(r"~\Documents\Adobe\Premiere Pro")
            if not os.path.exists(docs_path):
                self.append_log(" Adobe folder not found in Documents.", THEME_USER_COLORS["error"])
                return

            versions = [f for f in os.listdir(docs_path) 
                        if os.path.isdir(os.path.join(docs_path, f)) and f[0].isdigit()]
            
            if not versions:
                self.append_log(" No valid Premiere version found.", THEME_USER_COLORS["error"])
                return
            
            versions.sort(key=lambda x: os.path.getmtime(os.path.join(docs_path, x)), reverse=True)
            target_version = versions[0]
            
            default_data = config if config else {}
            default_data["selected_version"] = target_version
            PresetApplier.save_config(default_data)

        self.splash_overlay = SplashOverlay(self, THEME_USER_COLORS)
        self.splash_overlay.set_title("Fetching Presets...")
        self.splash_overlay.show()
        self.setEnabled(False)
        self._presets_total = 0
        
        def run_fetch():
            try:
                fetch_presets(target_version)
                QTimer.singleShot(0, self.finish_fetch)
            except Exception as e:
                QTimer.singleShot(0, lambda: self.append_log(f" Preset Fetch Error: {e}", THEME_USER_COLORS["error"]))
                QTimer.singleShot(0, self._close_splash_overlay)
        
        self.fetch_thread = threading.Thread(target=run_fetch, daemon=True)
        self.fetch_thread.start()

    def finish_fetch(self):
        try:
            self.load_presets()
            self.refresh_ui(effects=True, presets=True)
            self.append_log(f" Presets synced!", THEME_USER_COLORS["success"])
        except Exception as e:
            self.append_log(f" Preset Load Error: {e}", THEME_USER_COLORS["error"])
        self._close_splash_overlay()

    def cancel_fetch(self):
        self.fetch_cancelled = True
        if self.load_dialog:
            self.load_dialog.close()
            self.load_dialog = None
        self.append_log(" Preset sync cancelled.", THEME_USER_COLORS["warning"])

    def finalize_sync(self):
        processed_effects = []
        for effect in self.temp_effects:
            processed_effects.append(effect)
        
        self.all_effects = processed_effects
        self.temp_effects = []
        
        os.makedirs(get_data_path(), exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f: json.dump(self.all_effects, f, indent=4)
        
        self.refresh_ui(effects=True, presets=True)
        self.append_log(f" Database saved with {len(self.all_effects)} effects.", THEME_USER_COLORS["success"])
        self._close_splash_overlay()
        
        config = load_quick_apply_config()
        is_qa_enabled = config.get("quick_apply_enabled", False) if config else False
        has_capture = config and "mouse_x" in config and "mouse_y" in config
        
        if is_qa_enabled and has_capture:
            self.append_log(" QuickApply configured. Auto-fetching presets...", THEME_USER_COLORS["info"])
            self.sync_presets()

    def _close_splash_overlay(self):
        if self.splash_overlay:
            self.splash_overlay.close()
            self.splash_overlay = None
        if self._effects_connection:
            try:
                self.worker.effects_signal.disconnect(self._effects_connection)
            except:
                pass
            self._effects_connection = None
        self.setEnabled(True)

    def refresh_ui(self, effects=False, presets=False):
        self.last_selected_widget = None
        self.effect_list.clear()

        pi_config = load_priority_ignore_config()
        ignore_set = set(pi_config.get("ignore", []))

        items_to_build = []
        if effects:
            items_to_build.extend(self.all_effects)
        if presets:
            items_to_build.extend(self.all_presets)
        items_to_build.extend(self.all_commands)

        for item_data in items_to_build:
            d_name = item_data.get("displayName", "")
            m_name = item_data.get("matchName", "")
            e_type = item_data.get("type", "Unknown")

            if m_name in ignore_set:
                continue

            clean_d_name = self.cleaner.clean_name(d_name, e_type)

            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem()
            widget = EffectItemWidget(clean_d_name, m_name, e_type, self, self.effect_list)
            item.setSizeHint(QSize(0, 45))
            item.setData(Qt.ItemDataRole.UserRole, {"clean_name": clean_d_name.lower(), "match_name": m_name.lower(), "type": e_type})
            self.effect_list.addItem(item)
            self.effect_list.setItemWidget(item, widget)

        self.execute_filter()

    def cycle_filter(self, direction):
        self.current_filter_idx = cycle_filter(self.current_filter_idx, direction)
        self.menu_search.current_filter_idx = self.current_filter_idx
        self.menu_search._apply_filter_style()
        if self.search_bar_overlay and self.search_bar_overlay.mode == "search":
            self.search_bar_overlay.apply_filter_style()
            self.search_bar_overlay.update_results(self.search_bar_overlay.search_input.text())

    def execute_filter(self):
        raw_query = self.search_bar.text().lower().strip()

        # Parse command prefix (/V, /A, /T, /P…)
        type_override, query_text = parse_search_command(raw_query, self._commands_config)
        query_words = query_text.split() if query_text else []

        if type_override in ("FX.V", "FX.A", "TR.V", "PRST", "CMD"):
            current_mode = type_override
        elif type_override in ("CMD.QA", "CMD.BM", "CMD.PR"):
            current_mode = "CMD"
            if not query_text:
                if type_override == "CMD.QA":   query_text = "quick apply";   query_words = ["quick", "apply"]
                elif type_override == "CMD.BM": query_text = "better motion"; query_words = ["better", "motion"]
        else:
            current_mode = self.filter_modes[self.current_filter_idx]["type"]

        # Sync the mode indicator when a prefix is active
        if type_override is not None:
            for i, m in enumerate(self.filter_modes):
                if m["type"] == current_mode:
                    if self.current_filter_idx != i:
                        self.current_filter_idx = i
                        self.menu_search.current_filter_idx = i
                        self.menu_search._apply_filter_style()
                    break

        for i in range(self.effect_list.count()):
            item = self.effect_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            e_type = data.get("type", "")

            if current_mode == "CMD":
                # CMD mode: show only CMD items
                if not is_command(e_type):
                    item.setHidden(True)
                    continue
                target_text = f"{data['clean_name']} {data['match_name']}"
                matches_text = not query_words or all(w in target_text for w in query_words)
                item.setHidden(not matches_text)
                continue

            # Specific type modes (FX.V, FX.A, TR.V, PRST): hide CMD items
            # All mode: CMD items are visible
            if is_command(e_type) and current_mode != "All":
                item.setHidden(True)
                continue

            matches_type = True
            if current_mode != "All":
                if is_video(e_type) and current_mode == "FX.V": pass
                elif is_audio(e_type) and current_mode == "FX.A": pass
                elif is_transition(e_type) and current_mode == "TR.V": pass
                elif is_preset(e_type) and current_mode == "PRST": pass
                else: matches_type = False

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

    def append_log(self, message, color=THEME_USER_COLORS["text_white"]):
        if self.log_console:
            self.log_console.append(f'<span style="color:{color};">{message}</span>')
            self.log_console.verticalScrollBar().setValue(self.log_console.verticalScrollBar().maximum())

    def toggle_console(self):
        if self._debug_mode:
            self._console_restart_label.setText("Console Désactivée - Redémarrez pour la désactiver")
            self.settings["console_visible"] = False
        else:
            self._console_restart_label.setText("Console Désactivée - Redémarrez pour l'activer")
            self.settings["console_visible"] = True
        self._console_restart_label.show()
        self.save_settings()

    def update_status(self, is_connected):
        self.status_label.setText("Premiere Pro Connected" if is_connected else "Waiting for Premiere Pro...")
        self.status_label.setProperty("connected", is_connected)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def show_tooltip_error(self, message):
        QToolTip.showText(QCursor.pos(), f" {message}", self, QRect(), 3000)

    def register_child_window(self, window):
        """Enregistre une fenêtre enfant pour qu'elle soit fermée avec la fenêtre principale"""
        if window not in self.child_windows:
            self.child_windows.append(window)

    def closeEvent(self, event):
        """Ferme toutes les fenêtres enfants avant de fermer la fenêtre principale"""
        # Supprimer le fichier de lock
        lock_path = os.path.join(get_data_path(), "premiere_companion.lock")
        try:
            if os.path.exists(lock_path):
                os.remove(lock_path)
        except:
            pass
        
        # Fermer les fenêtres enfants
        for window in self.child_windows:
            if window and window.isVisible():
                window.close()
        super().closeEvent(event)
